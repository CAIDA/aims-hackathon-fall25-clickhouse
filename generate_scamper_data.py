#!/usr/bin/env python3

"""
Simple scamper ping/trace measurement with data saving
Usage: ./generate_scamper_data.py MUX METHOD TARGET_IP
Example: ./generate_scamper_data.py /run/ark/mux ping 192.172.226.122
Example: ./generate_scamper_data.py /run/ark/mux trace 192.172.226.122
"""

import argparse
from datetime import datetime, timedelta
from scamper import ScamperCtrl, ScamperFile, ScamperPing, ScamperTrace


def probe(method, mux, target):
    # Create output file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_ip = target.replace(":", "_")  # Replace colons for valid filename
    output_file = f"{method}_{target_ip}_{timestamp}.warts"

    print(f"Starting {method} measurement to {target}")
    print(f"Saving data to: {output_file}")

    # Open warts file for writing
    outfile = ScamperFile(output_file, "w")

    # Connect to scamper daemon and attach output file
    with ScamperCtrl(mux=mux, outfile=outfile) as ctrl:
        ctrl.add_vps(ctrl.vps())
        for inst in ctrl.instances():
            if method == "ping":
                ctrl.do_ping(target, inst=inst)
            elif method == "trace":
                ctrl.do_trace(target, inst=inst)

            # Wait for response
            for o in ctrl.responses(timeout=timedelta(seconds=10)):
                if isinstance(o, ScamperPing):
                    if o.min_rtt:
                        rtt_ms = o.min_rtt.total_seconds() * 1000
                        print(f"{inst.ipv4} ({inst.name}) -> {target}: {rtt_ms:.1f} ms")
                    else:
                        print(f"No response from {inst.name} ({inst.ipv4}) to {target}")
                elif isinstance(o, ScamperTrace):
                    print(f"Trace data received from {inst.name} ({inst.ipv4}) to {target}")
                break
            else:
                print(f"Timeout: No response from {inst.name} ({inst.ipv4}) to {target}")

    print(f"✓ Data saved to: {output_file}")
    print("Measurement complete!")
    print(f"Use './warts2clickhouse.py {output_file}' to import data")


def main():
    parser = argparse.ArgumentParser(
        description="Simple scamper ping/trace measurement with data saving"
    )
    parser.add_argument("mux", help="Path to scamper mux socket")
    parser.add_argument("method", choices=["ping", "trace"], help="Measurement method")
    parser.add_argument("target", help="Target IP address")

    args = parser.parse_args()

    probe(args.method, args.mux, args.target)


if __name__ == "__main__":
    main()
