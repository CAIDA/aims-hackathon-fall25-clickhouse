# Scamper to ClickHouse Analytics Pipeline

A complete data pipeline for analyzing [scamper](https://www.caida.org/catalog/software/scamper/) network measurement data using ClickHouse and Grafana.

## 🎯 Project Overview

This AIMS-18 Hackathon project demonstrates:
1. **Data Loading**: Convert scamper warts files to ClickHouse format
2. **Data Analysis**: SQL-based network measurement analytics
3. **Data Visualization**: RTT and DNS robustness analysis with Grafana

## 🚀 Quick Start (3 minutes)

### Step 1: Setup Environment
```bash
pip install -r requirements.txt
./setup.sh
```

### Step 2: Load Data (Choose one)

**Option A: Mock Data (Quick Demo)**
```bash
python data/generate_mock_data_simple.py
```

**Option B: Real Scamper Data**
```bash
# Requires scamper daemon running
python Scamper/generate_scamper_data.py /var/run/scamper 8.8.8.8
python Clickhouse/warts2clickhouse.py *.warts
```

### Step 3: View Results
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **ClickHouse Query Interface**: http://localhost:8123/play

## 📁 Project Structure

```
AIMS-18/
├── Clickhouse/                  
    ├── clickhouse-config.xml        # Clickhouse configuration
    └── schema.sql                   # Clickhouse table schemas
├── data/                  
    ├── generate_mock_data_simple.py # Generate mock test data and insert into Clickhouse
    ├── ping_192.172.226.122.json    # Example file converted to json (sc_warts2json)
    └── ping_192.172.226.122.warts   # Example warts file
├── docker-compose.yml               # Docker services configuration
├── Grafana/                    
    └── provisioning/
        └── datasources/
            └── clickhouse.yml       # Grafana datasource configuration
├── README.md                        # Project overview (this file)
├── requirements.txt                 # Python dependencies
├── Scamper/                  
    ├── warts2clickhouse.py          # Core: warts file processor
    └── generate_scamper_data.py     # Generate real scamper measurements
└── setup.sh                         # One-click environment setup
``

## 🗄️ Data Architecture

### Database Tables
- **`ping_measurements`**: RTT statistics and packet loss
- **`traceroute_measurements`**: Path discovery results
- **`traceroute_hops`**: Per-hop detailed information
- **`dns_measurements`**: DNS query performance

### Data Flow
```
Scamper → .warts files → warts2clickhouse.py → ClickHouse → Grafana
```

## 📊 Example Queries

**RTT Time Series Analysis:**
```sql
SELECT
  toStartOfMinute(timestamp) AS time,
  avg(rtt_avg) AS value
FROM ping_measurements
WHERE timestamp >= today() - 2
GROUP BY time
ORDER BY time
```

**Packet Loss by Target:**
```sql
SELECT
  IPv6NumToString(destination) as target,
  avg(rtt_avg) as avg_rtt,
  avg(packet_loss) * 100 as loss_percent
FROM ping_measurements
WHERE timestamp >= today() - 1
GROUP BY target
```

## 🔧 Usage Examples

### Process Existing Warts Files
```bash
./warts2clickhouse.py your_file.warts

# View imported data
curl "http://localhost:8123/?query=SELECT * FROM ping_measurements LIMIT 10"
```

### Generate Demo Data
```bash
# For Hackathon demonstration
./generate_mock_data_simple.py

# Check data count
curl "http://localhost:8123/?query=SELECT count() FROM ping_measurements"
```

## 💡 Key Features

- **Complete Pipeline**: End-to-end solution from data generation to visualization
- **Real-world Application**: Based on CAIDA scamper for actual network measurements
- **High Performance**: ClickHouse columnar storage for large-scale analytics
- **Docker Ready**: One-click deployment with Docker Compose
- **Production Ready**: Supports both IPv4 and IPv6, handles timezone correctly

## 🛠️ Technology Stack

- **Data Collection**: Scamper (CAIDA)
- **Database**: ClickHouse (Columnar storage)
- **Visualization**: Grafana
- **Deployment**: Docker + Docker Compose
- **Language**: Python 3.8+

## 📚 Common Operations

**Clear data:**
```bash
docker exec scamper-clickhouse clickhouse-client --query "TRUNCATE TABLE ping_measurements"
```

**Check ClickHouse status:**
```bash
curl http://localhost:8123/ping
```

**View Grafana logs:**
```bash
docker logs scamper-grafana
```

---

*Created for AIMS-18 Hackathon - A modern network measurement data analysis solution.*
