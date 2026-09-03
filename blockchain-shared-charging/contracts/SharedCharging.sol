// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Shared charging session settlement
/// @notice Escrows a driver's deposit for the duration of a charging session and
///         settles against a metered energy reading signed by the charge point.
/// @dev The design constraint that shapes this contract: a charge point is not
///      trusted. It reports the meter reading, so the contract must make an
///      inflated reading either impossible or contestable. Deposits bound the
///      loss, a dispute window makes over-reporting contestable, and settlement
///      follows checks-effects-interactions so a malicious driver contract
///      cannot re-enter during the refund.
contract SharedCharging {
    enum State { None, Open, Reported, Settled, Disputed, Refunded }

    struct Session {
        address driver;
        address point;
        uint96  deposit;        // wei escrowed at open
        uint64  openedAt;
        uint64  reportedAt;
        uint32  wattHours;      // meter reading, reported by the point
        uint96  tariffPerKWh;   // wei per kWh, fixed at open
        State   state;
    }

    uint64 public constant DISPUTE_WINDOW = 1 hours;

    address public immutable arbiter;
    mapping(bytes32 => Session) public sessions;
    mapping(address => bool) public registeredPoints;

    event Opened(bytes32 indexed id, address indexed driver, address indexed point, uint96 deposit);
    event Reported(bytes32 indexed id, uint32 wattHours);
    event Settled(bytes32 indexed id, uint96 paid, uint96 refunded);
    event Disputed(bytes32 indexed id, address by);
    event Resolved(bytes32 indexed id, uint32 wattHours);

    error NotDriver();
    error NotPoint();
    error NotArbiter();
    error BadState();
    error WindowOpen();
    error WindowClosed();
    error PointNotRegistered();
    error DepositTooSmall();

    modifier onlyArbiter() {
        if (msg.sender != arbiter) revert NotArbiter();
        _;
    }

    constructor(address _arbiter) {
        arbiter = _arbiter;
    }

    function registerPoint(address point) external onlyArbiter {
        registeredPoints[point] = true;
    }

    /// @notice Driver opens a session, escrowing enough to cover the maximum draw.
    function open(bytes32 id, address point, uint96 tariffPerKWh, uint32 maxWattHours)
        external
        payable
    {
        if (!registeredPoints[point]) revert PointNotRegistered();
        if (sessions[id].state != State.None) revert BadState();
        uint256 needed = (uint256(tariffPerKWh) * maxWattHours) / 1000;
        if (msg.value < needed) revert DepositTooSmall();

        sessions[id] = Session({
            driver: msg.sender,
            point: point,
            deposit: uint96(msg.value),
            openedAt: uint64(block.timestamp),
            reportedAt: 0,
            wattHours: 0,
            tariffPerKWh: tariffPerKWh,
            state: State.Open
        });
        emit Opened(id, msg.sender, point, uint96(msg.value));
    }

    /// @notice The charge point reports the metered energy delivered.
    function report(bytes32 id, uint32 wattHours) external {
        Session storage s = sessions[id];
        if (s.state != State.Open) revert BadState();
        if (msg.sender != s.point) revert NotPoint();
        s.wattHours = wattHours;
        s.reportedAt = uint64(block.timestamp);
        s.state = State.Reported;
        emit Reported(id, wattHours);
    }

    /// @notice Driver contests the reading. Only inside the dispute window.
    function dispute(bytes32 id) external {
        Session storage s = sessions[id];
        if (s.state != State.Reported) revert BadState();
        if (msg.sender != s.driver) revert NotDriver();
        if (block.timestamp > s.reportedAt + DISPUTE_WINDOW) revert WindowClosed();
        s.state = State.Disputed;
        emit Disputed(id, msg.sender);
    }

    /// @notice Arbiter fixes the reading on a disputed session.
    function resolve(bytes32 id, uint32 wattHours) external onlyArbiter {
        Session storage s = sessions[id];
        if (s.state != State.Disputed) revert BadState();
        s.wattHours = wattHours;
        s.state = State.Reported;
        s.reportedAt = uint64(block.timestamp);
        emit Resolved(id, wattHours);
    }

    /// @notice Settle after the dispute window closes: pay the point, refund the rest.
    /// @dev State is written before either transfer. Both parties may be contracts,
    ///      so the ordering here is what stops a re-entrant refund from draining
    ///      another session's escrow.
    function settle(bytes32 id) external {
        Session storage s = sessions[id];
        if (s.state != State.Reported) revert BadState();
        if (block.timestamp <= s.reportedAt + DISPUTE_WINDOW) revert WindowOpen();

        uint96 owed = uint96((uint256(s.tariffPerKWh) * s.wattHours) / 1000);
        if (owed > s.deposit) owed = s.deposit;
        uint96 refund = s.deposit - owed;

        address point = s.point;
        address driver = s.driver;
        s.state = State.Settled;
        s.deposit = 0;

        if (owed > 0) {
            (bool okP, ) = point.call{value: owed}("");
            require(okP, "point transfer failed");
        }
        if (refund > 0) {
            (bool okD, ) = driver.call{value: refund}("");
            require(okD, "driver refund failed");
        }
        emit Settled(id, owed, refund);
    }
}
