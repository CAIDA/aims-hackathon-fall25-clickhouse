#!/usr/bin/env python3
"""
Simple mock data generator that directly inserts into ClickHouse
无需依赖scamper或warts2clickhouse，直接生成模拟数据用于演示
"""

import random
import sys
from datetime import datetime, timedelta, timezone

try:
    from clickhouse_driver import Client
except ImportError:
    print("缺少依赖: clickhouse-driver")
    print("安装方法: pip install clickhouse-driver")
    sys.exit(1)


def generate_simple_mock_data():
    """生成简单的模拟数据并直接插入ClickHouse"""

    # 连接ClickHouse
    try:
        client = Client(host='localhost', port=9000)
        # 测试连接
        client.execute('SELECT 1')
        print("✅ ClickHouse连接成功")
    except Exception as e:
        print(f"❌ ClickHouse连接失败: {e}")
        print("请确保ClickHouse正在运行: docker ps | grep clickhouse")
        return False

    # 目标地址
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

    # 生成最近24小时的数据 (使用UTC时间)
    base_time = datetime.now(timezone.utc) - timedelta(hours=24)
    print(base_time)

    print("📊 开始生成模拟数据...")

    # 生成ping测量数据
    ping_data = []
    for hour in range(24):
        for minute in range(0, 60, 10):  # 每10分钟
            timestamp = base_time + timedelta(hours=hour, minutes=minute)

            for target in targets:
                # 模拟RTT数据
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

    # 生成traceroute测量数据
    trace_data = []
    trace_hops_data = []
    for hour in range(0, 24, 2):  # 每2小时
        for minute in range(0, 60, 30):  # 每30分钟
            timestamp = base_time + timedelta(hours=hour, minutes=minute)

            for target in targets[:2]:  # 只对前两个目标做traceroute
                measurement_id = f"trace_{int(timestamp.timestamp())}_{hash(target)}"
                hop_count = random.randint(8, 15)

                # 主traceroute记录
                trace_record = (
                    timestamp,                                          # timestamp
                    measurement_id,                                     # measurement_id
                    "::ffff:192.168.1.100",                            # source
                    target,                                             # destination
                    hop_count,                                          # hop_count
                    1                                                   # completed
                )
                trace_data.append(trace_record)

                # 逐跳记录
                for hop_num in range(1, hop_count + 1):
                    # 生成模拟的hop地址
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

    # 生成DNS测量数据
    dns_data = []
    nameservers = ["::ffff:8.8.8.8", "::ffff:1.1.1.1", "2001:4860:4860::8888"]

    for hour in range(0, 24, 3):  # 每3小时
        for minute in range(0, 60, 20):  # 每20分钟
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

    # 插入数据到ClickHouse
    try:
        # 插入ping数据
        if ping_data:
            client.execute(
                'INSERT INTO ping_measurements VALUES',
                ping_data
            )
            print(f"✅ 插入了 {len(ping_data)} 条ping测量记录")

        # 插入traceroute主记录
        if trace_data:
            client.execute(
                'INSERT INTO traceroute_measurements VALUES',
                trace_data
            )
            print(f"✅ 插入了 {len(trace_data)} 条traceroute测量记录")

        # 插入traceroute hop记录
        if trace_hops_data:
            client.execute(
                'INSERT INTO traceroute_hops VALUES',
                trace_hops_data
            )
            print(f"✅ 插入了 {len(trace_hops_data)} 条traceroute hop记录")

        # 插入DNS数据
        if dns_data:
            client.execute(
                'INSERT INTO dns_measurements VALUES',
                dns_data
            )
            print(f"✅ 插入了 {len(dns_data)} 条DNS测量记录")

        print(f"\n🎉 模拟数据生成完成!")
        print(f"📊 总计生成了 {len(ping_data) + len(trace_data) + len(trace_hops_data) + len(dns_data)} 条记录")

        # 验证数据
        ping_count = client.execute('SELECT count() FROM ping_measurements')[0][0]
        trace_count = client.execute('SELECT count() FROM traceroute_measurements')[0][0]
        dns_count = client.execute('SELECT count() FROM dns_measurements')[0][0]

        print(f"\n📈 数据库中的记录统计:")
        print(f"  Ping测量: {ping_count} 条")
        print(f"  Traceroute测量: {trace_count} 条")
        print(f"  DNS测量: {dns_count} 条")

        print(f"\n🌐 访问链接:")
        print(f"  ClickHouse查询界面: http://localhost:8123/play")
        print(f"  Grafana仪表板: http://localhost:3000 (admin/admin)")

        return True

    except Exception as e:
        print(f"❌ 数据插入失败: {e}")
        return False


if __name__ == '__main__':
    print("🎲 生成简单模拟数据用于演示...")
    print("📝 注意: 这是模拟数据，不是真实的网络测量数据")
    print()

    success = generate_simple_mock_data()

    if success:
        print("\n✅ 数据生成成功! 现在可以在Grafana中查看可视化结果了。")
    else:
        print("\n❌ 数据生成失败，请检查ClickHouse是否正在运行。")