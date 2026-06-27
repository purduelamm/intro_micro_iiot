from pymodbus.client import ModbusTcpClient
from pymodbus.client.mixin import ModbusClientMixin
import datetime

host = "127.0.0.1"  # Emulator IP
port = 502
device_id = 1

client = ModbusTcpClient(host=host, port=port)

try:
    if not client.connect():
        raise RuntimeError(f"Connect failed: {host}:{port}")

    now = datetime.datetime.now()

    freq_read = client.read_holding_registers(
        address=1536,
        count=2,
        device_id=device_id
    )

    if freq_read.isError():
        raise RuntimeError(f"Modbus read error: {freq_read}")

    freq_reg = freq_read.registers

    freq_value = client.convert_from_registers(
        registers=freq_reg,
        data_type=ModbusClientMixin.DATATYPE.FLOAT32,
        word_order="big"
    )

    print(f"{now}: Frequency is {freq_value} Hz")

finally:
    client.close()