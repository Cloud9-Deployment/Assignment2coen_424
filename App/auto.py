#!/usr/bin/env python3
"""
Automated Step-by-Step Test Script for Microservices
COEN 424 Assignment 2

This script tests all functionality through the API Gateway only.
Internal services (user-v1, user-v2, order, event) are not directly accessible
from outside Azure Container Apps - all requests go through the API Gateway.

Prerequisites:
- API Gateway must be deployed and accessible
- All internal services must be running in Azure Container Apps
"""

import requests
import json
import time
import sys

# Configuration - Only the API Gateway is externally accessible
GATEWAY_URL = "https://api-gateway.whitetree-8d660c42.westus2.azurecontainerapps.io"

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

def check_gateway():
    """Check if the API Gateway is accessible"""
    print_header("CHECKING API GATEWAY")
    
    try:
        print_info(f"Testing connection to: {GATEWAY_URL}")
        response = requests.get(f"{GATEWAY_URL}/", timeout=10)
        if response.status_code == 200:
            print_success(f"API Gateway is running!")
            print_response(response)
            return True
        else:
            print_error(f"API Gateway returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError as e:
        print_error(f"Cannot connect to API Gateway: {e}")
        return False
    except requests.exceptions.Timeout:
        print_error("Connection timed out")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_gateway_status():
    """Test 1: Check gateway status and configuration"""
    print_header("TEST 1: GATEWAY STATUS & CONFIGURATION")
    
    print_step(1.1, "Getting gateway health check")
    print_request("GET", f"{GATEWAY_URL}/")
    response = requests.get(f"{GATEWAY_URL}/", timeout=10)
    print_response(response)
    
    wait_for_user()
    
    print_step(1.2, "Getting detailed service status")
    print_info("This checks connectivity to all internal services...")
    print_request("GET", f"{GATEWAY_URL}/status")
    try:
        response = requests.get(f"{GATEWAY_URL}/status", timeout=30)
        print_response(response)
        
        # Check if services are available
        if "Unavailable" in response.text:
            print_error("Some internal services are unavailable!")
            print_info("Check Azure Container Apps logs for errors.")
        else:
            print_success("All internal services are responding!")
    except requests.exceptions.Timeout:
        print_error("Status check timed out - services may be slow or unavailable")
    
    wait_for_user()
    
    print_step(1.3, "Getting gateway configuration (Strangler Pattern)")
    print_request("GET", f"{GATEWAY_URL}/config")
    response = requests.get(f"{GATEWAY_URL}/config", timeout=10)
    print_response(response)
    
    try:
        config = response.json()
        v1_pct = config['strangler_pattern']['v1_percentage']
        v2_pct = config['strangler_pattern']['v2_percentage']
        print_info(f"Current routing: {v1_pct}% to V1, {v2_pct}% to V2")
        print_info(f"User V1 URL: {config['services'].get('user_v1', 'N/A')}")
        print_info(f"User V2 URL: {config['services'].get('user_v2', 'N/A')}")
        print_info(f"Order URL: {config['services'].get('order', 'N/A')}")
        print_info(f"Event URL: {config['services'].get('event', 'N/A')}")
    except Exception as e:
        print_error(f"Could not parse config: {e}")


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
    response = requests.post(f"{GATEWAY_URL}/user", json=user_data, timeout=15)
    print_response(response)
    
    if response.status_code == 200:
        print_success("User created successfully!")
        print_info("Based on strangler pattern config, this went to V1 or V2")
    else:
        print_error(f"User creation failed with status {response.status_code}")
    
    wait_for_user()
    
    print_step(2.2, "Listing all users to find the created user")
    print_request("GET", f"{GATEWAY_URL}/users")
    response = requests.get(f"{GATEWAY_URL}/users", timeout=15)
    print_response(response)
    
    # Try to extract user ID
    try:
        data = response.json()
        users = data.get("status", [])
        if isinstance(users, list) and users:
            created_user_id = users[-1].get("user_account_id")
            print_success(f"Found user with ID: {created_user_id}")
        elif isinstance(users, str):
            print_info("No users found or unexpected response format")
            created_user_id = 1
    except Exception as e:
        created_user_id = 1
        print_info(f"Assuming user ID: {created_user_id}")


def test_get_user():
    """Test 3: Get user details"""
    print_header("TEST 3: GET USER DETAILS")
    
    user_id = created_user_id or 1
    
    print_step(3.1, f"Getting details for user ID: {user_id}")
    print_request("GET", f"{GATEWAY_URL}/user/{user_id}")
    response = requests.get(f"{GATEWAY_URL}/user/{user_id}", timeout=15)
    print_response(response)
    
    if response.status_code == 200:
        print_success("User details retrieved!")
    elif response.status_code == 404:
        print_error("User not found")
    else:
        print_error(f"Failed with status {response.status_code}")


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
    response = requests.post(f"{GATEWAY_URL}/order", json=order_data, timeout=15)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Order created successfully!")
    else:
        print_error(f"Order creation failed with status {response.status_code}")
    
    wait_for_user()
    
    print_step(4.2, "Listing all orders")
    print_request("GET", f"{GATEWAY_URL}/orders")
    response = requests.get(f"{GATEWAY_URL}/orders", timeout=15)
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
        response = requests.put(f"{GATEWAY_URL}/order/status/{order_id}", json=update_data, timeout=15)
        print_response(response)
        
        if i < len(statuses) - 1:
            wait_for_user()
    
    wait_for_user()
    
    print_step(5.4, "Verifying order status change")
    print_request("GET", f"{GATEWAY_URL}/order/{order_id}")
    response = requests.get(f"{GATEWAY_URL}/order/{order_id}", timeout=15)
    print_response(response)


def test_data_synchronization():
    """Test 6: Data synchronization between User and Order services"""
    print_header("TEST 6: DATA SYNCHRONIZATION (KEY FEATURE)")
    
    user_id = created_user_id or 1
    order_id = created_order_id or 1
    
    print_info("This test verifies that when a user updates their email/address,")
    print_info("the change is automatically synchronized to all their orders via RabbitMQ events.")
    print_info("")
    print_info("Architecture:")
    print_info("  User Service → RabbitMQ → Order Service (updates all user's orders)")
    print_info("               → RabbitMQ → Event Service (logs all events)")
    
    wait_for_user()
    
    # First, show current order state
    print_step(6.1, f"Current state of order {order_id} (BEFORE update)")
    print_request("GET", f"{GATEWAY_URL}/order/{order_id}")
    response = requests.get(f"{GATEWAY_URL}/order/{order_id}", timeout=15)
    print_response(response)
    
    wait_for_user()
    
    # Update user email
    print_step(6.2, f"Updating email for user {user_id}")
    new_email = f"synced_{int(time.time())}@example.com"
    update_data = {"email": new_email}
    print_request("PUT", f"{GATEWAY_URL}/user/{user_id}/email", update_data)
    response = requests.put(f"{GATEWAY_URL}/user/{user_id}/email", json=update_data, timeout=15)
    print_response(response)
    
    print_info("Event published to RabbitMQ: user.email_updated")
    print_info("Waiting 3 seconds for synchronization...")
    time.sleep(3)
    
    wait_for_user()
    
    # Check if order was updated
    print_step(6.3, f"Checking order {order_id} (AFTER email update)")
    print_request("GET", f"{GATEWAY_URL}/order/{order_id}")
    response = requests.get(f"{GATEWAY_URL}/order/{order_id}", timeout=15)
    print_response(response)
    
    try:
        order = response.json().get("status", {})
        if isinstance(order, dict) and order.get("user_email") == new_email:
            print_success("EMAIL SYNCHRONIZATION SUCCESSFUL!")
        else:
            print_info("Check if email was synchronized in the response above")
            print_info(f"Expected: {new_email}")
    except:
        pass
    
    wait_for_user()
    
    # Update user address
    print_step(6.4, f"Updating address for user {user_id}")
    new_address = f"456 Synced Address {int(time.time())}, Toronto, ON"
    update_data = {"delivery_address": new_address}
    print_request("PUT", f"{GATEWAY_URL}/user/{user_id}/address", update_data)
    response = requests.put(f"{GATEWAY_URL}/user/{user_id}/address", json=update_data, timeout=15)
    print_response(response)
    
    print_info("Event published to RabbitMQ: user.address_updated")
    print_info("Waiting 3 seconds for synchronization...")
    time.sleep(3)
    
    wait_for_user()
    
    # Check if order was updated
    print_step(6.5, f"Checking order {order_id} (AFTER address update)")
    print_request("GET", f"{GATEWAY_URL}/order/{order_id}")
    response = requests.get(f"{GATEWAY_URL}/order/{order_id}", timeout=15)
    print_response(response)
    
    try:
        order = response.json().get("status", {})
        if isinstance(order, dict) and order.get("user_address") == new_address:
            print_success("ADDRESS SYNCHRONIZATION SUCCESSFUL!")
        else:
            print_info("Check if address was synchronized in the response above")
            print_info(f"Expected: {new_address}")
    except:
        pass


def test_event_logging():
    """Test 7: Check event service logs (via Gateway)"""
    print_header("TEST 7: EVENT SERVICE LOGS")
    
    print_info("The Event Service subscribes to RabbitMQ and logs all user events.")
    print_info("Accessing event logs through the API Gateway...")
    
    wait_for_user()
    
    print_step(7.1, "Getting all logged events")
    print_request("GET", f"{GATEWAY_URL}/events")
    response = requests.get(f"{GATEWAY_URL}/events", timeout=15)
    print_response(response)
    
    try:
        data = response.json()
        total = data.get("total_events", 0)
        print_info(f"Total events logged: {total}")
        if total > 0:
            print_success("Event service is capturing RabbitMQ messages!")
    except:
        pass
    
    wait_for_user()
    
    print_step(7.2, "Getting event count")
    print_request("GET", f"{GATEWAY_URL}/events/count")
    response = requests.get(f"{GATEWAY_URL}/events/count", timeout=15)
    print_response(response)


def test_strangler_pattern():
    """Test 8: Test strangler pattern routing"""
    print_header("TEST 8: STRANGLER PATTERN ROUTING")
    
    print_info("The strangler pattern routes P% of requests to V1 and (100-P)% to V2")
    print_info("We'll make multiple requests - check Azure logs to see routing distribution")
    
    # Get current config
    print_step(8.1, "Getting current strangler pattern configuration")
    print_request("GET", f"{GATEWAY_URL}/config")
    response = requests.get(f"{GATEWAY_URL}/config", timeout=10)
    print_response(response)
    
    try:
        config = response.json()
        v1_pct = config['strangler_pattern']['v1_percentage']
        v2_pct = config['strangler_pattern']['v2_percentage']
        print_info(f"Expected distribution: ~{v1_pct}% to V1, ~{v2_pct}% to V2")
    except:
        pass
    
    wait_for_user()
    
    print_step(8.2, "Making 10 user listing requests")
    print_info("Each request is routed to V1 or V2 based on the configured percentage")
    print_info("Check API Gateway logs in Azure to see actual routing decisions\n")
    
    for i in range(10):
        print(f"  Request {i+1}/10...", end=" ")
        try:
            response = requests.get(f"{GATEWAY_URL}/users", timeout=15)
            if response.status_code == 200:
                print(f"{Colors.GREEN}OK{Colors.END}")
            else:
                print(f"{Colors.RED}Status {response.status_code}{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}")
        time.sleep(0.5)
    
    print_info("\nTo see routing decisions, check Azure Container Apps logs:")
    print_info("  az containerapp logs show --name api-gateway --resource-group rg-coen314-a2")
    print_info("Look for: [Strangler] Routing to User V1/V2...")


def test_batch_operations():
    """Test 9: Test V2-exclusive batch operations"""
    print_header("TEST 9: BATCH OPERATIONS (V2 EXCLUSIVE)")
    
    print_info("Batch user creation is a V2-only feature")
    print_info("This request will ALWAYS go to V2 regardless of strangler pattern config")
    
    wait_for_user()
    
    print_step(9.1, "Creating multiple users in batch")
    timestamp = int(time.time())
    batch_data = {
        "users": [
            {"email": f"batch1_{timestamp}@example.com", "delivery_address": "Batch Address 1"},
            {"email": f"batch2_{timestamp}@example.com", "delivery_address": "Batch Address 2"},
            {"email": f"batch3_{timestamp}@example.com", "delivery_address": "Batch Address 3"}
        ]
    }
    print_request("POST", f"{GATEWAY_URL}/users/batch", batch_data)
    response = requests.post(f"{GATEWAY_URL}/users/batch", json=batch_data, timeout=20)
    print_response(response)
    
    try:
        data = response.json()
        created = data.get("total_created", 0)
        errors = data.get("total_errors", 0)
        if created > 0:
            print_success(f"Batch creation successful! Created {created} users")
        if errors > 0:
            print_error(f"Had {errors} errors during batch creation")
    except:
        pass
    
    wait_for_user()
    
    print_step(9.2, "Listing all users after batch creation")
    print_request("GET", f"{GATEWAY_URL}/users")
    response = requests.get(f"{GATEWAY_URL}/users", timeout=15)
    print_response(response)


def test_orders_by_status():
    """Test 10: Get orders by status"""
    print_header("TEST 10: FILTER ORDERS BY STATUS")
    
    statuses = ["under process", "shipping", "delivered"]
    
    for i, status in enumerate(statuses):
        print_step(f"10.{i+1}", f"Getting orders with status: '{status}'")
        # URL encode the status (spaces become %20)
        encoded_status = status.replace(" ", "%20")
        print_request("GET", f"{GATEWAY_URL}/orders/status/{encoded_status}")
        response = requests.get(f"{GATEWAY_URL}/orders/status/{encoded_status}", timeout=15)
        print_response(response)
        
        if i < len(statuses) - 1:
            wait_for_user()


def run_all_tests():
    """Run all tests in sequence"""
    print_header("MICROSERVICES AUTOMATED TEST SUITE")
    print(f"{Colors.BOLD}COEN 424 - Assignment 2{Colors.END}")
    print(f"\nThis script tests all microservice functionality through the API Gateway.")
    print("You will be prompted to press Enter between each step.")
    print(f"\n{Colors.BOLD}API Gateway URL:{Colors.END} {GATEWAY_URL}")
    print(f"\n{Colors.BOLD}Architecture:{Colors.END}")
    print("  ┌─────────────────┐")
    print("  │   API Gateway   │  ← External (you are here)")
    print("  └────────┬────────┘")
    print("           │")
    print("  ┌────────┴────────┐")
    print("  │  Internal Only  │")
    print("  ├─────────────────┤")
    print("  │ User V1 & V2    │")
    print("  │ Order Service   │")
    print("  │ Event Service   │")
    print("  │ RabbitMQ        │")
    print("  │ MongoDB Atlas   │")
    print("  └─────────────────┘")
    
    wait_for_user()
    
    # Check gateway first
    if not check_gateway():
        print_error("\nAPI Gateway is not accessible!")
        print_info("Make sure the Azure Container Apps are running.")
        print_info(f"URL: {GATEWAY_URL}")
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
        print("  ✓ Azure Container Apps deployment")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user.{Colors.END}")
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


def run_quick_test():
    """Run a quick automated test without waiting for user input"""
    print_header("QUICK AUTOMATED TEST")
    print(f"Gateway URL: {GATEWAY_URL}\n")
    
    if not check_gateway():
        print_error("API Gateway not accessible!")
        return False
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Check status
    print("\n[1/7] Checking service status...")
    try:
        response = requests.get(f"{GATEWAY_URL}/status", timeout=30)
        if response.status_code == 200:
            if "Unavailable" not in response.text:
                print_success("All services connected")
                tests_passed += 1
            else:
                print_error("Some services unavailable")
                print(response.text)
                tests_failed += 1
        else:
            print_error(f"Status check failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 2: Create user
    print("\n[2/7] Creating user...")
    try:
        response = requests.post(f"{GATEWAY_URL}/user", json={
            "email": f"quicktest_{int(time.time())}@example.com",
            "delivery_address": "Quick Test Address"
        }, timeout=15)
        if response.status_code == 200:
            print_success("User created")
            tests_passed += 1
        else:
            print_error(f"User creation failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 3: List users
    print("\n[3/7] Listing users...")
    try:
        response = requests.get(f"{GATEWAY_URL}/users", timeout=15)
        if response.status_code == 200:
            print_success("Users listed")
            tests_passed += 1
        else:
            print_error(f"Failed to list users: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 4: Create order
    print("\n[4/7] Creating order...")
    try:
        response = requests.post(f"{GATEWAY_URL}/order", json={
            "user_id": "1",
            "items": [{"item": "Test Item", "quantity": 1}],
            "email": "quicktest@example.com",
            "delivery_address": "Quick Test Address"
        }, timeout=15)
        if response.status_code == 200:
            print_success("Order created")
            tests_passed += 1
        else:
            print_error(f"Order creation failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 5: Update user email (triggers sync)
    print("\n[5/7] Updating user email (testing sync)...")
    try:
        response = requests.put(f"{GATEWAY_URL}/user/1/email", json={
            "email": f"synced_{int(time.time())}@example.com"
        }, timeout=15)
        if response.status_code == 200:
            print_success("Email updated")
            tests_passed += 1
        else:
            print_error(f"Email update failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    time.sleep(2)  # Wait for sync
    
    # Test 6: Check events
    print("\n[6/7] Checking events...")
    try:
        response = requests.get(f"{GATEWAY_URL}/events", timeout=15)
        if response.status_code == 200:
            print_success("Events retrieved")
            tests_passed += 1
        else:
            print_error(f"Failed to get events: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Test 7: Batch create (V2 feature)
    print("\n[7/7] Testing batch creation (V2)...")
    try:
        response = requests.post(f"{GATEWAY_URL}/users/batch", json={
            "users": [
                {"email": f"batch_q1_{int(time.time())}@example.com", "delivery_address": "Addr 1"},
                {"email": f"batch_q2_{int(time.time())}@example.com", "delivery_address": "Addr 2"}
            ]
        }, timeout=20)
        if response.status_code == 200:
            print_success("Batch creation successful")
            tests_passed += 1
        else:
            print_error(f"Batch creation failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print_error(f"Error: {e}")
        tests_failed += 1
    
    # Summary
    print_header("QUICK TEST RESULTS")
    total = tests_passed + tests_failed
    print(f"Passed: {tests_passed}/{total}")
    print(f"Failed: {tests_failed}/{total}")
    
    if tests_failed == 0:
        print_success("\nAll tests passed!")
    else:
        print_error(f"\n{tests_failed} test(s) failed")
    
    return tests_failed == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = run_quick_test()
        sys.exit(0 if success else 1)
    else:
        run_all_tests()