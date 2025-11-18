import requests

# Define the JSON schema for user data
user_schema = {
  "type": "object",
  "properties": {
    "email": {"type": "string"},
    "delivery_address": {"type": "string"}
  },
  "required": ["email", "delivery_address"]
}

def main():
    print("Welcome to the App!")
    print("Choose an option:")
    print("1. Say Hello")
    print("2. List Users")
    print("3. Get User Details by ID")
    print("4. Create User")
    print("5. Update User email or address")
    print("6. List Orders")
    print("7. Get Order Details by ID")
    print("8. Create Order")
    print("9. Update Order status")
    print("10. Update Order email or address")
    choice = input("Enter your choice: ")

    # Handle user choices       ------------------------------------

    # Choice 1: Say Hello
    if choice == '1':
        response = requests.get("http://localhost:8000/")
        print(response.text)

    # Choice 2: List Users
    elif choice == '2':
        print("Listing all users...")
        response = requests.get("http://localhost:8000/users")
        data = response.json()
        
        # Extract the users from the response
        users = data.get("status")
        
        if not users:
            print("No users found.")
        else:
            if isinstance(users, list):
                for user in users:
                    print(f"\nUser ID: {user.get('user_account_id')}, \nEmail: {user.get('email')}, \nAddress: {user.get('delivery_address')} \n")
            else:
                print(users)  # If it's a string message

    # Choice 3: Get User Details by ID
    elif choice == '3':
        print("Enter User ID:")
        user_id = input()

        response = requests.get(f"http://localhost:8000/user/{user_id}")
        data = response.json()
       # Extract the users from the response
        users = data.get("status")
        
        if not users:
            print("No users found.")
        else:
            if isinstance(users, list):
                for user in users:
                    print(f"\nUser ID: {user.get('user_account_id')}, \nEmail: {user.get('email')}, \nAddress: {user.get('delivery_address')} \n")
            else:
                print(users)  # If it's a string message
        
    # Choice 4: Create User
    elif choice == '4':
        print("Your email:")
        email = input()
        print("Your address:")
        address = input()

        user = {
            "email": email,
            "delivery_address": address
        }

        response = requests.post("http://localhost:8000/user", json=user)
        print("Response from API Gateway:", response.json().get("status"))

    # Choice 5: Update User email and address
    elif choice == '5':
        print("User ID to update:")
        user_account_id = input()

        print("Update email or address? (e/a):")
        update_choice = input().lower()

        # Handle email
        if update_choice == 'e':
            print("New email:")
            email = input()
            user = {
                "email": email
            }
            
            response = requests.put(f"http://localhost:8000/user/{user_account_id}/email", json=user)
            data = response.json()
            users = data.get("status")
            
            if not users:
                print("No users found.")
            else:
                if isinstance(users, list):
                    for user in users:
                        print(f"\nUser ID: {user.get('user_account_id')}, \nEmail: {user.get('email')}, \nAddress: {user.get('delivery_address')} \n")
                else:
                    print(users)  # If it's a string message

        # Handle address
        elif update_choice == 'a':
            print("New address:")
            address = input()
            user = {
                "delivery_address": address
            }
            
            response = requests.put(f"http://localhost:8000/user/{user_account_id}/address", json=user)
            print("Response from API Gateway:", response.json().get("status"))
        
        else:
            print("Invalid choice.")
            return
        
    # Choice 6: List Orders
    elif choice == '6':
        print("Listing all orders...")
        response = requests.get("http://localhost:8000/orders")
        data = response.json()
        orders = data.get("status")
        
        if not orders:
            print("No orders found.")
        else:
            if isinstance(orders, list):
                for order in orders:
                    print(f"\nOrder ID: {order.get('order_id')}, \nUser ID: {order.get('user_id')}, \nItem: {order.get('item')}, \nQuantity: {order.get('quantity')}, \nStatus: {order.get('status')} \n")
            else:
                print(orders)  # If it's a string message

    # Choice 7: Get Order Details by ID
    elif choice == '7':
        print("Enter Order ID:")
        order_id = input()

        response = requests.get(f"http://localhost:8000/order/{order_id}")
        data = response.json()
        orders = data.get("status")
        
        if not orders:
            print("No orders found.")
        else:
            if isinstance(orders, list):
                for order in orders:
                    print(f"\nOrder ID: {order.get('order_id')}, \nUser ID: {order.get('user_id')}, \nItem: {order.get('item')}, \nQuantity: {order.get('quantity')}, \nStatus: {order.get('status')} \n")
            else:
                print(orders)  # If it's a string message

    # Choice 8: Create Order
    elif choice == '8':
        print("User ID:")
        user_id = input()
        print("Item:")
        item = input()
        print("Quantity:")
        quantity = input()

        order = {
            "user_id": user_id,
            "item": item,
            "quantity": quantity
        }

        response = requests.post("http://localhost:8000/order", json=order)
        print("Response from API Gateway:", response.json().get("status"))

    # Choice 9: Update Order status
    elif choice == '9':
        print("Order ID to update:")
        order_id = input()

        print("New status:")
        status = input()
        order = {
            "status": status
        }
        
        response = requests.put(f"http://localhost:8000/order/status/{order_id}", json=order)
        print("Response from API Gateway:", response.json().get("status"))

    # Choice 10: Update Order email or address
    elif choice == '10':
        print("Order ID to update:")
        order_id = input()

        print("Update email or address? (e/a):")
        update_choice = input().lower()

        # Handle email
        if update_choice == 'e':
            print("New email:")
            email = input()
            order = {
                "email": email
            }
            
            response = requests.put(f"http://localhost:8000/order/{order_id}/email", json=order)
            data = response.json()
            users = data.get("status")
            
            if not users:
                print("No users found.")
            else:
                if isinstance(users, list):
                    for user in users:
                        print(f"\nUser ID: {user.get('user_account_id')}, \nEmail: {user.get('email')}, \nAddress: {user.get('delivery_address')} \n")
                else:
                    print(users)  # If it's a string message

        # Handle address
        elif update_choice == 'a':
            print("New address:")
            address = input()
            order = {
                "delivery_address": address
            }
            
            response = requests.put(f"http://localhost:8000/order/{order_id}/address", json=order)
            print("Response from API Gateway:", response.json().get("status"))

        else:
            print("\nInvalid choice.\n")
            main()
        
    else:
        print("\nInvalid choice.\n")
        main()
        

    main()

if __name__ == "__main__":
    main()
