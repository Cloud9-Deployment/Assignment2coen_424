from urllib.parse import quote_plus
from flask import Flask, json, request, jsonify
from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv
import pika
import ssl
import time

load_dotenv()

app = Flask(__name__)

# MongoDB Connection ------------------------------

users_collection = None

# Connect at module level
try:
    username = quote_plus(os.getenv('MONGODB_USER', ''))
    password = quote_plus(os.getenv('MONGODB_PASSWORD', ''))
    
    if username and password:
        mongo_uri = f"mongodb+srv://{username}:{password}@cluster0.4agn1ar.mongodb.net/?retryWrites=true&w=majority"

        client = MongoClient(
            mongo_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        
        client.admin.command('ping')
        
        db = client[os.getenv('MONGODB_USER_DB', 'user_database')]
        users_collection = db['users']
        print("✓ Connected to MongoDB - User Database (V1)")
    else:
        print("✗ MongoDB credentials not set")
except Exception as e:
    print(f"✗ MongoDB Connection Error: {e}")

# RabbitMQ Connection ------------------------------

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


def wait_for_rabbitmq(max_retries=5, delay=3):
    """Wait for RabbitMQ to be available"""
    for attempt in range(max_retries):
        try:
            connection = get_rabbitmq_connection()
            if connection and connection.is_open:
                print("✓ RabbitMQ is ready")
                connection.close()
                return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: RabbitMQ not ready - {e}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    print("✗ RabbitMQ not available, continuing without it")
    return False


def rabbitmq_publisher(event_type, data):
    """Publish events to RabbitMQ for synchronization"""
    try:
        connection = get_rabbitmq_connection()
        if connection is None:
            print("RabbitMQ connection not established. Skipping publish.")
            return False
            
        channel = connection.channel()

        channel.exchange_declare(
            exchange='user_events', 
            exchange_type='topic', 
            durable=True
        )

        event = {
            "event_type": event_type,
            "data": data,
            "source": "user_v1"
        }

        channel.basic_publish(
            exchange='user_events',
            routing_key=f"user.{event_type}",
            body=json.dumps(event),
            properties=pika.BasicProperties(
                delivery_mode=2,  
                content_type='application/json'
            )
        )

        connection.close()
        print(f"✓ Published event to RabbitMQ: user.{event_type}")
        return True
    except Exception as e:
        print(f"✗ RabbitMQ Publish Error: {e}")
        return False


# Endpoints ----------------------------------

@app.route('/', methods=['GET'])
def entry():
    return "User V1 Service is running!"

@app.route('/users', methods=['GET'])
def list_users():
    if users_collection is None:
        return jsonify({"status": "Database not connected"}), 503
    users = get_all_users()
    if not users:
        return jsonify({"status": "User V1 ZERO user found"})
    else:
        for user in users:
            user["_id"] = str(user["_id"])  
        return jsonify({"status": users})

@app.route('/user/<user_account_id>', methods=['GET'])
def see_user(user_account_id):
    if users_collection is None:
        return jsonify({"status": "Database not connected"}), 503
    user = users_collection.find_one({"user_account_id": int(user_account_id)})
    if user:
        return jsonify({
            "status": "\nUsers:" + "\nUser ID:" + str(user["user_account_id"]) 
            + "\nEmail:" + user["email"] + "\nAddress:" + user["delivery_address"] + "\n"
        })  
    else:
        return jsonify({"status": "User V1 not found with id " + user_account_id}), 404

@app.route('/user', methods=['POST'])
def create_user():
    if users_collection is None:
        return jsonify({"status": "Database not connected"}), 503
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    result = userCreation(email, address)
    
    rabbitmq_publisher("created", {
        "user_account_id": result,
        "email": email,
        "delivery_address": address
    })
    
    return jsonify({"status": "User V1 created " + email})

@app.route('/user/<user_account_id>/email', methods=['PUT'])
def update_user_by_email(user_account_id):
    if users_collection is None:
        return jsonify({"status": "Database not connected"}), 503
    data = request.get_json()
    new_email = data.get("email")
    
    user = users_collection.find_one({"user_account_id": int(user_account_id)})

    if user:
        old_email = user.get("email")
        address = user.get("delivery_address")
        userUpdate(user["_id"], int(user_account_id), new_email, address)
        
        rabbitmq_publisher("email_updated", {
            "user_account_id": int(user_account_id),
            "old_email": old_email,
            "new_email": new_email,
            "delivery_address": address
        })
        
        user = users_collection.find_one({"user_account_id": int(user_account_id)})
        return jsonify({
            "status": "\nUsers:" + "\nUser ID: " + str(user["user_account_id"]) 
            + "\nEmail:" + user["email"] + "\nAddress:" + user["delivery_address"] + "\n"
        }) 
    else:
        return jsonify({"status": "User V1 not found with id " + user_account_id + " to change " + new_email}), 404

@app.route('/user/<user_account_id>/address', methods=['PUT'])
def update_user_by_address(user_account_id):
    if users_collection is None:
        return jsonify({"status": "Database not connected"}), 503
    data = request.get_json()
    new_address = data.get("delivery_address")
    
    user = users_collection.find_one({"user_account_id": int(user_account_id)})
    
    if user:
        email = user.get("email")
        old_address = user.get("delivery_address")
        userUpdate(user["_id"], int(user_account_id), email, new_address)
        
        rabbitmq_publisher("address_updated", {
            "user_account_id": int(user_account_id),
            "email": email,
            "old_address": old_address,
            "new_address": new_address
        })
        
        return jsonify({"status": "User V1 updated with address " + new_address})
    else:
        return jsonify({"status": "User V1 not found with id " + user_account_id}), 404

# Helper functions --------------------------------

def get_all_users():
    result = list(users_collection.find())
    return result

def get_number_of_users():
    users = get_all_users()
    return len(users)

def find_new_user_id():
    users = get_all_users()
    if not users:
        return 1
    max_id = max(user.get("user_account_id", 0) for user in users)
    return max_id + 1

def userCreation(email, address):
    new_id = find_new_user_id()
    users_collection.insert_one({
        "user_account_id": new_id,
        "email": email,
        "delivery_address": address
    })
    return new_id

def userUpdate(object_id, user_account_id, email, address):
    results = users_collection.update_one(
        {"_id": object_id},
        {"$set": {
            "user_account_id": user_account_id,
            "email": email,
            "delivery_address": address
        }}
    )
    return results

if __name__ == '__main__':
    print("=" * 50)
    print("User V1 Service STARTING")
    print("=" * 50)
    wait_for_rabbitmq()
    app.run(host='0.0.0.0', port=5000, debug=True)