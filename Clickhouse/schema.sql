-- ClickHouse schema for scamper measurements

-- Create (if needed) and use the Scamper database
CREATE DATABASE IF NOT EXISTS scamper;
USE scamper;

-- Ping measurements table
CREATE TABLE IF NOT EXISTS ping_measurements (
    timestamp DateTime64(3),
    measurement_id String,
    source IPv6,
    destination IPv6,
    rtt_avg Float32,
    rtt_min Float32,
    rtt_max Float32,
    packet_loss Float32,
    probe_count UInt16,
    probe_size UInt16
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, destination)
SETTINGS index_granularity = 8192;

-- Traceroute measurements table
CREATE TABLE IF NOT EXISTS traceroute_measurements (
    timestamp DateTime64(3),
    measurement_id String,
    source IPv6,
    destination IPv6,
    hop_count UInt8,
    completed UInt8
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, destination)
SETTINGS index_granularity = 8192;

-- Traceroute hops table (detailed hop information)
CREATE TABLE IF NOT EXISTS traceroute_hops (
    timestamp DateTime64(3),
    measurement_id String,
    source IPv6,
    destination IPv6,
    hop_number UInt8,
    rtt Float32,
    probe_ttl UInt8,
    icmp_type Nullable(UInt8),
    icmp_code Nullable(UInt8)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, destination, hop_number)
SETTINGS index_granularity = 8192;

-- DNS measurements table (for RFC2182 analysis)
CREATE TABLE IF NOT EXISTS dns_measurements (
    timestamp DateTime64(3),
    measurement_id String,
    query_name String,
    query_type String,
    nameserver IPv6,
    response_code UInt16,
    rtt Float32,
    answer_count UInt16,
    authority_count UInt16,
    additional_count UInt16
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, query_name)
SETTINGS index_granularity = 8192;

-- Create views for common analytics queries
CREATE VIEW IF NOT EXISTS ping_stats AS
SELECT
    toStartOfHour(timestamp) as hour,
    destination,
    avg(rtt_avg) as avg_rtt,
    min(rtt_min) as min_rtt,
    max(rtt_max) as max_rtt,
    avg(packet_loss) as avg_loss,
    count() as measurement_count
FROM ping_measurements
GROUP BY hour, destination;

CREATE VIEW IF NOT EXISTS dns_robustness AS
SELECT
    toStartOfDay(timestamp) as day,
    query_name,
    uniq(nameserver) as unique_nameservers,
    countIf(response_code = 0) as successful_queries,
    count() as total_queries
FROM dns_measurements
WHERE query_type = 'NS'
GROUP BY day, query_name;
