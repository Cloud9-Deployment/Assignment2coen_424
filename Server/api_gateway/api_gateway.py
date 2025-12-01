import requests
import random
import yaml
import json
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Service Ports:
# http://localhost:5000/ - User V1
# http://localhost:5001/ - User V2
# http://localhost:5002/ - Order service
# http://localhost:5003/ - Event service
# http://localhost:8000/ - API Gateway

# Fetch environment variables for service URLs
USER_V1_URL = os.getenv('USER_V1_URL', 'http://localhost:5000')
USER_V2_URL = os.getenv('USER_V2_URL', 'http://localhost:5001')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://242order-d9d5egcuauabdzab.eastus2-01.azurewebsites.net')
EVENT_SERVICE_URL = os.getenv('EVENT_SERVICE_URL', 'http://localhost:5003')

# Configuration file path
CONFIG_FILE = os.getenv('CONFIG_FILE', 'gateway_config.yaml')

def load_config():
    """Load configuration from YAML file"""
    default_config = {
        'strangler_pattern': {
            'enabled': True,
            'v1_percentage': 0,   # P percentage goes to V1
            'v2_percentage': 100  # (1-P) percentage goes to V2
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
            print(f"Config file not found, using defaults (V1: 0%, V2: 100%)")
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
    
    # Generate random number between 1-100
    random_value = random.randint(1, 100)
    
    if random_value <= v1_percentage:
        url = config['services'].get('user_v1', USER_V1_URL)
        print(f"[Strangler] Routing to User V1 (random: {random_value}, threshold: {v1_percentage}%)")
        return url
    else:
        url = config['services'].get('user_v2', USER_V2_URL)
        print(f"[Strangler] Routing to User V2 (random: {random_value}, threshold: {v1_percentage}%)")
        return url


# Gateway endpoints ----------------------------------

# Simple health check - FAST (doesn't check other services)
@app.route('/', methods=['GET'])
def hello_world():
    """Simple health check - returns immediately"""
    return "API Gateway is running!"

# Detailed status check (checks all services) - use /status instead
@app.route('/status', methods=['GET'])
def detailed_status():
    """Detailed status check - checks all services (may be slow)"""
    response = "\n=== API Gateway Status ===\n"
    response += f"Strangler Pattern: {'Enabled' if config['strangler_pattern']['enabled'] else 'Disabled'}\n"
    response += f"V1 Traffic: {config['strangler_pattern']['v1_percentage']}%\n"
    response += f"V2 Traffic: {config['strangler_pattern']['v2_percentage']}%\n"
    response += "\n=== Service Status ===\n"
    
    timeout = 2  # Short timeout for status checks
    
    try:
        res1 = requests.get(f"{config['services'].get('user_v1', USER_V1_URL)}/", timeout=timeout)
        response += f"User V1: {res1.text if res1.status_code == 200 else 'Error'}\n"
    except:
        response += "User V1: Unavailable\n"
    
    try:
        res2 = requests.get(f"{config['services'].get('user_v2', USER_V2_URL)}/", timeout=timeout)
        response += f"User V2: {res2.text if res2.status_code == 200 else 'Error'}\n"
    except:
        response += "User V2: Unavailable\n"
    
    try:
        res3 = requests.get(f"{config['services'].get('order', ORDER_SERVICE_URL)}/", timeout=timeout)
        response += f"Order Service: {res3.text if res3.status_code == 200 else 'Error'}\n"
    except:
        response += "Order Service: Unavailable\n"
    
    try:
        res4 = requests.get(f"{config['services'].get('event', EVENT_SERVICE_URL)}/", timeout=timeout)
        response += f"Event Service: {res4.text if res4.status_code == 200 else 'Error'}\n"
    except:
        response += "Event Service: Unavailable\n"
    
    return response

# Configuration endpoint
@app.route('/config', methods=['GET'])
def get_config():
    """Return current gateway configuration"""
    return jsonify({
        "strangler_pattern": config['strangler_pattern'],
        "services": config['services'],
        "timeout": config.get('timeout', 10)
    })

@app.route('/config/reload', methods=['POST'])
def reload_configuration():
    """Reload configuration from file"""
    new_config = reload_config()
    return jsonify({
        "status": "Configuration reloaded",
        "strangler_pattern": new_config['strangler_pattern']
    })

# User endpoints ----------------------------------

@app.route('/users', methods=['GET'])
def list_users():
    """List all users - routes through strangler pattern"""
    url = get_user_service_url()
    try:
        response = requests.get(f"{url}/users", timeout=config.get('timeout', 10))
        return response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/user/<user_account_id>', methods=['GET'])
def see_user(user_account_id):
    """Get user by ID - routes through strangler pattern"""
    url = get_user_service_url()
    try:
        response = requests.get(f"{url}/user/{user_account_id}", timeout=config.get('timeout', 10))
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/user', methods=['POST'])
def create_user():
    """Create a new user - routes through strangler pattern"""
    url = get_user_service_url()
    try:
        response = requests.post(f"{url}/user", json=request.get_json(), timeout=config.get('timeout', 10))
        return jsonify({"status": "User created", "details": response.json().get("status")})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/user/<user_id>/email', methods=['PUT'])
def update_user_email(user_id):
    """Update user email - routes through strangler pattern"""
    url = get_user_service_url()
    try:
        response = requests.put(f"{url}/user/{user_id}/email", json=request.get_json(), timeout=config.get('timeout', 10))
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/user/<user_id>/address', methods=['PUT'])
def update_user_address(user_id):
    """Update user address - routes through strangler pattern"""
    url = get_user_service_url()
    try:
        response = requests.put(f"{url}/user/{user_id}/address", json=request.get_json(), timeout=config.get('timeout', 10))
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/users/batch', methods=['POST'])
def batch_create_users():
    """Batch create users - V2 exclusive feature, always routes to V2"""
    try:
        # Batch operations are a V2-only feature
        response = requests.post(
            f"{config['services'].get('user_v2', USER_V2_URL)}/users/batch", 
            json=request.get_json(), 
            timeout=config.get('timeout', 10)
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

# Order endpoints ----------------------------------

@app.route('/orders', methods=['GET'])
def list_orders():
    """List all orders"""
    try:
        response = requests.get(
            f"{config['services'].get('order', ORDER_SERVICE_URL)}/orders", 
            timeout=config.get('timeout', 10)
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/orders/status/<status>', methods=['GET'])
def list_orders_by_status(status):
    """List orders by status"""
    try:
        response = requests.get(
            f"{config['services'].get('order', ORDER_SERVICE_URL)}/orders/status/{status}", 
            timeout=config.get('timeout', 10)
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/order/<order_id>', methods=['GET'])
def see_order(order_id):
    """Get order by ID"""
    try:
        response = requests.get(
            f"{config['services'].get('order', ORDER_SERVICE_URL)}/order/{order_id}", 
            timeout=config.get('timeout', 10)
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/order', methods=['POST'])
def create_order():
    """Create a new order"""
    try:
        response = requests.post(
            f"{config['services'].get('order', ORDER_SERVICE_URL)}/order", 
            json=request.get_json(), 
            timeout=config.get('timeout', 10)
        )
        return jsonify({"status": "Order created", "details": response.json()})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/order/status/<order_id>', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        response = requests.put(
            f"{config['services'].get('order', ORDER_SERVICE_URL)}/order/{order_id}", 
            json=request.get_json(), 
            timeout=config.get('timeout', 10)
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/order/<order_id>/email', methods=['PUT'])
def update_order_email(order_id):
    """Update order email"""
    try:
        response = requests.put(
            f"{config['services'].get('order', ORDER_SERVICE_URL)}/order/{order_id}/email", 
            json=request.get_json(), 
            timeout=config.get('timeout', 10)
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/order/<order_id>/address', methods=['PUT'])
def update_order_address(order_id):
    """Update order address"""
    try:
        response = requests.put(
            f"{config['services'].get('order', ORDER_SERVICE_URL)}/order/{order_id}/address", 
            json=request.get_json(), 
            timeout=config.get('timeout', 10)
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

# Event service endpoints ----------------------------------

@app.route('/events', methods=['GET'])
def list_events():
    """List all events from event service"""
    try:
        response = requests.get(
            f"{config['services'].get('event', EVENT_SERVICE_URL)}/events", 
            timeout=config.get('timeout', 10)
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/events/count', methods=['GET'])
def event_count():
    """Get event count from event service"""
    try:
        response = requests.get(
            f"{config['services'].get('event', EVENT_SERVICE_URL)}/events/count", 
            timeout=config.get('timeout', 10)
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

if __name__ == '__main__':
    print("=" * 50)
    print("API GATEWAY STARTING")
    print("=" * 50)
    print(f"Strangler Pattern: {'Enabled' if config['strangler_pattern']['enabled'] else 'Disabled'}")
    print(f"V1 Traffic: {config['strangler_pattern']['v1_percentage']}%")
    print(f"V2 Traffic: {config['strangler_pattern']['v2_percentage']}%")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8000, debug=True)