import os
from urllib.parse import quote_plus
import certifi
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pymongo import MongoClient





load_dotenv()

app = Flask(__name__)

# MongoDB Connection ------------------------------

orders_collection = None

try:
    username = quote_plus(os.getenv('MONGODB_USER'))
    password = quote_plus(os.getenv('MONGODB_PASSWORD'))

    mongo_uri = f"mongodb+srv://{username}:{password}@cluster0.4agn1ar.mongodb.net/?retryWrites=true&w=majority"

    client = MongoClient(
        mongo_uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000
    )

    client.admin.command('ping')

    db = client[os.getenv('MONGODB_ORDER_DB', 'order_database')]
    orders_collection = db['orders']
    print("✓ Connected to MongoDB - Order Database")
except Exception as e:
    print(f"✗ MongoDB Connection Error: {e}")
    print("Make sure:")
    print("  1. Your MongoDB Atlas cluster is running")
    print("  2. Credentials are correct (MONGODB_USER and MONGODB_PASSWORD)")
    print("  3. Your IP address is whitelisted in MongoDB Atlas")
    print("  4. You have internet connection")

#RabbitMQ Connection ------------------------------

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

                result = channel.queue_declare(queue='user_events')
                queue_name = result.method.queue

                print("✓ Order service subscribed to user events")

                def callback(ch, method, properties, body):
                    try:
                        print(f" [x] Received {method.routing_key} : {body.decode()}")
                        # Here you would add logic to handle the event, e.g., update orders
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

                channel.basic_consume(queue=queue_name, on_message_callback=callback)

                print("✓ Waiting for user events...")
                channel.start_consuming()

            except Exception as e:
                print(f"RabbitMQ subscriber error: {e}")
                print("Retrying in 5 seconds...")
                import time
                time.sleep(5)

    thread = threading.Thread(target=subscriber, daemon=True)
    thread.start()
    return thread


#Endpoints ----------------------------------

# To greet
@app.route('/', methods=['GET'])
def hello_world():
    return 'Order Service is running!'

# To create an order
@app.route('/order', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get("user_id")
    item = data.get("item")
    quantity = data.get("quantity")
    orderCreation(user_id, item, quantity)
    
    return jsonify({"status": "Order created for user " + user_id})


# To update status of an order
@app.route('/order/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()
    status = data.get("status")
    orderStatusUpdate(order_id, status)
    
    return jsonify({"status": "Order " + order_id + " updated to " + status})

# To update user email or address
@app.route('/user/contact/<user_id>', methods=['PUT'])
def update_user_contact(user_id):
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    userContactUpdate(user_id, email, address)
    
    return jsonify({"status": "User " + user_id + " contact updated"})

# Helper functions --------------------------------

# Helper function to simulate order creation
def orderCreation(user_id, item, quantity):
    print("Received order data at Order service:", user_id, item, quantity)

# Helper function to simulate order status update
def orderStatusUpdate(order_id, status):
    print(f"Updated order {order_id} at Order service:", status)

# Helper function to simulate user contact update
def userContactUpdate(user_id, email, address):
    print(f"Updated user {user_id} contact at Order service:", email, address)

if __name__ == '__main__':
    print("Microservices Order !!!!")
    start_event_subscriber()
    app.run(host='0.0.0.0', port=5002, debug=True)