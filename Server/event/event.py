import os
from dotenv import load_dotenv
from flask import Flask, jsonify
import json
import pika
import threading
import time
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# In-memory event log
events_log = []


def get_rabbitmq_connection():
    """Create RabbitMQ connection using RABBITMQ_URL (CloudAMQP compatible)"""
    rabbitmq_url = os.getenv('RABBITMQ_URL')
    
    if not rabbitmq_url:
        print("✗ RABBITMQ_URL not set")
        return None
    
    try:
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

                print("🔄 Event service connecting to RabbitMQ...")

                params = pika.URLParameters(rabbitmq_url)
                params.socket_timeout = 10
                params.connection_attempts = 3
                params.heartbeat = 600
                params.blocked_connection_timeout = 300

                connection = pika.BlockingConnection(params)
                channel = connection.channel()

                # Declare the exchange (must match user service)
                channel.exchange_declare(
                    exchange='user_events', 
                    exchange_type='topic', 
                    durable=True
                )
                
                # Declare a queue for event service
                result = channel.queue_declare(queue='event_service_queue', durable=True)
                queue_name = result.method.queue

                # Bind to ALL user events using wildcard
                channel.queue_bind(
                    exchange='user_events', 
                    queue=queue_name, 
                    routing_key='user.*'
                )

                print("✓ Event service subscribed to user.* events")

                def callback(ch, method, properties, body):
                    """Log all incoming events"""
                    try:
                        event_data = json.loads(body.decode())
                        routing_key = method.routing_key
                        
                        # Create event record
                        event_record = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "routing_key": routing_key,
                            "event_type": event_data.get("event_type"),
                            "source": event_data.get("source"),
                            "data": event_data.get("data", {})
                        }
                        
                        events_log.append(event_record)
                        print(f" [x] Logged event: {routing_key} - {event_data.get('event_type')}")
                        
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

                channel.basic_consume(queue=queue_name, on_message_callback=callback)

                print("✓ Event service waiting for events...")
                channel.start_consuming()

            except Exception as e:
                print(f"RabbitMQ subscriber error: {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)

    thread = threading.Thread(target=subscriber, daemon=True)
    thread.start()
    print("✓ Event service RabbitMQ subscriber thread started")
    return thread


# Endpoints ----------------------------------

@app.route('/', methods=['GET'])
def greetings():
    return 'Event Service is running!'


@app.route('/events', methods=['GET'])
def get_all_events():
    """Get all logged events"""
    return jsonify({
        "status": "success",
        "count": len(events_log),
        "events": events_log
    })


@app.route('/events/type/<event_type>', methods=['GET'])
def get_events_by_type(event_type):
    """Get events filtered by type"""
    filtered = [e for e in events_log if e.get("event_type") == event_type]
    return jsonify({
        "status": "success",
        "count": len(filtered),
        "events": filtered
    })


@app.route('/events/count', methods=['GET'])
def get_event_count():
    """Get count of all events"""
    return jsonify({
        "status": "success",
        "total_events": len(events_log)
    })


@app.route('/events/stats', methods=['GET'])
def get_event_stats():
    """Get event statistics by type"""
    stats = {}
    for event in events_log:
        event_type = event.get("event_type", "unknown")
        stats[event_type] = stats.get(event_type, 0) + 1
    
    return jsonify({
        "status": "success",
        "total_events": len(events_log),
        "by_type": stats
    })


@app.route('/events/clear', methods=['DELETE'])
def clear_events():
    """Clear all logged events"""
    global events_log
    count = len(events_log)
    events_log = []
    return jsonify({
        "status": "success",
        "message": f"Cleared {count} events"
    })


@app.route('/rabbitmq/status', methods=['GET'])
def rabbitmq_status():
    """Check RabbitMQ connection status"""
    rabbitmq_url = os.getenv('RABBITMQ_URL')
    
    if not rabbitmq_url:
        return jsonify({
            "status": "error",
            "message": "RABBITMQ_URL not configured"
        }), 503
    
    try:
        connection = get_rabbitmq_connection()
        if connection:
            connection.close()
            return jsonify({
                "status": "connected",
                "message": "RabbitMQ connection successful"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to connect to RabbitMQ"
            }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 503


# ============================================================
# START RABBITMQ SUBSCRIBER AT MODULE LOAD
# This ensures it runs with Gunicorn (not just when __main__)
# ============================================================
print("=" * 50)
print("Event Service STARTING")
print("=" * 50)

# Start the RabbitMQ subscriber thread when module loads
start_event_subscriber()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)