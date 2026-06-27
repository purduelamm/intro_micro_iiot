#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MTConnet adapter sample for ME597 Lab5
# This code is for power meter

import sys
import time
import datetime
from data_item import Event, Sample
from mtconnect_adapter import Adapter

from pymodbus.client import ModbusTcpClient
from pymodbus.client.mixin import ModbusClientMixin


# function for power meter
def readReg(client, address, length=2, unit=1):
    rr = client.read_holding_registers(
        address=address,
        count=length,
        device_id=unit
    )

    if rr is None or rr.isError():
        raise RuntimeError(f"Modbus read failed at address {address}: {rr}")

    return client.convert_from_registers(
        registers=rr.registers,
        data_type=ModbusClientMixin.DATATYPE.FLOAT32,
        word_order="big"
    )


class MTConnectAdapter(object):

    def __init__(self, host, port):  # init of MTconnectAdapter class
        # MTConnect adapter connection info
        self.host = host
        self.port = port
        self.adapter = Adapter((host, port))

        # For samples
        self.p1 = Sample('p1')  # power (W)
        self.adapter.add_data_item(self.p1)

        # For events
        self.ps = Event('ps')  # power state
        self.adapter.add_data_item(self.ps)

        # MTConnnect adapter availability
        self.avail = Event('avail')
        self.adapter.add_data_item(self.avail)

        # Power meter Modbus TCP info
        self.pm_ip = "127.0.0.1"
        self.pm_port = 502
        self.pm_unit = 1

        self.power_reg_addr = 0 # Address??
        self.power_reg_len = 2

        # Threshold for ON/OFF
        self.on_threshold_w = 5.0

        # Start MTConnect
        self.adapter.start()
        self.adapter.begin_gather()
        self.avail.set_value("AVAILABLE")
        self.adapter.complete_gather()

        self.adapter_stream()

    def adapter_stream(self):
        while True:
            try:
                c = ModbusTcpClient(
                    host=self.pm_ip,
                    port=self.pm_port,
                    timeout=2
                )

                if not c.connect():
                    c.close()
                    raise RuntimeError(f"Failed to connect ModbusTcpClient to {self.pm_ip}:{self.pm_port}")

                # Read power (W)
#               p1 = ???

                # Determine power state
#               ps = ???

                now = datetime.datetime.now()

                self.adapter.begin_gather()
                self.p1.set_value(f"{p1:.3f}")
                self.ps.set_value(ps)
                self.adapter.complete_gather()

                print("{} MTConnect data collection completed ... ".format(now))
                print("Power meter: Machine is now {}, {:.3f} W\n".format(ps, p1))

                c.close()
                time.sleep(0.5)

            except KeyboardInterrupt:
                print("Stopping MTConnect...")
                self.adapter.stop()
                sys.exit()

            except Exception as e:
                print("Error:", e)
                try:
                    c.close()
                except Exception:
                    pass
                time.sleep(1)

## ====================== MAIN ======================
if __name__ == "__main__":
    MTConnectAdapter('127.0.0.1', 7878)