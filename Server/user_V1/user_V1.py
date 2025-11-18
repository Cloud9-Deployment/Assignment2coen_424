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
def entry():
    results= "User V1 Service is running! With " + str(get_number_of_users()) + " users."
    return results

# To list all users
@app.route('/users', methods=['GET'])
def list_users():
    users = get_all_users()
    if not users:
        return jsonify({"status":"User V1 ZERO user found"})
    else:
        for user in users:
            user["_id"] = str(user["_id"])  
        return jsonify({"status": users })

# To see user details by user_account_id
@app.route('/user/<user_account_id>', methods=['GET'])
def see_user(user_account_id):
    user = users_collection.find_one({"user_account_id": int(user_account_id)})
    if user:
        return jsonify({"status": "\nUsers:" +"\nUser ID:"+ str(user["user_account_id"]) 
                        +"\nEmail:" + user["email"] + "\nAddress:" + user["delivery_address"]+"\n"})  
    else:
        return jsonify({"status": "User V1 not found with id " + user_account_id}), 404

# To create a user
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    userCreation(email, address)
    
    return jsonify({"status": "User V1 created " + email})

# Update email of the user by user_account_id
@app.route('/users/<user_account_id>/email', methods=['PUT'])
def update_user_by_email(user_account_id):
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    
    user = users_collection.find_one({"user_account_id": user_account_id})

    if user:
        userUpdate(user["_id"],user_account_id, email, address)
        return jsonify({"status": "User V1 updated " + email})
    else:
        return jsonify({"status": "User V1 not found with id " + user_account_id + " to change " +email}), 404

# Update address of the user by user_account_id
@app.route('/users/<user_account_id>/address', methods=['PUT'])
def update_user_by_address(user_account_id):
    data = request.get_json()
    email = data.get("email")
    address = data.get("delivery_address")
    
    user = users_collection.find_one({"delivery_address": address})
    if user:
        userUpdate(user["_id"], email, address)
        return jsonify({"status": "User V1 updated with address " + address})
    else:
        return jsonify({"status": "User V1 not found with address " + address}), 404

# Helper functions --------------------------------

# Function to get number of users
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
    results = users_collection.insert_one({
        "user_account_id": find_new_user_id(),
        "email": email,
        "delivery_address": address
    })
    return results

# Helper function for the user update
def userUpdate(object_id, user_account_id , email, address):
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
    app.run(host='0.0.0.0', port=5000, debug=True)