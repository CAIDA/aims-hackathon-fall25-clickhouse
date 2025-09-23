#!/usr/bin/env python3
"""
Simple scamper ping measurement with data saving
Usage: ./test.py $mux $ip
Example: ./test.py /var/run/scamper 8.8.8.8
"""

import sys
from datetime import datetime, timedelta
from scamper import ScamperCtrl, ScamperFile

if len(sys.argv) != 3:
    print("usage: test.py $mux $ip")
    sys.exit(-1)

# Create output file with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
target_ip = sys.argv[2].replace(":", "_")  # Replace colons for valid filename
output_file = f"ping_{target_ip}_{timestamp}.warts"

print(f"Starting ping measurement to {sys.argv[2]}")
print(f"Saving data to: {output_file}")

# Open warts file for writing
outfile = ScamperFile(output_file, 'w')

# Connect to scamper daemon and attach output file
with ScamperCtrl(mux=sys.argv[1], outfile=outfile) as ctrl:
    ctrl.add_vps(ctrl.vps())
    for i in ctrl.instances():
        ctrl.do_ping(sys.argv[2], inst=i)

        # Wait for response
        for o in ctrl.responses(timeout=timedelta(seconds=10)):
            if o.min_rtt:
                rtt_ms = o.min_rtt.total_seconds() * 1000
                print(f"{sys.argv[2]}: {rtt_ms:.1f} ms")
            else:
                print(f"No response from {sys.argv[2]}")

            print(f"✓ Data saved to: {output_file}")
            break
        else:
            print(f"Timeout: No response from {sys.argv[2]}")
            print(f"✓ Data saved to: {output_file}")

print("Measurement complete!")
print(f"Use './warts2clickhouse.py {output_file}' to import data")