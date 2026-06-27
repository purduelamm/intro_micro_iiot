from pymodbus.client import ModbusTcpClient
from pymodbus.client.mixin import ModbusClientMixin
import datetime

host = "127.0.0.1"
port = 502
device_id = 1

client = ModbusTcpClient(host=host, port=port)

parameters = {
    "Frequency": {
        "address": 1536,
        "unit": "Hz",
    },
    "Phase 1 Voltage": {
        "address": 1538,
        "unit": "V",
    },
    "Total Phase A Current": {
        "address": 1550,
        "unit": "A",
    },
    "Total System Power": {
        "address": 1564,
        "unit": "W",
    },
    "Total Reactive Power": {
        "address": 1572,
        "unit": "var",
    },
    "Total Apparent Power": {
        "address": 1574,
        "unit": "VA",
    },
    "Total Power Factor": {
        "address": 1582,
        "unit": "",
    },
}


def read_float32(client, address, device_id=1):
    result = client.read_holding_registers(
        address=address,
        count=2,
        device_id=device_id
    )

    if result.isError():
        raise RuntimeError(f"Modbus read error at address {address}: {result}")

    value = client.convert_from_registers(
        registers=result.registers,
        data_type=ModbusClientMixin.DATATYPE.FLOAT32,
        word_order="big"
    )

    return value


try:
    if not client.connect():
        raise RuntimeError(f"Connect failed: {host}:{port}")

    now = datetime.datetime.now()
    print(f"\n[{now}] Modbus Data")
    print("-" * 50)

    for name, info in parameters.items():
        address = info["address"]
        unit = info["unit"]

        value = read_float32(
            client=client,
            address=address,
            device_id=device_id
        )

        if unit:
            print(f"{name}: {value} {unit}")
        else:
            print(f"{name}: {value}")

finally:
    client.close()