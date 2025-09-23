#!/usr/bin/env python3
"""
Simple mock data generator that directly inserts into ClickHouse
"""

import random
import sys
from datetime import datetime, timedelta, timezone

try:
    from clickhouse_driver import Client
except ImportError:
    print("Lacking required dependencies: clickhouse-driver")
    print("Install with: pip install clickhouse-driver")
    sys.exit(1)


def generate_simple_mock_data():
    """Generate simple mock data and insert directly into ClickHouse"""

    # 连接ClickHouse
    try:
        client = Client(host='localhost', port=9000, database='scamper')
        # 测试连接
        client.execute('SELECT 1')
        print("✅ ClickHouse connection successful")
    except Exception as e:
        print(f"❌ ClickHouse connection failed: {e}")
        print("Please ensure ClickHouse is running: docker ps | grep clickhouse")
        return False

    # Target addresses
    targets = [
        "::ffff:8.8.8.8",        # Google DNS (IPv4-mapped)
        "::ffff:1.1.1.1",        # Cloudflare DNS
        "::ffff:208.67.222.222", # OpenDNS
        "2001:4860:4860::8888",  # Google DNS IPv6
        "2606:4700:4700::1111"   # Cloudflare DNS IPv6
    ]

    domains = [
        "google.com",
        "cloudflare.com",
        "github.com",
        "baidu.com",
        "example.org"
    ]

    # Generate data for the last 24 hours (using UTC time)
    base_time = datetime.now(timezone.utc) - timedelta(hours=24)
    print(base_time)

    print("📊 Starting to generate mock data...")

    # Generate ping measurement data
    ping_data = []
    for hour in range(24):
        for minute in range(0, 60, 10):  # Every 10 minutes
            timestamp = base_time + timedelta(hours=hour, minutes=minute)

            for target in targets:
                # Simulate RTT data
                base_rtt = random.uniform(10, 80)
                variation = random.uniform(0.8, 1.2)

                ping_record = (
                    timestamp,                                          # timestamp
                    f"ping_{int(timestamp.timestamp())}_{hash(target)}", # measurement_id
                    "::ffff:192.168.1.100",                            # source
                    target,                                             # destination
                    base_rtt * variation,                               # rtt_avg
                    base_rtt * 0.9 * variation,                         # rtt_min
                    base_rtt * 1.1 * variation,                         # rtt_max
                    random.choice([0.0, 0.0, 0.0, 0.1, 0.2]),          # packet_loss
                    3,                                                  # probe_count
                    56                                                  # probe_size
                )
                ping_data.append(ping_record)

    # Generate traceroute measurement data
    trace_data = []
    trace_hops_data = []
    for hour in range(0, 24, 2):  # Every 2 hours
        for minute in range(0, 60, 30):  # Every 30 minutes
            timestamp = base_time + timedelta(hours=hour, minutes=minute)

            for target in targets[:2]:  # Only do traceroute for the first two targets
                measurement_id = f"trace_{int(timestamp.timestamp())}_{hash(target)}"
                hop_count = random.randint(8, 15)

                # Main traceroute record
                trace_record = (
                    timestamp,                                          # timestamp
                    measurement_id,                                     # measurement_id
                    "::ffff:192.168.1.100",                            # source
                    target,                                             # destination
                    hop_count,                                          # hop_count
                    1                                                   # completed
                )
                trace_data.append(trace_record)

                # Each hop record
                for hop_num in range(1, hop_count + 1):
                    # Generate simulated hop address
                    hop_addr = f"::ffff:10.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

                    hop_record = (
                        timestamp,                                      # timestamp
                        measurement_id,                                 # measurement_id
                        "::ffff:192.168.1.100",                        # source
                        target,                                         # destination
                        hop_num,                                        # hop_number
                        hop_addr,                                       # hop_address
                        random.uniform(1, 50 + hop_num * 2),           # rtt
                        hop_num,                                        # probe_ttl
                        11,                                             # icmp_type
                        0                                               # icmp_code
                    )
                    trace_hops_data.append(hop_record)

    # Generate DNS measurement data
    dns_data = []
    nameservers = ["::ffff:8.8.8.8", "::ffff:1.1.1.1", "2001:4860:4860::8888"]

    for hour in range(0, 24, 3):  # Every 3 hours
        for minute in range(0, 60, 20):  # Every 20 minutes
            timestamp = base_time + timedelta(hours=hour, minutes=minute)

            for domain in domains:
                for ns in nameservers:
                    dns_record = (
                        timestamp,                                      # timestamp
                        f"dns_{int(timestamp.timestamp())}_{hash(domain)}", # measurement_id
                        domain,                                         # query_name
                        'NS',                                           # query_type
                        ns,                                             # nameserver
                        random.choice([0, 0, 0, 0, 2]),                 # response_code (mostly 0=success)
                        random.uniform(0.01, 0.1),                     # rtt
                        random.randint(2, 4),                          # answer_count
                        0,                                              # authority_count
                        random.randint(0, 2)                           # additional_count
                    )
                    dns_data.append(dns_record)

    # Insert data into ClickHouse
    try:
        # Insert ping data
        if ping_data:
            client.execute(
                'INSERT INTO ping_measurements VALUES',
                ping_data
            )
            print(f"✅ Inserted {len(ping_data)} ping measurement records")

        # Insert traceroute main record
        if trace_data:
            client.execute(
                'INSERT INTO traceroute_measurements VALUES',
                trace_data
            )
            print(f"✅ Inserted {len(trace_data)} traceroute measurement records")

        # Insert traceroute hop record
        if trace_hops_data:
            client.execute(
                'INSERT INTO traceroute_hops VALUES',
                trace_hops_data
            )
            print(f"✅ Inserted {len(trace_hops_data)} traceroute hop records")

        # Insert DNS data
        if dns_data:
            client.execute(
                'INSERT INTO dns_measurements VALUES',
                dns_data
            )
            print(f"✅ Inserted {len(dns_data)} DNS measurement records")

        print(f"\n🎉 Mock data generation completed!")
        print(f"📊 Total records generated: {len(ping_data) + len(trace_data) + len(trace_hops_data) + len(dns_data)}")

        # Verify data
        ping_count = client.execute('SELECT count() FROM ping_measurements')[0][0]
        trace_count = client.execute('SELECT count() FROM traceroute_measurements')[0][0]
        dns_count = client.execute('SELECT count() FROM dns_measurements')[0][0]

        print(f"\n📈 Record statistics in the database:")
        print(f"  Ping measurement: {ping_count} records")
        print(f"  Traceroute measurement: {trace_count} records")
        print(f"  DNS measurement: {dns_count} records")

        print(f"\n🌐 Access links:")
        print(f"  ClickHouse query interface: http://localhost:8123/play")
        print(f"  Grafana dashboard: http://localhost:3000 (admin/admin)")

        return True

    except Exception as e:
        print(f"❌ Data insertion failed: {e}")
        return False


if __name__ == '__main__':
    print("🎲 Generating simple mock data for demonstration...")
    print("📝 Note: This is mock data, not real network measurement data")
    print()

    success = generate_simple_mock_data()

    if success:
        print("\n✅ Data generation successful! Now you can view the visual results in Grafana.")
    else:
        print("\n❌ Data generation failed, please check if ClickHouse is running.")
