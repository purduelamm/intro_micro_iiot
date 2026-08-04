import asyncio
import logging
import random
import struct

from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice


HOST = "127.0.0.1"
PORT = 502
DEVICE_ID = 1
UPDATE_INTERVAL = 1.0  # seconds


PARAMETERS = {
    "Frequency": {
        "address": 1536,
        "unit": "Hz",
        "center": 60.0,
        "variation": 0.05,
    },
    "Phase 1 Voltage": {
        "address": 1538,
        "unit": "V",
        "center": 120.0,
        "variation": 1.0,
    },
    "Total Phase A Current": {
        "address": 1550,
        "unit": "A",
        "center": 0.08,
        "variation": 0.02,
    },
    "Total System Power": {
        "address": 1564,
        "unit": "W",
        "center": 2.8,
        "variation": 0.5,
    },
    "Total Reactive Power": {
        "address": 1572,
        "unit": "var",
        "center": -5.9,
        "variation": 0.8,
    },
    "Total Apparent Power": {
        "address": 1574,
        "unit": "VA",
        "center": 9.7,
        "variation": 0.7,
    },
    "Total Power Factor": {
        "address": 1582,
        "unit": "",
        "center": 0.29,
        "variation": 0.03,
    },
}


def float_to_registers(value: float) -> list[int]:
    """
    Convert float32 value to two 16-bit Modbus registers.

    Byte order: Big endian
    Word order: Big endian
    """
    packed = struct.pack(">f", float(value))
    return list(struct.unpack(">HH", packed))


def generate_value(center: float, variation: float) -> float:
    """
    Generate a random value within center ± variation.
    """
    return random.uniform(
        center - variation,
        center + variation,
    )


class PowerMeterEmulator:
    def __init__(self):
        min_address = min(info["address"] for info in PARAMETERS.values())
        max_address = max(info["address"] for info in PARAMETERS.values()) + 1

        register_count = max_address - min_address + 1

        device = SimDevice(
            DEVICE_ID,
            SimData(
                min_address,
                values=[0] * register_count,
                datatype=DataType.REGISTERS,
            ),
        )

        self.server = ModbusTcpServer(
            device,
            address=(HOST, PORT),
        )

    async def set_float32(self, address: int, value: float) -> None:
        registers = float_to_registers(value)

        await self.server.async_setValues(
            DEVICE_ID,
            3,  # Function code 3: Holding Registers
            address,
            registers,
        )

    async def update_registers(self) -> None:
        print("[REGISTER UPDATE]")

        for name, info in PARAMETERS.items():
            address = info["address"]
            unit = info["unit"]

            value = generate_value(
                center=info["center"],
                variation=info["variation"],
            )

            await self.set_float32(address, value)

            if unit:
                print(f"  {name}: {value:.6f} {unit}")
            else:
                print(f"  {name}: {value:.6f}")

        print()

    async def update_loop(self) -> None:
        while True:
            await self.update_registers()
            await asyncio.sleep(UPDATE_INTERVAL)

    async def run(self) -> None:
        print()
        print("==============================================")
        print(" Modbus TCP Power Meter Emulator")
        print("==============================================")
        print(f" Server          : {HOST}:{PORT}")
        print(f" Device ID       : {DEVICE_ID}")
        print(" Data type       : IEEE-754 32-bit float")
        print(" Byte order      : Big Endian")
        print(" Word order      : Big Endian")
        print(f" Update interval : {UPDATE_INTERVAL} s")
        print(" Stop            : Ctrl+C")
        print("==============================================")
        print()

        update_task = asyncio.create_task(self.update_loop())

        try:
            await self.server.serve_forever()
        finally:
            update_task.cancel()

            try:
                await update_task
            except asyncio.CancelledError:
                pass


async def async_main() -> None:
    emulator = PowerMeterEmulator()
    await emulator.run()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    try:
        asyncio.run(async_main())

    except KeyboardInterrupt:
        print("\nModbus emulator stopped.")

    except PermissionError as exc:
        raise RuntimeError(
            "Permission denied while opening port 502. "
            "On Windows, run PowerShell as Administrator. "
            "On Linux, port 502 may require sudo."
        ) from exc

    except OSError as exc:
        raise RuntimeError(
            "Could not start the Modbus server. "
            "Port 502 may already be in use."
        ) from exc


if __name__ == "__main__":
    main()