from influxdb_client import InfluxDBClient

URL = "http://localhost:8086"
TOKEN = "YOUR_INFLUXDB_TOKEN"
ORG = "my-org"

def test_influx_connection():
    try:
        client = InfluxDBClient(
            url=URL,
            token=TOKEN,
            org=ORG,
            timeout=5000
        )

        health = client.health()
        print("InfluxDB status:", health.status)
        print("Message:", health.message)

        client.close()
        return True

    except Exception as e:
        print("❌ Connection failed:", e)
        return False


if __name__ == "__main__":
    test_influx_connection()
