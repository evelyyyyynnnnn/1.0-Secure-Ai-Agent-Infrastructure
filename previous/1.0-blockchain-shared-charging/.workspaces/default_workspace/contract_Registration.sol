pragma solidity ^0.8.0;

contract V2G {
    struct Vehicle {
        string VIN;
        string publicKey;
    }

    mapping(string => Vehicle) public vehicles;

    function register(string memory _VIN, string memory _publicKey) public {
        // 检查 VIN 码是否已被注册
        require(bytes(vehicles[_VIN].VIN).length == 0, "Vehicle already registered");

        // 创建一个新的车辆结构体，并添加到映射中
        Vehicle memory newVehicle = Vehicle(_VIN, _publicKey);
        vehicles[_VIN] = newVehicle;
    }
}

