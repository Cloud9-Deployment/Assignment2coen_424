from urllib.parse import quote_plus
from flask import Flask, request, jsonify
from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB Connection ------------------------------

try:
    username = quote_plus(os.getenv('MONGODB_USER'))
    password = quote_plus(os.getenv('MONGODB_PASSWORD'))
    mongo_uri = f"mongodb+srv://{username}:{password}@cluster0.4agn1ar.mongodb.net/?appName=Cluster0"
    
    # Add tlsCAFile parameter with certifi's CA bundle
    client = MongoClient(
        mongo_uri,
        tlsCAFile=certifi.where()
    )
    db = client[os.getenv('MONGODB_USER_DB', 'user_database')]
    users_collection = db['users']
    print("✓ Connected to MongoDB - User Database (V1)")
except Exception as e:
    print(f"✗ MongoDB Connection Error: {e}")

#Endpoints ----------------------------------

# To greet
@app.route('/', methods=['GET'])
def hello_world():
    results= "User V1 Service is running! With " + str(get_number_of_users()) + " users."
    return results

# To create a user
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    userCreation(email, address)
    
    return jsonify({"status": "User V1 created " + email})

@app.route('/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    userUpdate(user_id, email, address)
    
    return jsonify({"status": "User V1 updated " + user_id})

# Helper functions --------------------------------

# Function to get number of users
def get_all_users():
    print("Fetching all users from User database:")
    result = list(users_collection.find())
    return result

def get_number_of_users():
    users = get_all_users()
    print("Number of users in User V1 service:", len(users))
    return len(users)

# Helper function to simulate user creation
def userCreation(email, address):
    results = users_collection.insert_one({
        "email": email,
        "delivery_address": address
    })
    print("Inserted user ", email, " ", address, " with id:", results.inserted_id)

# Helper function to simulate user update
def userUpdate(user_id, email, address):
    print(f"Updated user {user_id} at User V1 service:", email, address)

if __name__ == '__main__':
    print("Microservices user V1 !!!!")
    app.run(host='0.0.0.0', port=5000, debug=True)
    