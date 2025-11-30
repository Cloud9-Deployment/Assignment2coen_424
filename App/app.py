import requests

# API Gateway URL
GATEWAY_URL = "http://localhost:8000"

def main():
    while True:
        print("\n" + "=" * 50)
        print("Welcome to the Microservices Test App!")
        print("=" * 50)
        print("\n--- User Operations ---")
        print("1. Check Gateway Status")
        print("2. List Users")
        print("3. Get User Details by ID")
        print("4. Create User")
        print("5. Update User Email or Address")
        print("6. Batch Create Users (V2 feature)")
        print("\n--- Order Operations ---")
        print("7. List Orders")
        print("8. List Orders by Status")
        print("9. Get Order Details by ID")
        print("10. Create Order")
        print("11. Update Order Status")
        print("12. Update Order Email or Address")
        print("\n--- Event Operations ---")
        print("13. View Events Log")
        print("14. View Event Statistics")
        print("\n--- Configuration ---")
        print("15. View Gateway Config")
        print("16. Reload Gateway Config")
        print("\n0. Exit")
        print("-" * 50)
        
        choice = input("Enter your choice: ").strip()

        try:
            # Choice 0: Exit
            if choice == '0':
                print("\nGoodbye!")
                break

            # Choice 1: Check Gateway Status
            elif choice == '1':
                response = requests.get(f"{GATEWAY_URL}/")
                print(response.text)

            # Choice 2: List Users
            elif choice == '2':
                print("\nListing all users...")
                response = requests.get(f"{GATEWAY_URL}/users")
                data = response.json()
                users = data.get("status")
                
                if isinstance(users, list):
                    for user in users:
                        print(f"\n  User ID: {user.get('user_account_id')}")
                        print(f"  Email: {user.get('email')}")
                        print(f"  Address: {user.get('delivery_address')}")
                else:
                    print(f"  {users}")

            # Choice 3: Get User Details by ID
            elif choice == '3':
                user_id = input("Enter User ID: ").strip()
                response = requests.get(f"{GATEWAY_URL}/user/{user_id}")
                data = response.json()
                print(f"\nResult: {data.get('status')}")

            # Choice 4: Create User
            elif choice == '4':
                email = input("Your email: ").strip()
                address = input("Your address: ").strip()
                
                user = {
                    "email": email,
                    "delivery_address": address
                }
                
                response = requests.post(f"{GATEWAY_URL}/user", json=user)
                print(f"\nResponse: {response.json()}")

            # Choice 5: Update User Email or Address
            elif choice == '5':
                user_id = input("User ID to update: ").strip()
                update_choice = input("Update (e)mail or (a)ddress? ").strip().lower()
                
                if update_choice == 'e':
                    email = input("New email: ").strip()
                    response = requests.put(
                        f"{GATEWAY_URL}/user/{user_id}/email", 
                        json={"email": email}
                    )
                    print(f"\nResponse: {response.json()}")
                    
                elif update_choice == 'a':
                    address = input("New address: ").strip()
                    response = requests.put(
                        f"{GATEWAY_URL}/user/{user_id}/address", 
                        json={"delivery_address": address}
                    )
                    print(f"\nResponse: {response.json()}")
                else:
                    print("Invalid choice.")

            # Choice 6: Batch Create Users
            elif choice == '6':
                num_users = int(input("Number of users to create: ").strip())
                users_list = []
                
                for i in range(num_users):
                    print(f"\n--- User {i+1} ---")
                    email = input("Email: ").strip()
                    address = input("Delivery Address: ").strip()
                    users_list.append({
                        "email": email,
                        "delivery_address": address
                    })
                
                response = requests.post(
                    f"{GATEWAY_URL}/users/batch", 
                    json={"users": users_list}
                )
                data = response.json()
                print(f"\nBatch Creation Result:")
                print(f"  Created: {data.get('total_created', 0)}")
                print(f"  Errors: {data.get('total_errors', 0)}")

            # Choice 7: List Orders
            elif choice == '7':
                print("\nListing all orders...")
                response = requests.get(f"{GATEWAY_URL}/orders")
                data = response.json()
                orders = data.get("status")
                
                if isinstance(orders, list):
                    for order in orders:
                        print(f"\n  Order ID: {order.get('order_id')}")
                        print(f"  User ID: {order.get('user_id')}")
                        print(f"  Items: {order.get('items')}")
                        print(f"  Email: {order.get('user_email')}")
                        print(f"  Address: {order.get('user_address')}")
                        print(f"  Status: {order.get('status')}")
                else:
                    print(f"  {orders}")

            # Choice 8: List Orders by Status
            elif choice == '8':
                print("Status options: under process, shipping, delivered")
                status = input("Enter status: ").strip()
                response = requests.get(f"{GATEWAY_URL}/orders/status/{status}")
                data = response.json()
                orders = data.get("status")
                
                if isinstance(orders, list):
                    for order in orders:
                        print(f"\n  Order ID: {order.get('order_id')}")
                        print(f"  User ID: {order.get('user_id')}")
                        print(f"  Status: {order.get('status')}")
                else:
                    print(f"  {orders}")

            # Choice 9: Get Order Details by ID
            elif choice == '9':
                order_id = input("Enter Order ID: ").strip()
                response = requests.get(f"{GATEWAY_URL}/order/{order_id}")
                data = response.json()
                order = data.get("status")
                
                if isinstance(order, dict):
                    print(f"\n  Order ID: {order.get('order_id')}")
                    print(f"  User ID: {order.get('user_id')}")
                    print(f"  Items: {order.get('items')}")
                    print(f"  Email: {order.get('user_email')}")
                    print(f"  Address: {order.get('user_address')}")
                    print(f"  Status: {order.get('status')}")
                else:
                    print(f"  {order}")

            # Choice 10: Create Order
            elif choice == '10':
                user_id = input("User ID: ").strip()
                email = input("Email (or press Enter to skip): ").strip() or "N/A"
                address = input("Delivery Address (or press Enter to skip): ").strip() or "N/A"
                
                items = []
                while True:
                    item = input("Item name (or press Enter to finish): ").strip()
                    if not item:
                        break
                    quantity = input(f"Quantity for {item}: ").strip()
                    items.append({"item": item, "quantity": int(quantity)})
                
                if not items:
                    items = [{"item": "Default Item", "quantity": 1}]
                
                order = {
                    "user_id": user_id,
                    "items": items,
                    "email": email,
                    "delivery_address": address
                }
                
                response = requests.post(f"{GATEWAY_URL}/order", json=order)
                print(f"\nResponse: {response.json()}")

            # Choice 11: Update Order Status
            elif choice == '11':
                order_id = input("Order ID to update: ").strip()
                print("Status options: under process, shipping, delivered")
                status = input("New status: ").strip()
                
                response = requests.put(
                    f"{GATEWAY_URL}/order/status/{order_id}", 
                    json={"status": status}
                )
                print(f"\nResponse: {response.json()}")

            # Choice 12: Update Order Email or Address
            elif choice == '12':
                order_id = input("Order ID to update: ").strip()
                update_choice = input("Update (e)mail or (a)ddress? ").strip().lower()
                
                if update_choice == 'e':
                    email = input("New email: ").strip()
                    response = requests.put(
                        f"{GATEWAY_URL}/order/{order_id}/email", 
                        json={"email": email}
                    )
                    print(f"\nResponse: {response.json()}")
                    
                elif update_choice == 'a':
                    address = input("New address: ").strip()
                    response = requests.put(
                        f"{GATEWAY_URL}/order/{order_id}/address", 
                        json={"delivery_address": address}
                    )
                    print(f"\nResponse: {response.json()}")
                else:
                    print("Invalid choice.")

            # Choice 13: View Events Log
            elif choice == '13':
                response = requests.get(f"{GATEWAY_URL}/events")
                data = response.json()
                
                if data.get("total_events", 0) == 0:
                    print("\nNo events logged.")
                else:
                    print(f"\nTotal Events: {data.get('total_events')}")
                    for event in data.get("events", []):
                        print(f"\n  Time: {event.get('timestamp')}")
                        print(f"  Type: {event.get('event_type')}")
                        print(f"  Source: {event.get('source')}")
                        print(f"  Data: {event.get('data')}")

            # Choice 14: View Event Statistics
            elif choice == '14':
                response = requests.get(f"{GATEWAY_URL}/events/count")
                data = response.json()
                print(f"\nTotal Events: {data.get('total_events')}")

            # Choice 15: View Gateway Config
            elif choice == '15':
                response = requests.get(f"{GATEWAY_URL}/config")
                data = response.json()
                print("\nGateway Configuration:")
                print(f"  Strangler Pattern Enabled: {data['strangler_pattern']['enabled']}")
                print(f"  V1 Traffic: {data['strangler_pattern']['v1_percentage']}%")
                print(f"  V2 Traffic: {data['strangler_pattern']['v2_percentage']}%")

            # Choice 16: Reload Gateway Config
            elif choice == '16':
                response = requests.post(f"{GATEWAY_URL}/config/reload")
                print(f"\nResponse: {response.json()}")

            else:
                print("\nInvalid choice. Please try again.")

        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Could not connect to the API Gateway.")
            print("   Make sure all services are running.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()