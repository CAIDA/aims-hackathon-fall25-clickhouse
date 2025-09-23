#!/usr/bin/env python3
"""
Scamper warts to ClickHouse data loader
Reads warts files and loads measurement data into ClickHouse database
"""

import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import ipaddress

try:
    from scamper import ScamperFile, ScamperPing, ScamperTrace
    from clickhouse_driver import Client
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    sys.exit(1)


class WartsClickHouseLoader:
    def __init__(self, clickhouse_host: str = 'localhost', clickhouse_port: int = 9000, clickhouse_database: str = 'scamper'):
        self.client = Client(host=clickhouse_host, port=clickhouse_port, database=clickhouse_database)
        self.ping_batch = []
        self.trace_batch = []
        self.trace_hops_batch = []
        self.batch_size = 1000

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def normalize_ip(self, addr) -> str:
        """Convert IP address to IPv6 format for ClickHouse"""
        if addr is None:
            return None
        try:
            # Convert to IPv6 format
            ip = ipaddress.ip_address(addr)
            if isinstance(ip, ipaddress.IPv4Address):
                # Convert IPv4 to IPv4-mapped IPv6
                return str(ipaddress.IPv6Address(f"::ffff:{ip}"))
            return str(ip)
        except:
            return None

    def process_ping(self, ping: ScamperPing):
        """Process ping measurement"""
        try:
            # Check if we have valid RTT data
            if ping.avg_rtt is None:
                return

            ping_data = {
                'timestamp': ping.start,
                'measurement_id': f"ping_{ping.start.timestamp()}_{hash(str(ping.dst))}",
                'source': self.normalize_ip(ping.src),
                'destination': self.normalize_ip(ping.dst),
                'rtt_avg': ping.avg_rtt.total_seconds() * 1000 if ping.avg_rtt else 0.0,
                'rtt_min': ping.min_rtt.total_seconds() * 1000 if ping.min_rtt else 0.0,
                'rtt_max': ping.max_rtt.total_seconds() * 1000 if ping.max_rtt else 0.0,
                'packet_loss': ping.nloss / ping.probe_count if ping.probe_count > 0 else 1.0,
                'probe_count': ping.probe_count,
                'probe_size': ping.probe_size
            }

            self.ping_batch.append(ping_data)

        except Exception as e:
            self.logger.warning(f"Error processing ping {ping.dst}: {e}")
            # Continue processing other pings

    def process_traceroute(self, trace: ScamperTrace):
        """Process traceroute measurement"""
        try:
            # Handle both method and property for hops (compatibility)
            hops = trace.hops() if callable(trace.hops) else trace.hops

            # Main traceroute record
            trace_data = {
                'timestamp': trace.start,
                'measurement_id': f"trace_{trace.start.timestamp()}_{hash(str(trace.dst))}",
                'source': self.normalize_ip(trace.src),
                'destination': self.normalize_ip(trace.dst),
                'hop_count': trace.hop_count,
                'completed': 1 if trace.stop_reason_str == "completed" else 0
            }
            self.trace_batch.append(trace_data)

            # Individual hops
            for hop_num, hop in enumerate(hops, 1):
                if hop is None:
                    continue

                hop_data = {
                    'timestamp': trace.start,
                    'measurement_id': trace_data['measurement_id'],
                    'source': self.normalize_ip(trace.src),
                    'destination': self.normalize_ip(trace.dst),
                    'hop_number': hop_num,
                    'hop_address': self.normalize_ip(hop.addr) if hasattr(hop, 'addr') and hop.addr else None,
                    'rtt': hop.rtt.total_seconds() * 1000 if hop.rtt is not None else 0.0,
                    'probe_ttl': hop.probe_ttl,
                    'icmp_type': hop.icmp_type,
                    'icmp_code': hop.icmp_code
                }
                self.trace_hops_batch.append(hop_data)

        except Exception as e:
            self.logger.warning(f"Error processing traceroute {trace.dst}: {e}")
            # Continue processing other traces

    # DNS measurements not supported in current scamper Python library
    # def process_dns(self, dns):
    #     """Process DNS measurement - NOT IMPLEMENTED"""
    #     pass

    def flush_batches(self):
        """Insert accumulated batches into ClickHouse"""
        try:
            if self.ping_batch:
                self.client.execute(
                    'INSERT INTO ping_measurements VALUES',
                    self.ping_batch
                )
                self.logger.info(f"Inserted {len(self.ping_batch)} ping measurements")
                self.ping_batch.clear()

            if self.trace_batch:
                self.client.execute(
                    'INSERT INTO traceroute_measurements VALUES',
                    self.trace_batch
                )
                self.logger.info(f"Inserted {len(self.trace_batch)} traceroute measurements")
                self.trace_batch.clear()

            if self.trace_hops_batch:
                self.client.execute(
                    'INSERT INTO traceroute_hops VALUES',
                    self.trace_hops_batch
                )
                self.logger.info(f"Inserted {len(self.trace_hops_batch)} traceroute hops")
                self.trace_hops_batch.clear()


        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")
            raise

    def load_warts_file(self, filename: str):
        """Load a warts file into ClickHouse"""
        self.logger.info(f"Processing {filename}")

        try:
            with ScamperFile(filename) as warts_file:
                for obj in warts_file:
                    if isinstance(obj, ScamperPing):
                        self.process_ping(obj)
                    elif isinstance(obj, ScamperTrace):
                        self.process_traceroute(obj)
                    # DNS measurements not supported in current scamper Python library

                    # Flush batches when they get large
                    total_items = (len(self.ping_batch) + len(self.trace_batch) +
                                 len(self.trace_hops_batch))
                    if total_items >= self.batch_size:
                        self.flush_batches()

                # Final flush
                self.flush_batches()

        except Exception as e:
            self.logger.error(f"Error processing {filename}: {e}")
            raise

    def test_connection(self):
        """Test ClickHouse connection"""
        try:
            result = self.client.execute('SELECT 1')
            self.logger.info("ClickHouse connection successful")
            return True
        except Exception as e:
            self.logger.error(f"ClickHouse connection failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Load scamper warts files into ClickHouse')
    parser.add_argument('files', nargs='+', help='Warts files to process')
    parser.add_argument('--host', default='localhost', help='ClickHouse host')
    parser.add_argument('--port', type=int, default=9000, help='ClickHouse port')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for inserts')

    args = parser.parse_args()

    loader = WartsClickHouseLoader(args.host, args.port)
    loader.batch_size = args.batch_size

    if not loader.test_connection():
        sys.exit(1)

    for filename in args.files:
        try:
            loader.load_warts_file(filename)
            print(f"✓ Successfully processed {filename}")
        except Exception as e:
            print(f"✗ Failed to process {filename}: {e}")
            sys.exit(1)

    print(f"✓ All files processed successfully")


if __name__ == '__main__':
    main()
