#!/usr/bin/env python3
"""
Automated Step-by-Step Test Script for Microservices
COEN 424 Assignment 2

This script tests all functionality step by step, waiting for user confirmation
between each test to allow observation of the results.

Prerequisites:
- All services must be running (user_V1, user_V2, order, event, api_gateway)
- RabbitMQ must be running
- MongoDB must be accessible
"""

import requests
import json
import time
import sys

# Configuration
GATEWAY_URL = "http://localhost:8000"
USER_V1_URL = "http://localhost:5000"
USER_V2_URL = "http://localhost:5001"
ORDER_URL = "http://localhost:5002"
EVENT_URL = "http://localhost:5003"
# Test data storage
created_user_id = None
created_order_id = None

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_step(step_num, description):
    print(f"{Colors.CYAN}{Colors.BOLD}[STEP {step_num}]{Colors.END} {Colors.CYAN}{description}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def print_request(method, url, data=None):
    print(f"{Colors.BLUE}→ {method} {url}{Colors.END}")
    if data:
        print(f"{Colors.BLUE}  Body: {json.dumps(data, indent=2)}{Colors.END}")

def print_response(response):
    try:
        data = response.json()
        print(f"{Colors.GREEN}← Response ({response.status_code}):{Colors.END}")
        print(f"{Colors.GREEN}{json.dumps(data, indent=2)}{Colors.END}")
    except:
        print(f"{Colors.GREEN}← Response ({response.status_code}): {response.text}{Colors.END}")

def wait_for_user():
    """Wait for user to press Enter to continue"""
    input(f"\n{Colors.YELLOW}Press Enter to continue to next step...{Colors.END}\n")

def check_services():
    """Check if all services are running"""
    print_header("CHECKING SERVICES")
    
    services = [
        ("API Gateway", GATEWAY_URL),
        ("User V1", USER_V1_URL),
        ("User V2", USER_V2_URL),
        ("Order Service", ORDER_URL),
        ("Event Service", EVENT_URL),
    ]
    
    all_running = True
    for name, url in services:
        try:
            response = requests.get(f"{url}/", timeout=3)
            if response.status_code == 200:
                print_success(f"{name} is running at {url}")
            else:
                print_error(f"{name} returned status {response.status_code}")
                all_running = False
        except requests.exceptions.ConnectionError:
            print_error(f"{name} is NOT running at {url}")
            all_running = False
        except Exception as e:
            print_error(f"{name} error: {str(e)}")
            all_running = False
    
    return all_running


def test_gateway_status():
    """Test 1: Check gateway status and configuration"""
    print_header("TEST 1: GATEWAY STATUS & CONFIGURATION")
    
    print_step(1.1, "Getting gateway health check")
    print_request("GET", f"{GATEWAY_URL}/")
    response = requests.get(f"{GATEWAY_URL}/")
    print_response(response)
    
    wait_for_user()
    
    print_step(1.2, "Getting detailed service status (may take a moment)")
    print_request("GET", f"{GATEWAY_URL}/status")
    response = requests.get(f"{GATEWAY_URL}/status", timeout=15)
    print_response(response)
    
    wait_for_user()
    
    print_step(1.3, "Getting gateway configuration (Strangler Pattern)")
    print_request("GET", f"{GATEWAY_URL}/config")
    response = requests.get(f"{GATEWAY_URL}/config")
    print_response(response)
    
    config = response.json()
    v1_pct = config['strangler_pattern']['v1_percentage']
    v2_pct = config['strangler_pattern']['v2_percentage']
    print_info(f"Current routing: {v1_pct}% to V1, {v2_pct}% to V2")


def test_user_creation():
    """Test 2: Create users through gateway"""
    global created_user_id
    
    print_header("TEST 2: USER CREATION")
    
    print_step(2.1, "Creating a new user through API Gateway")
    user_data = {
        "email": "testuser@example.com",
        "delivery_address": "123 Test Street, Montreal, QC"
    }
    print_request("POST", f"{GATEWAY_URL}/user", user_data)
    response = requests.post(f"{GATEWAY_URL}/user", json=user_data)
    print_response(response)
    print_info("Note: Check which version (V1 or V2) handled this request in the service logs!")
    
    wait_for_user()
    
    print_step(2.2, "Listing all users to find the created user")
    print_request("GET", f"{GATEWAY_URL}/users")
    response = requests.get(f"{GATEWAY_URL}/users")
    print_response(response)
    
    # Try to extract user ID
    try:
        data = response.json()
        users = data.get("status", [])
        if isinstance(users, list) and users:
            created_user_id = users[-1].get("user_account_id")
            print_success(f"Found user with ID: {created_user_id}")
    except:
        created_user_id = 1
        print_info(f"Assuming user ID: {created_user_id}")


def test_get_user():
    """Test 3: Get user details"""
    print_header("TEST 3: GET USER DETAILS")
    
    user_id = created_user_id or 1
    
    print_step(3.1, f"Getting details for user ID: {user_id}")
    print_request("GET", f"{GATEWAY_URL}/user/{user_id}")
    response = requests.get(f"{GATEWAY_URL}/user/{user_id}")
    print_response(response)


def test_order_creation():
    """Test 4: Create an order"""
    global created_order_id
    
    print_header("TEST 4: ORDER CREATION")
    
    user_id = created_user_id or 1
    
    print_step(4.1, f"Creating an order for user ID: {user_id}")
    order_data = {
        "user_id": str(user_id),
        "items": [
            {"item": "Laptop", "quantity": 1},
            {"item": "Mouse", "quantity": 2}
        ],
        "email": "testuser@example.com",
        "delivery_address": "123 Test Street, Montreal, QC"
    }
    print_request("POST", f"{GATEWAY_URL}/order", order_data)
    response = requests.post(f"{GATEWAY_URL}/order", json=order_data)
    print_response(response)
    
    wait_for_user()
    
    print_step(4.2, "Listing all orders")
    print_request("GET", f"{GATEWAY_URL}/orders")
    response = requests.get(f"{GATEWAY_URL}/orders")
    print_response(response)
    
    # Try to extract order ID
    try:
        data = response.json()
        orders = data.get("status", [])
        if isinstance(orders, list) and orders:
            created_order_id = orders[-1].get("order_id")
            print_success(f"Found order with ID: {created_order_id}")
    except:
        created_order_id = 1
        print_info(f"Assuming order ID: {created_order_id}")


def test_order_status_update():
    """Test 5: Update order status"""
    print_header("TEST 5: ORDER STATUS UPDATE")
    
    order_id = created_order_id or 1
    
    statuses = ["under process", "shipping", "delivered"]
    
    for i, status in enumerate(statuses):
        print_step(f"5.{i+1}", f"Updating order {order_id} status to: '{status}'")
        update_data = {"status": status}
        print_request("PUT", f"{GATEWAY_URL}/order/status/{order_id}", update_data)
        response = requests.put(f"{GATEWAY_URL}/order/status/{order_id}", json=update_data)
        print_response(response)
        
        if i < len(statuses) - 1:
            wait_for_user()
    
    wait_for_user()
    
    print_step(5.4, "Verifying order status change")
    print_request("GET", f"{GATEWAY_URL}/order/{order_id}")
    response = requests.get(f"{GATEWAY_URL}/order/{order_id}")
    print_response(response)


def test_data_synchronization():
    """Test 6: Data synchronization between User and Order services"""
    print_header("TEST 6: DATA SYNCHRONIZATION (KEY FEATURE)")
    
    user_id = created_user_id or 1
    order_id = created_order_id or 1
    
    print_info("This test verifies that when a user updates their email/address,")
    print_info("the change is automatically synchronized to all their orders via RabbitMQ events.")
    
    wait_for_user()
    
    # First, show current order state
    print_step(6.1, f"Current state of order {order_id} (BEFORE update)")
    print_request("GET", f"{GATEWAY_URL}/order/{order_id}")
    response = requests.get(f"{GATEWAY_URL}/order/{order_id}")
    print_response(response)
    
    wait_for_user()
    
    # Update user email
    print_step(6.2, f"Updating email for user {user_id}")
    new_email = "newemail_synchronized@example.com"
    update_data = {"email": new_email}
    print_request("PUT", f"{GATEWAY_URL}/user/{user_id}/email", update_data)
    response = requests.put(f"{GATEWAY_URL}/user/{user_id}/email", json=update_data)
    print_response(response)
    
    print_info("Event published to RabbitMQ: user.email_updated")
    print_info("Waiting 2 seconds for synchronization...")
    time.sleep(2)
    
    wait_for_user()
    
    # Check if order was updated
    print_step(6.3, f"Checking order {order_id} (AFTER email update)")
    print_request("GET", f"{GATEWAY_URL}/order/{order_id}")
    response = requests.get(f"{GATEWAY_URL}/order/{order_id}")
    print_response(response)
    
    try:
        order = response.json().get("status", {})
        if isinstance(order, dict) and order.get("user_email") == new_email:
            print_success("EMAIL SYNCHRONIZATION SUCCESSFUL!")
        else:
            print_info("Check if email was synchronized in the response above")
    except:
        pass
    
    wait_for_user()
    
    # Update user address
    print_step(6.4, f"Updating address for user {user_id}")
    new_address = "456 New Synchronized Address, Toronto, ON"
    update_data = {"delivery_address": new_address}
    print_request("PUT", f"{GATEWAY_URL}/user/{user_id}/address", update_data)
    response = requests.put(f"{GATEWAY_URL}/user/{user_id}/address", json=update_data)
    print_response(response)
    
    print_info("Event published to RabbitMQ: user.address_updated")
    print_info("Waiting 2 seconds for synchronization...")
    time.sleep(2)
    
    wait_for_user()
    
    # Check if order was updated
    print_step(6.5, f"Checking order {order_id} (AFTER address update)")
    print_request("GET", f"{GATEWAY_URL}/order/{order_id}")
    response = requests.get(f"{GATEWAY_URL}/order/{order_id}")
    print_response(response)
    
    try:
        order = response.json().get("status", {})
        if isinstance(order, dict) and order.get("user_address") == new_address:
            print_success("ADDRESS SYNCHRONIZATION SUCCESSFUL!")
        else:
            print_info("Check if address was synchronized in the response above")
    except:
        pass


def test_event_logging():
    """Test 7: Check event service logs"""
    print_header("TEST 7: EVENT SERVICE LOGS")
    
    print_step(7.1, "Getting all logged events")
    print_request("GET", f"{GATEWAY_URL}/events")
    response = requests.get(f"{GATEWAY_URL}/events")
    print_response(response)
    
    print_info("These events were captured from RabbitMQ by the Event Service")
    
    wait_for_user()
    
    print_step(7.2, "Getting event statistics")
    print_request("GET", f"{EVENT_URL}/events/stats")
    response = requests.get(f"{EVENT_URL}/events/stats")
    print_response(response)


def test_strangler_pattern():
    """Test 8: Test strangler pattern routing"""
    print_header("TEST 8: STRANGLER PATTERN ROUTING")
    
    print_info("The strangler pattern routes P% of requests to V1 and (100-P)% to V2")
    print_info("We'll make multiple requests and observe which service handles them")
    print_info("Check the USER SERVICE CONSOLE LOGS to see which version handles each request!")
    
    wait_for_user()
    
    print_step(8.1, "Making 10 requests to observe routing distribution")
    
    v1_count = 0
    v2_count = 0
    
    for i in range(10):
        print(f"\n  Request {i+1}/10...")
        response = requests.get(f"{GATEWAY_URL}/users")
        # The actual routing is logged in the gateway console
        print(f"  Response received (check gateway logs for routing info)")
        time.sleep(0.5)
    
    print_info("\nCheck the API Gateway console output to see the routing distribution!")
    print_info("You should see messages like:")
    print_info("  [Strangler] Routing to User V1 (random: X, threshold: Y%)")
    print_info("  [Strangler] Routing to User V2 (random: X, threshold: Y%)")


def test_batch_operations():
    """Test 9: Test V2-exclusive batch operations"""
    print_header("TEST 9: BATCH OPERATIONS (V2 EXCLUSIVE)")
    
    print_info("Batch user creation is a V2-only feature")
    print_info("This request will ALWAYS go to V2 regardless of strangler pattern config")
    
    wait_for_user()
    
    print_step(9.1, "Creating multiple users in batch")
    batch_data = {
        "users": [
            {"email": "batch1@example.com", "delivery_address": "Batch Address 1"},
            {"email": "batch2@example.com", "delivery_address": "Batch Address 2"},
            {"email": "batch3@example.com", "delivery_address": "Batch Address 3"}
        ]
    }
    print_request("POST", f"{GATEWAY_URL}/users/batch", batch_data)
    response = requests.post(f"{GATEWAY_URL}/users/batch", json=batch_data)
    print_response(response)
    
    wait_for_user()
    
    print_step(9.2, "Listing all users after batch creation")
    print_request("GET", f"{GATEWAY_URL}/users")
    response = requests.get(f"{GATEWAY_URL}/users")
    print_response(response)


def test_orders_by_status():
    """Test 10: Get orders by status"""
    print_header("TEST 10: FILTER ORDERS BY STATUS")
    
    statuses = ["under process", "shipping", "delivered"]
    
    for i, status in enumerate(statuses):
        print_step(f"10.{i+1}", f"Getting orders with status: '{status}'")
        print_request("GET", f"{GATEWAY_URL}/orders/status/{status}")
        response = requests.get(f"{GATEWAY_URL}/orders/status/{status}")
        print_response(response)
        
        if i < len(statuses) - 1:
            wait_for_user()


def run_all_tests():
    """Run all tests in sequence"""
    print_header("MICROSERVICES AUTOMATED TEST SUITE")
    print(f"{Colors.BOLD}COEN 424 - Assignment 2{Colors.END}")
    print(f"\nThis script will test all microservice functionality step by step.")
    print("You will be prompted to press Enter between each step.")
    print("\nMake sure all services are running:")
    print("  - RabbitMQ (localhost:5672)")
    print("  - User V1 (localhost:5000)")
    print("  - User V2 (localhost:5001)")
    print("  - Order Service (localhost:5002)")
    print("  - Event Service (localhost:5003)")
    print("  - API Gateway (localhost:8000)")
    
    wait_for_user()
    
    # Check services first
    if not check_services():
        print_error("\nSome services are not running. Please start all services and try again.")
        print_info("\nTo start services locally, run in separate terminals:")
        print("  Terminal 1: python user_V1.py")
        print("  Terminal 2: python user_V2.py")
        print("  Terminal 3: python order.py")
        print("  Terminal 4: python event.py")
        print("  Terminal 5: python api_gateway.py")
        return
    
    wait_for_user()
    
    try:
        # Run all tests
        test_gateway_status()
        wait_for_user()
        
        test_user_creation()
        wait_for_user()
        
        test_get_user()
        wait_for_user()
        
        test_order_creation()
        wait_for_user()
        
        test_order_status_update()
        wait_for_user()
        
        test_data_synchronization()
        wait_for_user()
        
        test_event_logging()
        wait_for_user()
        
        test_strangler_pattern()
        wait_for_user()
        
        test_batch_operations()
        wait_for_user()
        
        test_orders_by_status()
        
        # Summary
        print_header("TEST SUITE COMPLETED")
        print_success("All tests have been executed!")
        print(f"\n{Colors.BOLD}Summary of tests performed:{Colors.END}")
        print("  1. Gateway health check and configuration")
        print("  2. User creation through API Gateway")
        print("  3. Get user details")
        print("  4. Order creation")
        print("  5. Order status updates")
        print("  6. Data synchronization (User → Order via RabbitMQ)")
        print("  7. Event service logging")
        print("  8. Strangler pattern routing")
        print("  9. Batch operations (V2 exclusive)")
        print("  10. Filter orders by status")
        
        print(f"\n{Colors.BOLD}Key features demonstrated:{Colors.END}")
        print("  ✓ API Gateway routing")
        print("  ✓ Strangler Pattern (V1/V2 traffic splitting)")
        print("  ✓ Event-driven data synchronization")
        print("  ✓ RabbitMQ message passing")
        print("  ✓ MongoDB data persistence")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user.{Colors.END}")
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")


def run_quick_test():
    """Run a quick automated test without waiting for user input"""
    print_header("QUICK AUTOMATED TEST")
    
    if not check_services():
        print_error("Services not running!")
        return False
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Create user
    print("\n[1/6] Creating user...")
    try:
        response = requests.post(f"{GATEWAY_URL}/user", json={
            "email": "quicktest@example.com",
            "delivery_address": "Quick Test Address"
        })
        if response.status_code == 200:
            print_success("User created")
            tests_passed += 1
        else:
            print_error("User creation failed")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 2: List users
    print("\n[2/6] Listing users...")
    try:
        response = requests.get(f"{GATEWAY_URL}/users")
        if response.status_code == 200:
            print_success("Users listed")
            tests_passed += 1
        else:
            print_error("Failed to list users")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 3: Create order
    print("\n[3/6] Creating order...")
    try:
        response = requests.post(f"{GATEWAY_URL}/order", json={
            "user_id": "1",
            "items": [{"item": "Test Item", "quantity": 1}],
            "email": "quicktest@example.com",
            "delivery_address": "Quick Test Address"
        })
        if response.status_code == 200:
            print_success("Order created")
            tests_passed += 1
        else:
            print_error("Order creation failed")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 4: Update user email (triggers sync)
    print("\n[4/6] Updating user email (testing sync)...")
    try:
        response = requests.put(f"{GATEWAY_URL}/user/1/email", json={
            "email": "synced@example.com"
        })
        if response.status_code == 200:
            print_success("Email updated")
            tests_passed += 1
        else:
            print_error("Email update failed")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    time.sleep(2)  # Wait for sync
    
    # Test 5: Check events
    print("\n[5/6] Checking events...")
    try:
        response = requests.get(f"{GATEWAY_URL}/events")
        if response.status_code == 200:
            print_success("Events retrieved")
            tests_passed += 1
        else:
            print_error("Failed to get events")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 6: Batch create (V2 feature)
    print("\n[6/6] Testing batch creation (V2)...")
    try:
        response = requests.post(f"{GATEWAY_URL}/users/batch", json={
            "users": [
                {"email": "batch_quick1@example.com", "delivery_address": "Addr 1"},
                {"email": "batch_quick2@example.com", "delivery_address": "Addr 2"}
            ]
        })
        if response.status_code == 200:
            print_success("Batch creation successful")
            tests_passed += 1
        else:
            print_error("Batch creation failed")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Summary
    print_header("QUICK TEST RESULTS")
    print(f"Passed: {tests_passed}/6")
    print(f"Failed: {tests_failed}/6")
    
    return tests_failed == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_test()
    else:
        run_all_tests()