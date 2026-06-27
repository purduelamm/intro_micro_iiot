import requests
import json
import datetime


# define the IO-Link master IP
URL = "http://127.0.0.1/" 

# define JSON body for POST method
# note that the sensor is connected to port 1
BODY = {
    "code": "request",
    "cid": -1,
    "adr": "/iolinkmaster/port[1]/iolinkdevice/iolreadacyclic",
    "data": {
        "index": 40,
        "subindex": 0
    }
}


def hex_to_int16(hex_string: str) -> int:
    """
    Convert 4-character hex string to signed 16-bit integer.
    Example:
        '0002' -> 2
        'FFFE' -> -2
    """
    value = int(hex_string, 16)

    if value >= 0x8000:
        value -= 0x10000

    return value


def parse_sensor_value(value: str) -> dict:
    """
    Parse raw IO-Link sensor value.

    Raw value example:
        0000FC000002FF000000FF0000F6FF000026FF03

    Indexing:
        v_Rms       = value[0:4]
        a_Peak      = value[8:12]
        a_Rms       = value[16:20]
        Temperature = value[24:28]
        Crest       = value[32:36]
    """

    # Raw 16-bit integer values
    v_rms_raw = hex_to_int16(value[0:4])
    a_peak_raw = hex_to_int16(value[8:12])
    a_rms_raw = hex_to_int16(value[16:20])
    temperature_raw = hex_to_int16(value[24:28])
    crest_raw = hex_to_int16(value[32:36])

    # Unit conversion
    # Adjust scale factors if the sensor manual defines different scaling.
    v_rms = round(v_rms_raw * 0.0001, 4)          # m/s
    a_peak = round(a_peak_raw * 0.1, 4)        # m/s^2, 
    a_rms = round(a_rms_raw * 0.1, 4)          # m/s^2, 
    temperature = round(temperature_raw * 0.1, 1) # deg C, 
    crest = round(crest_raw * 0.1, 1)             

    return {
        "v_Rms": {
            "raw": v_rms_raw,
            "value": v_rms,
            "unit": "m/s"
        },
        "a_Peak": {
            "raw": a_peak_raw,
            "value": a_peak,
            "unit": "m/s^2"
        },
        "a_Rms": {
            "raw": a_rms_raw,
            "value": a_rms,
            "unit": "m/s^2"
        },
        "Temperature": {
            "raw": temperature_raw,
            "value": temperature,
            "unit": "deg C"
        },
        "Crest": {
            "raw": crest_raw,
            "value": crest,
            "unit": ""
        }
    }


def main():
    now = datetime.datetime.now()

    try:
        # Request data from the IO-Link master
        req = requests.post(
            url=URL,
            json=BODY,
            timeout=5
        )

        req.raise_for_status()

        data_json = req.json()

        # Pretty print JSON response
        data_json_formatted = json.dumps(data_json, indent=2)

        print(now, ": Data structure from the IO-Link master")
        print(data_json_formatted)
        print()

        # Parse JSON
        value = data_json["data"]["value"]

        print("raw measured value is", value)
        print("length of raw measured value is", len(value))
        print()

        parsed_data = parse_sensor_value(value)

        print("Parsed sensor data")
        print("-" * 40)

        for name, data in parsed_data.items():
            if data["unit"]:
                print(
                    f"{name}: {data['value']} {data['unit']} "
                    f"(raw: {data['raw']})"
                )
            else:
                print(
                    f"{name}: {data['value']} "
                    f"(raw: {data['raw']})"
                )

    except requests.exceptions.ConnectionError:
        print("Connection error: Could not connect to the IO-Link master.")
        print("Check the IP address, network connection, and power of the device.")

    except requests.exceptions.Timeout:
        print("Timeout error: The IO-Link master did not respond in time.")

    except requests.exceptions.HTTPError as error:
        print("HTTP error:", error)

    except KeyError as error:
        print("JSON parsing error: Missing key", error)
        print("Check the response structure from the IO-Link master.")

    except Exception as error:
        print("Unexpected error:", error)


if __name__ == "__main__":
    main()