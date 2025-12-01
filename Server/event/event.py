import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import pika
import ssl
import threading
import time

load_dotenv()

app = Flask(__name__)

# Store events in memory (in production, use a database)
events_log = []

# RabbitMQ Subscriber

def get_rabbitmq_connection():
    """Create RabbitMQ connection using RABBITMQ_URL (CloudAMQP compatible)"""
    rabbitmq_url = os.getenv('RABBITMQ_URL')
    
    if not rabbitmq_url:
        print("✗ RABBITMQ_URL not set")
        return None
    
    try:
        # Use URLParameters for CloudAMQP (handles amqps:// SSL connections)
        params = pika.URLParameters(rabbitmq_url)
        params.socket_timeout = 10
        params.connection_attempts = 3
        
        connection = pika.BlockingConnection(params)
        print("✓ Connected to RabbitMQ (CloudAMQP)")
        return connection
    except Exception as e:
        print(f"✗ RabbitMQ Connection Error: {e}")
        return None


def start_event_subscriber():
    """Start RabbitMQ event subscriber in a separate thread"""

    def subscriber():
        while True:
            try:
                rabbitmq_url = os.getenv('RABBITMQ_URL')
                if not rabbitmq_url:
                    print("✗ RABBITMQ_URL not set, cannot start subscriber")
                    time.sleep(10)
                    continue

                # Use URLParameters for CloudAMQP
                params = pika.URLParameters(rabbitmq_url)
                params.socket_timeout = 10
                params.connection_attempts = 3
                params.heartbeat = 600
                params.blocked_connection_timeout = 300

                connection = pika.BlockingConnection(params)
                channel = connection.channel()

                # Declare exchange and queue
                channel.exchange_declare(
                    exchange='user_events', 
                    exchange_type='topic', 
                    durable=True
                )
                
                result = channel.queue_declare(queue='event_service_queue', durable=True)
                queue_name = result.method.queue

                # Bind to all user events using wildcard
                channel.queue_bind(
                    exchange='user_events', 
                    queue=queue_name, 
                    routing_key='user.*'
                )

                print("✓ Event service subscribed to user events")

                def callback(ch, method, properties, body):
                    try:
                        event_data = json.loads(body.decode())
                        routing_key = method.routing_key
                        
                        print(f" [x] Received event {routing_key}: {event_data}")
                        
                        # Log the event with timestamp
                        event_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "routing_key": routing_key,
                            "event_type": event_data.get("event_type"),
                            "source": event_data.get("source"),
                            "data": event_data.get("data")
                        }
                        events_log.append(event_entry)
                        
                        print(f"✓ Event logged: {event_data.get('event_type')} from {event_data.get('source')}")
                        
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

                channel.basic_consume(queue=queue_name, on_message_callback=callback)

                print("✓ Waiting for events...")
                channel.start_consuming()

            except Exception as e:
                print(f"RabbitMQ subscriber error: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)

    thread = threading.Thread(target=subscriber, daemon=True)
    thread.start()
    return thread


# Endpoints ----------------------------------

@app.route('/', methods=['GET'])
def hello_world():
    return 'Event Service is running!'

@app.route('/events', methods=['GET'])
def list_events():
    if not events_log:
        return jsonify({"status": "No events logged", "total_events": 0})
    else:
        return jsonify({
            "status": "success",
            "events": events_log,
            "total_events": len(events_log)
        })

@app.route('/events/type/<event_type>', methods=['GET'])
def list_events_by_type(event_type):
    filtered = [e for e in events_log if e.get("event_type") == event_type]
    return jsonify({
        "status": "success",
        "event_type": event_type,
        "events": filtered,
        "total": len(filtered)
    })

@app.route('/events/count', methods=['GET'])
def event_count():
    return jsonify({"total_events": len(events_log)})

@app.route('/events/stats', methods=['GET'])
def event_stats():
    stats = {}
    for event in events_log:
        event_type = event.get("event_type", "unknown")
        stats[event_type] = stats.get(event_type, 0) + 1
    return jsonify({
        "total_events": len(events_log),
        "by_type": stats
    })

@app.route('/events/clear', methods=['POST'])
def clear_events():
    global events_log
    count = len(events_log)
    events_log = []
    return jsonify({"status": f"Events log cleared. {count} events removed."})

# RabbitMQ status endpoint
@app.route('/rabbitmq/status', methods=['GET'])
def rabbitmq_status():
    """Check RabbitMQ connection status"""
    try:
        connection = get_rabbitmq_connection()
        if connection and connection.is_open:
            connection.close()
            return jsonify({"status": "connected", "message": "RabbitMQ is connected"})
        else:
            return jsonify({"status": "disconnected", "message": "RabbitMQ connection failed"}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 503


if __name__ == '__main__':
    print("=" * 50)
    print("Event Service STARTING")
    print("=" * 50)
    start_event_subscriber()
    app.run(host='0.0.0.0', port=5003, debug=True)