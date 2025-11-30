import requests
import random
import yaml
import json
from flask import Flask, request, jsonify
import os
app = Flask(__name__)

# http://localhost:5000/ is the user V1
# http://localhost:5001/ is the user V2
# http://localhost:5002/ is the order service
# http://localhost:8000/ is the api gateway

# Fecth environment variables

# Service URLs 
USER_V1_URL = os.getenv('USER_V1_URL', 'http://localhost:5000')
USER_V2_URL = os.getenv('USER_V2_URL', 'http://localhost:5001')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://localhost:5002')
EVENT_SERVICE_URL = os.getenv('EVENT_SERVICE_URL', 'http://localhost:5003')

# Configuration file path
CONFIG_FILE = os.getenv('CONFIG_FILE', 'gateway_config.yaml')

def load_config():
    """Load configuration from YAML file"""
    default_config = {
        'strangler_pattern': {
            'enabled': True,
            'v1_percentage': 0,  # P percentage goes to V1
            'v2_percentage': 100     # (1-P) percentage goes to V2
        },
        'services': {
            'user_v1': USER_V1_URL,
            'user_v2': USER_V2_URL,
            'order': ORDER_SERVICE_URL,
            'event': EVENT_SERVICE_URL
        },
        'timeout': 10
    }
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), CONFIG_FILE)
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                print(f"✓ Loaded configuration from {CONFIG_FILE}")
                # Merge with defaults
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        else:
            print(f"Config file not found, using defaults (V1: 100%, V2: 0%)")
            return default_config
    except Exception as e:
        print(f"Error loading config: {e}, using defaults")
        return default_config


# Load initial configuration
config = load_config()


def reload_config():
    """Reload configuration from file"""
    global config
    config = load_config()
    return config


def get_user_service_url():
    """
    Strangler Pattern: Determine which user service version to route to
    Based on configured percentage P:
    - P% of requests go to V1
    - (100-P)% of requests go to V2
    """
    if not config['strangler_pattern']['enabled']:
        return config['services'].get('user_v1', USER_V1_URL)
    
    v1_percentage = config['strangler_pattern']['v1_percentage']
    
    # Generate random number between 0-100
    random_value = random.randint(1, 100)
    
    if random_value <= v1_percentage:
        url = config['services'].get('user_v1', USER_V1_URL)
        print(f"[Strangler] Routing to User V1 (random: {random_value}, threshold: {v1_percentage})")
        return url
    else:
        url = config['services'].get('user_v2', USER_V2_URL)
        print(f"[Strangler] Routing to User V2 (random: {random_value}, threshold: {v1_percentage})")
        return url



# Gateway endpoints ----------------------------------

# To verify gateway is working
@app.route('/', methods=['GET'])
def hello_world():
    response = "\nGateway working. Responses from services:\n"
    try:
        res1 = requests.get("http://localhost:5000/", timeout=2)
        response += res1.text if res1.status_code == 200 else "Error: User V1 service unavailable"
    except:
        response += "Error: Could not reach User V1 service"
    response += "\n"
    try:
        res2 = requests.get("http://localhost:5001/", timeout=2)
        response += res2.text if res2.status_code == 200 else "Error: User V2 service unavailable"
    except:
        response += "Error: Could not reach User V2 service"
    response += "\n"
    try:
        res3 = requests.get("http://localhost:5002/", timeout=2)
        response += res3.text if res3.status_code == 200 else "Error: Order service unavailable"
    except:
        response += "Error: Could not reach Order service"
    response += "\n"
    return response

# User endpoints ----------------------------------
@app.route('/users', methods=['GET'])
def list_users():
    url = get_user_service_url()
    response = requests.get(f"{url}/users")
    return response.json() 

# To see user details by ID
@app.route('/user/<user_account_id>', methods=['GET'])
def see_user(user_account_id):
    url = get_user_service_url()
    response = requests.get(f"{url}/user/{user_account_id}")
    return response.json()

# To create a user
@app.route('/user', methods=['POST'])
def create_user():
    url = get_user_service_url()
    response = requests.post(f"{url}/user", json=request.get_json())
    return jsonify({"status": "User created "+ response.json().get("status")})

# To update a user email by ID
@app.route('/user/<user_id>/email', methods=['PUT'])
def update_user(user_id):
    url = get_user_service_url()
    response = requests.put(f"{url}/user/{user_id}/email", json=request.get_json())
    return response.json()

# To update a user address by ID
@app.route('/user/<user_id>/address', methods=['PUT'])
def update_user_address(user_id):
    url = get_user_service_url()
    response = requests.put(f"{url}/user/{user_id}/address", json=request.get_json())
    return response.json()

@app.route('/users/batch', methods=['POST'])
def batch_create_users():
    response = requests.post(USER_V2_URL, json=request.get_json())
    return jsonify({"status": "Batch users created "+ response.json().get("status")})

# Order endpoints ----------------------------------

#To list all orders
@app.route('/orders', methods=['GET'])
def list_orders():
    response = requests.get("http://localhost:5002/orders")
    return response.json()

#To see order details by order_id
@app.route('/order/<order_id>', methods=['GET'])
def see_order(order_id):
    response = requests.get(f"http://localhost:5002/order/{order_id}")
    return response.json()

# To create an order
@app.route('/order', methods=['POST'])
def create_order():
    response = requests.post("http://localhost:5002/order", json=request.get_json())
    return jsonify({"status": "Order created "+ response.json().get("status")})

# To update an order status
@app.route('/order/status/<order_id>', methods=['PUT'])
def update_order(order_id):
    response = requests.put(f"http://localhost:5002/order/{order_id}", json=request.get_json())
    return jsonify({"status": "Order updated "+ response.json().get("status")})

# To update a user email by ID
@app.route('/order/<order_id>/email', methods=['PUT'])
def update_order_email(order_id):
    response = requests.put(f"http://localhost:5002/order/{order_id}/email", json=request.get_json())
    return response.json()

# To update a user address by ID
@app.route('/order/<order_id>/address', methods=['PUT'])
def update_order_address(order_id):
    response = requests.put(f"http://localhost:5002/order/{order_id}/address", json=request.get_json())
    return response.json()

if __name__ == '__main__':
    print("API GATEWAY !!!!")
    app.run(host='0.0.0.0', port=8000, debug=True)