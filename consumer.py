from kafka import KafkaConsumer
import json
import datetime

# Kafka Consumer Configuration
consumer = KafkaConsumer(
    "stock_prices",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

print("Listening for stock price updates...\n")

# Consume messages from Kafka
for message in consumer:
    stock_data = message.value

    # Convert Unix timestamp to readable format
    timestamp = datetime.datetime.fromtimestamp(stock_data["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')

    print(f"{timestamp} | {stock_data['ticker']}: ${stock_data['price']:.2f}")
