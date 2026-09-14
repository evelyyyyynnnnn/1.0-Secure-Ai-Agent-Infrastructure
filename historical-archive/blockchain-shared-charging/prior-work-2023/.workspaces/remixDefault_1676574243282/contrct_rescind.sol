pragma solidity ^0.8.0;

contract Authorization {
    
    mapping(address => mapping(address => bool)) private authorized;
    
    event RevokeAuthorization(address indexed vehicleAddress, address indexed thirdParty);
    
    function authorize(address _vehicleAddress, address _thirdParty) public {
        authorized[_vehicleAddress][_thirdParty] = true;
    }
    
    function revokeAuthorization(address _thirdParty) public {
        authorized[msg.sender][_thirdParty] = false;
        emit RevokeAuthorization(msg.sender, _thirdParty);
    }
    
    function isAuthorized(address _vehicleAddress, address _thirdParty) public view returns (bool) {
        return authorized[_vehicleAddress][_thirdParty];
    }
}
