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
    print("2. Create User")
    print("3. Update User email and address")
    choice = input("Enter your choice: ")

    if choice == '1':
        response = requests.get("http://localhost:8000/")
        print(response.text)

    elif choice == '2':
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

    elif choice == '3':
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
