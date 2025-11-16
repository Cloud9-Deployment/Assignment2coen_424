import requests
from flask import Flask, request, jsonify
app = Flask(__name__)

# http://localhost:5000/ is the user V1
# http://localhost:5001/ is the user V2
# http://localhost:5002/ is the order service
# http://localhost:8000/ is the api gateway

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

# To create a user
@app.route('/user', methods=['POST'])
def create_user():
    response = requests.post("http://localhost:5000/user", json=request.get_json())

    return jsonify({"status": "User created "+ response.json().get("status")})

# To update a user
@app.route('/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    response = requests.put(f"http://localhost:5000/user/{user_id}", json=request.get_json())

    return jsonify({"status": "User updated "+ response.json().get("status")})

# Order endpoints ----------------------------------

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

# To update an email or address
@app.route('/user/contact/<user_id>', methods=['PUT'])
def update_user_contact(user_id):
    response = requests.put(f"http://localhost:5002/user/contact/{user_id}", json=request.get_json())

    return jsonify({"status": "User contact updated "+ response.json().get("status")})


if __name__ == '__main__':
    print("API GATEWAY !!!!")
    app.run(host='0.0.0.0', port=8000, debug=True)