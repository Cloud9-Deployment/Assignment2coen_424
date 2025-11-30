import os
import json
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
                channel.exchange_declare(exchange='user_events', 
                                        exchange_type='topic', 
                                        durable=True)
                
                result = channel.queue_declare(queue='event_service_queue', durable=True)
                queue_name = result.method.queue

                # Bind to all user events
                channel.queue_bind(exchange='user_events', 
                                  queue=queue_name, 
                                  routing_key='user.*')

                print("✓ Event service subscribed to user events")

                def callback(ch, method, properties, body):
                    try:
                        event_data = json.loads(body.decode())
                        print(f" [x] Received event {method.routing_key}: {event_data}")
                        events_log.append({
                            "routing_key": method.routing_key,
                            "event": event_data
                        })
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
        return jsonify({"status": "No events logged"})
    else:
        return jsonify({"status": events_log, "total_events": len(events_log)})

# To get event count
@app.route('/events/count', methods=['GET'])
def event_count():
    return jsonify({"total_events": len(events_log)})

# To clear events log
@app.route('/events/clear', methods=['POST'])
def clear_events():
    global events_log
    events_log = []
    return jsonify({"status": "Events log cleared"})


if __name__ == '__main__':
    print("Event Service ACTIVATE!!!!")
    start_event_subscriber()
    app.run(host='0.0.0.0', port=5003, debug=True)
