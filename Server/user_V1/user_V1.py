from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

try:
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    db = client[os.getenv('MONGODB_USER_DB', 'user_database')]
    users_collection = db['users']
    print("✓ Connected to MongoDB - User Database (V1)")
except Exception as e:
    print(f"✗ MongoDB Connection Error: {e}")

#Endpoints ----------------------------------

# To greet
@app.route('/', methods=['GET'])
def hello_world():
    return 'User V1 Service is running!'

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

# Helper function to simulate user creation
def userCreation(email, address):
    print("Received user data at User V1 service:", email, address)

# Helper function to simulate user update
def userUpdate(user_id, email, address):
    print(f"Updated user {user_id} at User V1 service:", email, address)

if __name__ == '__main__':
    print("Microservices user V1 !!!!")
    app.run(host='0.0.0.0', port=5000, debug=True)