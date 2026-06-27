import json
import random
from http.server import BaseHTTPRequestHandler, HTTPServer


HOST = "127.0.0.1"
PORT = 80


SENSOR_VALUES = {
    "v_Rms": {
        "center": 0.0020,      # m/s
        "variation": 0.0005,
        "scale": 0.0001,
    },
    "a_Peak": {
        "center": 0.8,         # m/s^2
        "variation": 0.2,
        "scale": 0.1,
    },
    "a_Rms": {
        "center": 0.3,         # m/s^2
        "variation": 0.1,
        "scale": 0.1,
    },
    "Temperature": {
        "center": 25.0,        # deg C
        "variation": 1.0,
        "scale": 0.1,
    },
    "Crest": {
        "center": 3.0,
        "variation": 0.5,
        "scale": 0.1,
    },
}


def int16_to_hex(value: int) -> str:
    """
    Convert signed 16-bit integer to 4-character hex string.
    """
    if value < 0:
        value = (1 << 16) + value

    return f"{value & 0xFFFF:04X}"


def generate_raw_value(center: float, variation: float, scale: float) -> int:
    """
    Generate engineering value around center ± variation,
    then convert it to raw integer using the scale factor.
    """
    engineering_value = random.uniform(
        center - variation,
        center + variation,
    )

    raw_value = round(engineering_value / scale)

    return raw_value


def generate_sensor_hex_string() -> str:
    """
    Generate 40-character raw IO-Link value.

    Indexing used by the client:
        v_Rms       = value[0:4]
        a_Peak      = value[8:12]
        a_Rms       = value[16:20]
        Temperature = value[24:28]
        Crest       = value[32:36]

    Therefore, this string consists of 10 words,
    and the measured values are placed at word 0, 2, 4, 6, and 8.
    """

    words = ["0000"] * 10

    v_rms_raw = generate_raw_value(**SENSOR_VALUES["v_Rms"])
    a_peak_raw = generate_raw_value(**SENSOR_VALUES["a_Peak"])
    a_rms_raw = generate_raw_value(**SENSOR_VALUES["a_Rms"])
    temperature_raw = generate_raw_value(**SENSOR_VALUES["Temperature"])
    crest_raw = generate_raw_value(**SENSOR_VALUES["Crest"])

    words[0] = int16_to_hex(v_rms_raw)
    words[2] = int16_to_hex(a_peak_raw)
    words[4] = int16_to_hex(a_rms_raw)
    words[6] = int16_to_hex(temperature_raw)
    words[8] = int16_to_hex(crest_raw)

    return "".join(words)


class IOLinkEmulatorHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        request_body = self.rfile.read(content_length)

        try:
            request_json = json.loads(request_body.decode("utf-8"))
        except json.JSONDecodeError:
            request_json = {}

        raw_value = generate_sensor_hex_string()

        response = {
            "code": "response",
            "cid": request_json.get("cid", -1),
            "adr": request_json.get(
                "adr",
                "/iolinkmaster/port[1]/iolinkdevice/iolreadacyclic",
            ),
            "data": {
                "value": raw_value
            }
        }

        response_bytes = json.dumps(response, indent=2).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

        print("[REQUEST]")
        print(json.dumps(request_json, indent=2))
        print("[RESPONSE]")
        print(json.dumps(response, indent=2))
        print()

    def log_message(self, format, *args):
        return


def main():
    server = HTTPServer((HOST, PORT), IOLinkEmulatorHandler)

    print()
    print("==============================================")
    print(" IO-Link Master REST API Emulator")
    print("==============================================")
    print(f" Server : http://{HOST}:{PORT}")
    print(" Method : POST")
    print(" Stop   : Ctrl+C")
    print("==============================================")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nIO-Link emulator stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()