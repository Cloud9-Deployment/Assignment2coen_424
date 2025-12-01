import os
from urllib.parse import quote_plus
import certifi
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pymongo import MongoClient
import json

load_dotenv()

app = Flask(__name__)

# Order statuses: "under process", "shipping", "delivered"

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
    """Start RabbitMQ event subscriber in a separate thread to handle user events"""
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

                # Declare the exchange (must match user service)
                channel.exchange_declare(
                    exchange='user_events', 
                    exchange_type='topic', 
                    durable=True
                )
                
                # Declare a queue for order service
                result = channel.queue_declare(queue='order_service_queue', durable=True)
                queue_name = result.method.queue

                # Bind to user events - listen for email and address updates
                channel.queue_bind(
                    exchange='user_events', 
                    queue=queue_name, 
                    routing_key='user.email_updated'
                )
                channel.queue_bind(
                    exchange='user_events', 
                    queue=queue_name, 
                    routing_key='user.address_updated'
                )
                channel.queue_bind(
                    exchange='user_events', 
                    queue=queue_name, 
                    routing_key='user.*'  # Listen to all user events
                )

                print("✓ Order service subscribed to user events")

                def callback(ch, method, properties, body):
                    """Handle incoming events and synchronize data"""
                    try:
                        event_data = json.loads(body.decode())
                        routing_key = method.routing_key
                        print(f" [x] Received event {routing_key}: {event_data}")
                        
                        event_type = event_data.get("event_type")
                        data = event_data.get("data", {})
                        
                        # Handle email update synchronization
                        if event_type == "email_updated":
                            user_id = data.get("user_account_id")
                            new_email = data.get("new_email")
                            if user_id and new_email:
                                sync_user_email(user_id, new_email)
                                print(f"✓ Synchronized email for user {user_id} to {new_email}")
                        
                        # Handle address update synchronization
                        elif event_type == "address_updated":
                            user_id = data.get("user_account_id")
                            new_address = data.get("new_address")
                            if user_id and new_address:
                                sync_user_address(user_id, new_address)
                                print(f"✓ Synchronized address for user {user_id} to {new_address}")
                        
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


# Synchronization helper functions --------------------------------

def sync_user_email(user_id, new_email):
    """Synchronize user email across all their orders"""
    if orders_collection is not None:
        result = orders_collection.update_many(
            {"user_id": str(user_id)},
            {"$set": {"user_email": new_email}}
        )
        print(f"Updated {result.modified_count} orders with new email")
        return result.modified_count
    return 0

def sync_user_address(user_id, new_address):
    """Synchronize user address across all their orders"""
    if orders_collection is not None:
        result = orders_collection.update_many(
            {"user_id": str(user_id)},
            {"$set": {"user_address": new_address}}
        )
        print(f"Updated {result.modified_count} orders with new address")
        return result.modified_count
    return 0


#Endpoints ----------------------------------

# To greet
@app.route('/', methods=['GET'])
def greetings():
    return 'Order Service is running!'

# To list all orders
@app.route('/orders', methods=['GET'])
def list_orders():
    orders = get_all_orders()
    if not orders:
        return jsonify({"status": "No orders found"})
    else:
        for order in orders:
            order["_id"] = str(order["_id"])  
        return jsonify({"status": orders})

# To get orders by status
@app.route('/orders/status/<status>', methods=['GET'])
def list_orders_by_status(status):
    orders = get_orders_by_status(status)
    if not orders:
        return jsonify({"status": f"No orders found with status: {status}"})
    else:
        for order in orders:
            order["_id"] = str(order["_id"])  
        return jsonify({"status": orders})

# To see order details by order_id
@app.route('/order/<order_id>', methods=['GET'])
def see_order(order_id):
    order = orderExists(order_id)
    if order:
        order["_id"] = str(order["_id"])
        return jsonify({"status": order})
    else:
        return jsonify({"status": "Order not found with id " + order_id}), 404

# To create an order
@app.route('/order', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get("user_id")
    items = data.get("items")
    email = data.get("email", "N/A")
    address = data.get("delivery_address", "N/A")

    if items and isinstance(items, list):
        order_items = items
    else:
        item = data.get("item")
        quantity = data.get("quantity", 1)
        order_items = [{"item": item, "quantity": quantity}]

    result = orderCreation(user_id, order_items, email, address)

    return jsonify({
        "status": "Order created for user " + str(user_id), 
        "order_id": str(result.inserted_id), 
        "items": order_items
    })


# To update status of an order
@app.route('/order/<order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()
    status = data.get("status")
    
    if orderStatusUpdate(order_id, status):
        return jsonify({"status": "Order " + order_id + " updated to " + status})
    else:
        return jsonify({"status": "Failed to update order. Invalid status or order not found."}), 400

# To update order email
@app.route('/order/<order_id>/email', methods=['PUT'])
def update_order_email(order_id):
    data = request.get_json()
    email = data.get("email")
    
    order = orderExists(order_id)
    if order:
        orders_collection.update_one(
            {"order_id": int(order_id)},
            {"$set": {"user_email": email}}
        )
        return jsonify({"status": f"Order {order_id} email updated to {email}"})
    else:
        return jsonify({"status": "Order not found with id " + order_id}), 404

# To update order address
@app.route('/order/<order_id>/address', methods=['PUT'])
def update_order_address(order_id):
    data = request.get_json()
    address = data.get("delivery_address")
    
    order = orderExists(order_id)
    if order:
        orders_collection.update_one(
            {"order_id": int(order_id)},
            {"$set": {"user_address": address}}
        )
        return jsonify({"status": f"Order {order_id} address updated to {address}"})
    else:
        return jsonify({"status": "Order not found with id " + order_id}), 404

# To update user contact info across all their orders (direct API call)
@app.route('/user/contact/<user_id>', methods=['PUT'])
def update_user_contact(user_id):
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    
    updated = userContactUpdate(user_id, email, address)
    
    if updated:
        return jsonify({"status": "User " + user_id + " contact updated in orders"})
    else:
        return jsonify({"status": "No orders found for user " + user_id}), 404

# Helper functions --------------------------------

# Function to get all orders
def get_all_orders():
    result = list(orders_collection.find())
    return result

# Function to get orders by status
def get_orders_by_status(status):
    result = list(orders_collection.find({"status": status}))
    return result

# Function to get number of orders
def get_number_of_orders():
    count = get_all_orders()
    return len(count)

# Function to find new order_id
def find_new_order_id():
    orders = get_all_orders()
    if not orders:
        return 1
    max_id = max(order.get("order_id", 0) for order in orders)
    return max_id + 1

# Helper function to create an order
def orderCreation(user_id, items, email, address):
    results = orders_collection.insert_one({
        "order_id": find_new_order_id(),
        "user_id": str(user_id),
        "items": items,
        "user_email": email,
        "user_address": address,
        "status": "under process"
    })
    return results

# Helper function to check if order exists
def orderExists(order_id):
    order = orders_collection.find_one({"order_id": int(order_id)})
    return order

# Helper function to see if user has any orders
def userDidOrder(user_id):
    orders = list(orders_collection.find({"user_id": str(user_id)}))
    return orders

# Helper function to update order status
def orderStatusUpdate(order_id, status):
    valid_statuses = ["under process", "shipping", "delivered"]
    if status not in valid_statuses:
        return False
    if orderExists(order_id):
        orders_collection.update_one(
            {"order_id": int(order_id)},
            {"$set": {"status": status}}
        )
        return True
    return False

# Helper function to update user contact info across all their orders
def userContactUpdate(user_id, email, address):
    update_fields = {}
    if email:
        update_fields["user_email"] = email
    if address:
        update_fields["user_address"] = address
    
    if update_fields and userDidOrder(user_id):
        orders_collection.update_many(
            {"user_id": str(user_id)},
            {"$set": update_fields}
        )
        return True
    return False

if __name__ == '__main__':
    print("Microservices order ACTIVATE!!!!")
    start_event_subscriber()
    app.run(host='0.0.0.0', port=5002, debug=True)