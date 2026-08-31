pragma solidity ^0.8.0;

contract Authorization {
    
    mapping(address => mapping(address => bool)) private authorized;
    
    event UpdateAuthorization(address indexed vehicleAddress, address indexed thirdParty, bool authorized);
    
    function authorize(address _vehicleAddress, address _thirdParty, bool _authorized) public {
        authorized[_vehicleAddress][_thirdParty] = _authorized;
        emit UpdateAuthorization(_vehicleAddress, _thirdParty, _authorized);
    }
    
    function isAuthorized(address _vehicleAddress, address _thirdParty) public view returns (bool) {
        return authorized[_vehicleAddress][_thirdParty];
    }
}
