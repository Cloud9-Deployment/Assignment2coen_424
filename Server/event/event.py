import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Store events in memory (in production, use a database)
events_log = []

# RabbitMQ Subscriber
def start_event_subscriber():
    """Start RabbitMQ event subscriber in a separate thread"""
    import threading
    import pika

    def subscriber():
        while True:
            try:
                rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
                rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
                rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
                rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

                credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
                parameters = pika.ConnectionParameters(
                    host=rabbitmq_host,
                    port=rabbitmq_port,
                    credentials=credentials
                )

                connection = pika.BlockingConnection(parameters)
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
                import time
                time.sleep(5)

    thread = threading.Thread(target=subscriber, daemon=True)
    thread.start()
    return thread


# Endpoints ----------------------------------

# To verify event service is working
@app.route('/', methods=['GET'])
def hello_world():
    return 'Event Service is running!'

# To list all events
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

# To get events by type
@app.route('/events/type/<event_type>', methods=['GET'])
def list_events_by_type(event_type):
    filtered = [e for e in events_log if e.get("event_type") == event_type]
    return jsonify({
        "status": "success",
        "event_type": event_type,
        "events": filtered,
        "total": len(filtered)
    })

# To get event count
@app.route('/events/count', methods=['GET'])
def event_count():
    return jsonify({"total_events": len(events_log)})

# To get event statistics
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

# To clear events log
@app.route('/events/clear', methods=['POST'])
def clear_events():
    global events_log
    count = len(events_log)
    events_log = []
    return jsonify({"status": f"Events log cleared. {count} events removed."})


if __name__ == '__main__':
    print("=" * 50)
    print("Event Service ACTIVATE!!!!")
    print("=" * 50)
    start_event_subscriber()
    app.run(host='0.0.0.0', port=5003, debug=True)