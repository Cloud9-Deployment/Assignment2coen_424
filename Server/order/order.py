from flask import Flask, request, jsonify
app = Flask(__name__)

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
    app.run(host='0.0.0.0', port=5002, debug=True)