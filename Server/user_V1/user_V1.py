from urllib.parse import quote_plus
from flask import Flask, json, request, jsonify
from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv
import pika
import time

load_dotenv()

app = Flask(__name__)

# MongoDB Connection ------------------------------

users_collection = None
def connect_to_mongodb():

    try:
        username = quote_plus(os.getenv('MONGODB_USER'))
        password = quote_plus(os.getenv('MONGODB_PASSWORD'))
        
        # Use proper MongoDB Atlas connection string
        mongo_uri = f"mongodb+srv://{username}:{password}@cluster0.4agn1ar.mongodb.net/?retryWrites=true&w=majority"

        # Add tlsCAFile parameter with certifi's CA bundle
        client = MongoClient(
            mongo_uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        
        # Test the connection
        client.admin.command('ping')
        
        db = client[os.getenv('MONGODB_USER_DB', 'user_database')]
        users_collection = db['users']
        print("✓ Connected to MongoDB - User Database (V1)")
    except Exception as e:
        print(f"✗ MongoDB Connection Error: {e}")
        print("Make sure:")
        print("  1. Your MongoDB Atlas cluster is running")
        print("  2. Credentials are correct (MONGODB_USER and MONGODB_PASSWORD)")
        print("  3. Your IP address is whitelisted in MongoDB Atlas")
        print("  4. You have internet connection")

#RabbitMQ Connection ------------------------------
#Main function to establish RabbitMQ connection
def RabbitMQ_connection():
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        credentials=credentials)

    try:
        rabbitmq_connection = pika.BlockingConnection(parameters)
        print("✓ Connected to RabbitMQ")
        return rabbitmq_connection
    except Exception as e:
        print(f"✗ RabbitMQ Connection Error: {e}")
        return None


#Test the RabbitMQ connection
def wait_for_rabbitmq(max_retries=5, delay=3):
    """Wait for RabbitMQ to be available"""
    for attempt in range(max_retries):
        try:
            connection = RabbitMQ_connection()
            if connection and connection.is_open:
                print("✓ RabbitMQ is ready")
                connection.close()
                return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: RabbitMQ not ready - {e}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    return False


# RabbitMQ publisher
def rabbitmq_publisher(event_type, data):
    """Publish events to RabbitMQ for synchronization"""
    try:
        connection = RabbitMQ_connection()
        if connection is None:
            print("RabbitMQ connection not established. Cannot publish message.")
            return False
            
        channel = connection.channel()

        channel.exchange_declare(exchange='user_events', 
                                exchange_type='topic', 
                                durable=True)

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


#Endpoints ----------------------------------

# To greet
@app.route('/', methods=['GET'])
def entry():
    results = "User V1 Service is running!"
    return results

# To list all users
@app.route('/users', methods=['GET'])
def list_users():
    users = get_all_users()
    if not users:
        return jsonify({"status": "User V1 ZERO user found"})
    else:
        for user in users:
            user["_id"] = str(user["_id"])  
        return jsonify({"status": users})

# To see user details by user_account_id
@app.route('/user/<user_account_id>', methods=['GET'])
def see_user(user_account_id):
    user = users_collection.find_one({"user_account_id": int(user_account_id)})
    if user:
        return jsonify({
            "status": "\nUsers:" + "\nUser ID:" + str(user["user_account_id"]) 
            + "\nEmail:" + user["email"] + "\nAddress:" + user["delivery_address"] + "\n"
        })  
    else:
        return jsonify({"status": "User V1 not found with id " + user_account_id}), 404

# To create a user
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    result = userCreation(email, address)
    
    # Publish user created event
    rabbitmq_publisher("created", {
        "user_account_id": result,
        "email": email,
        "delivery_address": address
    })
    
    return jsonify({"status": "User V1 created " + email})

# Update email of the user by user_account_id
@app.route('/user/<user_account_id>/email', methods=['PUT'])
def update_user_by_email(user_account_id):
    data = request.get_json()
    new_email = data.get("email")
    
    user = users_collection.find_one({"user_account_id": int(user_account_id)})

    if user:
        old_email = user.get("email")
        address = user.get("delivery_address")
        userUpdate(user["_id"], int(user_account_id), new_email, address)
        
        # PUBLISH EVENT FOR SYNCHRONIZATION - This is the key fix!
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

# Update address of the user by user_account_id
@app.route('/user/<user_account_id>/address', methods=['PUT'])
def update_user_by_address(user_account_id):
    data = request.get_json()
    new_address = data.get("delivery_address")
    
    user = users_collection.find_one({"user_account_id": int(user_account_id)})
    
    if user:
        email = user.get("email")
        old_address = user.get("delivery_address")
        userUpdate(user["_id"], int(user_account_id), email, new_address)
        
        # PUBLISH EVENT FOR SYNCHRONIZATION - This is the key fix!
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

# Function to get all users
def get_all_users():
    result = list(users_collection.find())
    return result

# Function to get number of users
def get_number_of_users():
    users = get_all_users()
    return len(users)

# Function to find new user_account_id
def find_new_user_id():
    users = get_all_users()
    if not users:
        return 1
    max_id = max(user.get("user_account_id", 0) for user in users)
    return max_id + 1

# Helper function for the user creation
def userCreation(email, address):
    new_id = find_new_user_id()
    users_collection.insert_one({
        "user_account_id": new_id,
        "email": email,
        "delivery_address": address
    })
    return new_id

# Helper function for the user update
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
    print("Microservices user V1 ACTIVATE!!!!")
    connect_to_mongodb()
    print("Waiting for RabbitMQ to be ready...")
    wait_for_rabbitmq()
    app.run(host='0.0.0.0', port=5000, debug=True)