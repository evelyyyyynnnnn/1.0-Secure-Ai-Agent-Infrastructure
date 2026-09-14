pragma solidity ^0.8.0;

contract ChargingRecords {
    
    struct ChargingRecord {
        address vehicleAddress;
        uint startTime;
        uint endTime;
        uint energy;
    }
    
    mapping(address => ChargingRecord[]) private chargingRecords;
    
    function addChargingRecord(address _vehicleAddress, uint _startTime, uint _endTime, uint _energy) public {
        chargingRecords[_vehicleAddress].push(ChargingRecord(_vehicleAddress, _startTime, _endTime, _energy));
    }
    
    function getChargingRecordCount(address _vehicleAddress) public view returns (uint) {
        return chargingRecords[_vehicleAddress].length;
    }
    
    function getChargingRecord(address _vehicleAddress, uint _index) public view returns (address, uint, uint, uint) {
        ChargingRecord memory record = chargingRecords[_vehicleAddress][_index];
        return (record.vehicleAddress, record.startTime, record.endTime, record.energy);
    }
}
