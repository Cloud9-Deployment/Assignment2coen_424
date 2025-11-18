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
    print("5. Update User email and address")
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
        user_id = input()
        print("New email:")
        email = input()
        print("New address:")
        address = input()

        user = {
            "email": email,
            "delivery_address": address
        }

        response = requests.put(f"http://localhost:8000/user/{user_id}", json=user)
        print("Response from API Gateway:", response.json().get("status"))



    main()

if __name__ == "__main__":
    main()
