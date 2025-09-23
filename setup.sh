#!/bin/bash
# Setup script for Scamper to ClickHouse pipeline

set -e

echo "🚀 Setting up Scamper to ClickHouse pipeline..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Start Docker containers
echo "🐳 Starting ClickHouse and Grafana..."
docker compose up -d

# Wait for ClickHouse to be ready
echo "⏳ Waiting for ClickHouse to be ready..."
while ! curl -s http://localhost:8123/ping > /dev/null; do
    sleep 2
done

# Create database schema
echo "🗄️  Creating database tables..."
echo "Executing schema.sql..."
docker exec scamper-clickhouse clickhouse-client --query "$(cat schema.sql)"
echo "✅ Database tables created!"

echo "✅ Setup complete!"
echo ""
echo "🌐 Access points:"
echo "  - ClickHouse Web UI: http://localhost:8123/play"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "📊 Next steps:"
echo "  Option A - Process real data:"
echo "    ./warts2clickhouse.py your_file.warts"
echo "  Option B - Generate test data:"
echo "    ./generate_mock_data.py"
echo "  Then view the dashboard in Grafana: http://localhost:3000"