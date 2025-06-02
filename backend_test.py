#!/usr/bin/env python3
import requests
import json
import websocket
import threading
import time
import uuid
import os
from datetime import datetime

# Get the backend URL from environment variable or use default
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:8001")
if not BACKEND_URL.endswith("/api"):
    BACKEND_URL = f"{BACKEND_URL}/api"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def log_test_result(test_name, passed, message=""):
    """Log test result and update counters"""
    result = "PASS" if passed else "FAIL"
    print(f"[{result}] {test_name}: {message}")
    
    test_results["tests"].append({
        "name": test_name,
        "passed": passed,
        "message": message
    })
    
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            if "status" in data and data["status"] == "healthy":
                log_test_result("Health Endpoint", True, "Health endpoint is working correctly")
                return True
            else:
                log_test_result("Health Endpoint", False, f"Health endpoint returned unexpected data: {data}")
        else:
            log_test_result("Health Endpoint", False, f"Health endpoint returned status code {response.status_code}")
    except Exception as e:
        log_test_result("Health Endpoint", False, f"Exception occurred: {str(e)}")
    
    return False

def test_create_user():
    """Test user creation endpoint"""
    try:
        # Create a test user with random interests
        user_data = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "age": 25,
            "interests": ["travel", "technology", "music", "food"],
            "language": "en"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/users/create", json=user_data)
        
        if response.status_code == 200:
            data = response.json()
            if "user_id" in data and "message" in data:
                log_test_result("Create User", True, f"User created successfully with ID: {data['user_id']}")
                return data["user_id"]
            else:
                log_test_result("Create User", False, f"User creation response missing expected fields: {data}")
        else:
            log_test_result("Create User", False, f"User creation failed with status code {response.status_code}: {response.text}")
    except Exception as e:
        log_test_result("Create User", False, f"Exception occurred: {str(e)}")
    
    return None

def test_get_bot_profiles():
    """Test getting all bot profiles"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/bots/profiles")
        
        if response.status_code == 200:
            data = response.json()
            if "bot_profiles" in data and len(data["bot_profiles"]) > 0:
                log_test_result("Get Bot Profiles", True, f"Retrieved {len(data['bot_profiles'])} bot profiles")
                return data["bot_profiles"]
            else:
                log_test_result("Get Bot Profiles", False, "Bot profiles response missing expected data")
        else:
            log_test_result("Get Bot Profiles", False, f"Bot profiles request failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("Get Bot Profiles", False, f"Exception occurred: {str(e)}")
    
    return None

def test_bot_matching(user_id):
    """Test bot matching algorithm"""
    if not user_id:
        log_test_result("Bot Matching", False, "Cannot test bot matching without valid user ID")
        return None
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/bots/match/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            if "matched_bot" in data and "compatibility_score" in data:
                log_test_result("Bot Matching", True, 
                               f"Matched with bot: {data['matched_bot']['name']} (Score: {data['compatibility_score']})")
                return data["matched_bot"]
            else:
                log_test_result("Bot Matching", False, "Bot matching response missing expected data")
        else:
            log_test_result("Bot Matching", False, f"Bot matching failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("Bot Matching", False, f"Exception occurred: {str(e)}")
    
    return None

def test_start_chat_session(user_id, bot_id):
    """Test starting a new chat session"""
    if not user_id or not bot_id:
        log_test_result("Start Chat Session", False, "Cannot test chat session without valid user ID and bot ID")
        return None
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/chat/start?user_id={user_id}&bot_id={bot_id}")
        
        if response.status_code == 200:
            data = response.json()
            if "session_id" in data and "bot_profile" in data and "welcome_message" in data:
                log_test_result("Start Chat Session", True, 
                               f"Chat session started with ID: {data['session_id']}")
                return data["session_id"]
            else:
                log_test_result("Start Chat Session", False, "Chat session response missing expected data")
        else:
            log_test_result("Start Chat Session", False, f"Starting chat session failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("Start Chat Session", False, f"Exception occurred: {str(e)}")
    
    return None

def test_get_user_sessions(user_id):
    """Test getting user's chat sessions"""
    if not user_id:
        log_test_result("Get User Sessions", False, "Cannot test getting sessions without valid user ID")
        return None
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/chat/sessions/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            if "sessions" in data:
                log_test_result("Get User Sessions", True, 
                               f"Retrieved {len(data['sessions'])} chat sessions for user")
                return data["sessions"]
            else:
                log_test_result("Get User Sessions", False, "User sessions response missing expected data")
        else:
            log_test_result("Get User Sessions", False, f"Getting user sessions failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("Get User Sessions", False, f"Exception occurred: {str(e)}")
    
    return None

def test_get_chat_messages(session_id):
    """Test getting chat messages for a session"""
    if not session_id:
        log_test_result("Get Chat Messages", False, "Cannot test getting messages without valid session ID")
        return None
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/chat/messages/{session_id}")
        
        if response.status_code == 200:
            data = response.json()
            if "messages" in data:
                log_test_result("Get Chat Messages", True, 
                               f"Retrieved {len(data['messages'])} messages for chat session")
                return data["messages"]
            else:
                log_test_result("Get Chat Messages", False, "Chat messages response missing expected data")
        else:
            log_test_result("Get Chat Messages", False, f"Getting chat messages failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("Get Chat Messages", False, f"Exception occurred: {str(e)}")
    
    return None

def get_websocket_url(session_id, user_id):
    """Get WebSocket URL from backend URL"""
    # Extract the host and port from BACKEND_URL
    backend_host = BACKEND_URL.replace('http://', '').replace('https://', '').replace('/api', '')
    return f"ws://{backend_host}/ws/{session_id}/{user_id}"

def test_websocket_chat(session_id, user_id):
    """Test WebSocket real-time chat"""
    if not session_id or not user_id:
        log_test_result("WebSocket Chat", False, "Cannot test WebSocket without valid session ID and user ID")
        return False
    
    messages_received = []
    websocket_connected = False
    websocket_error = None
    
    def on_message(ws, message):
        messages_received.append(json.loads(message))
        print(f"Received message: {message}")
    
    def on_error(ws, error):
        nonlocal websocket_error
        websocket_error = str(error)
        print(f"WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print(f"WebSocket closed: {close_status_code} - {close_msg}")
    
    def on_open(ws):
        nonlocal websocket_connected
        websocket_connected = True
        print("WebSocket connection established")
        
        # Send a test message
        test_message = {
            "content": "Hello, this is a test message!"
        }
        ws.send(json.dumps(test_message))
        
        # Send another message after a short delay
        time.sleep(2)
        test_message2 = {
            "content": "How are you doing today?"
        }
        ws.send(json.dumps(test_message2))
    
    # Create WebSocket connection
    ws_url = f"ws://localhost:8001/ws/{session_id}/{user_id}"
    ws = websocket.WebSocketApp(ws_url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    # Start WebSocket connection in a separate thread
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for messages
    timeout = 10  # seconds
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if len(messages_received) >= 2:  # We expect at least 2 responses
            break
        time.sleep(0.5)
    
    # Close WebSocket connection
    ws.close()
    
    # Check results
    if websocket_error:
        log_test_result("WebSocket Chat", False, f"WebSocket error occurred: {websocket_error}")
        return False
    
    if not websocket_connected:
        log_test_result("WebSocket Chat", False, "WebSocket connection failed to establish")
        return False
    
    if len(messages_received) < 2:
        log_test_result("WebSocket Chat", False, f"Expected at least 2 messages, but received {len(messages_received)}")
        return False
    
    # Verify message structure
    for msg in messages_received:
        if not isinstance(msg, dict) or "type" not in msg:
            log_test_result("WebSocket Chat", False, "Received message has invalid format")
            return False
    
    log_test_result("WebSocket Chat", True, f"Successfully exchanged {len(messages_received)} messages via WebSocket")
    return True

def test_content_moderation(session_id, user_id):
    """Test content moderation system with violation keywords"""
    if not session_id or not user_id:
        log_test_result("Content Moderation", False, "Cannot test moderation without valid session ID and user ID")
        return False
    
    messages_received = []
    moderation_warning_received = False
    
    def on_message(ws, message):
        msg_data = json.loads(message)
        messages_received.append(msg_data)
        if msg_data.get("type") == "moderation_warning":
            nonlocal moderation_warning_received
            moderation_warning_received = True
            print("Moderation warning received!")
    
    def on_error(ws, error):
        print(f"WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print(f"WebSocket closed: {close_status_code} - {close_msg}")
    
    def on_open(ws):
        print("WebSocket connection established for moderation test")
        
        # Send a message with violation keywords
        test_message = {
            "content": "I hate this and want to hurt someone"
        }
        ws.send(json.dumps(test_message))
    
    # Create WebSocket connection
    ws_url = f"ws://localhost:8001/ws/{session_id}/{user_id}"
    ws = websocket.WebSocketApp(ws_url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    # Start WebSocket connection in a separate thread
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for moderation response
    timeout = 5  # seconds
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if moderation_warning_received:
            break
        time.sleep(0.5)
    
    # Close WebSocket connection
    ws.close()
    
    # Check results
    if moderation_warning_received:
        log_test_result("Content Moderation", True, "Content moderation system correctly identified violation keywords")
        return True
    else:
        log_test_result("Content Moderation", False, "Content moderation system failed to detect violation keywords")
        return False

def test_protection_status():
    """Test the protection status endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/admin/protection-status")
        
        if response.status_code == 200:
            data = response.json()
            if "protection_enabled" in data:
                protection_enabled = data["protection_enabled"]
                message = f"Protection system is {'enabled' if protection_enabled else 'disabled'}"
                
                if protection_enabled and "protection_stats" in data and "ai_service_status" in data:
                    stats = data["protection_stats"]
                    service_status = data["ai_service_status"]
                    message += f", {stats.get('proxies_available', 0)} proxies available"
                    
                log_test_result("Protection Status", True, message)
                return data
            else:
                log_test_result("Protection Status", False, "Protection status response missing expected data")
        else:
            log_test_result("Protection Status", False, f"Protection status request failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("Protection Status", False, f"Exception occurred: {str(e)}")
    
    return None

def test_reset_failed_services():
    """Test resetting failed AI services"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/admin/reset-failed-services")
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "reset" in data["message"].lower():
                log_test_result("Reset Failed Services", True, "Successfully reset failed services")
                return True
            else:
                log_test_result("Reset Failed Services", False, f"Unexpected response: {data}")
        else:
            # If protection is not enabled, this might return an error which is expected
            if response.status_code == 400 or response.status_code == 404:
                error_data = response.json()
                if "error" in error_data and "not available" in error_data["error"].lower():
                    log_test_result("Reset Failed Services", True, "Protection modules not available - expected response")
                    return True
            
            log_test_result("Reset Failed Services", False, f"Reset failed services request failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("Reset Failed Services", False, f"Exception occurred: {str(e)}")
    
    return False

def test_add_proxies():
    """Test adding premium proxies"""
    try:
        # Test proxies (these won't actually be used in the test environment)
        test_proxies = [
            "http://test:test@proxy1.example.com:8080",
            "http://test:test@proxy2.example.com:8080"
        ]
        
        response = requests.post(f"{BACKEND_URL}/api/admin/add-proxies", json=test_proxies)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "added" in data["message"].lower():
                log_test_result("Add Proxies", True, f"Successfully added test proxies: {data['message']}")
                return True
            else:
                log_test_result("Add Proxies", False, f"Unexpected response: {data}")
        else:
            # If protection is not enabled, this might return an error which is expected
            if response.status_code == 400 or response.status_code == 404:
                error_data = response.json()
                if "error" in error_data and "not available" in error_data["error"].lower():
                    log_test_result("Add Proxies", True, "Protection modules not available - expected response")
                    return True
            
            log_test_result("Add Proxies", False, f"Add proxies request failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("Add Proxies", False, f"Exception occurred: {str(e)}")
    
    return False

def test_api_keys_status():
    """Test API keys status endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/admin/api-keys-status")
        
        if response.status_code == 200:
            data = response.json()
            services = ['gemini', 'deepinfra', 'huggingface', 'openai']
            
            # Check if all expected services are in the response
            all_services_present = all(service in data for service in services)
            
            if all_services_present:
                configured_keys = sum(data[service].get("configured_keys", 0) for service in services)
                message = f"API keys status retrieved successfully. {configured_keys} total keys configured."
                log_test_result("API Keys Status", True, message)
                return data
            else:
                log_test_result("API Keys Status", False, "API keys status response missing expected services")
        else:
            # If protection is not enabled, this might return an error which is expected
            if response.status_code == 400 or response.status_code == 404:
                error_data = response.json()
                if "error" in error_data and "not available" in error_data["error"].lower():
                    log_test_result("API Keys Status", True, "Protection modules not available - expected response")
                    return True
            
            log_test_result("API Keys Status", False, f"API keys status request failed with status code {response.status_code}")
    except Exception as e:
        log_test_result("API Keys Status", False, f"Exception occurred: {str(e)}")
    
    return None

def run_all_tests():
    """Run all backend tests in sequence"""
    print("\n===== STARTING BACKEND TESTS =====\n")
    
    # Test health endpoint
    test_health_endpoint()
    
    # Test IP protection system endpoints
    print("\n----- Testing IP Protection System -----\n")
    test_protection_status()
    test_reset_failed_services()
    test_add_proxies()
    test_api_keys_status()
    
    # Test user creation
    print("\n----- Testing Core Chat Functionality -----\n")
    user_id = test_create_user()
    
    # Test bot profiles
    bot_profiles = test_get_bot_profiles()
    
    # If we have a valid user ID and bot profiles, continue with other tests
    if user_id and bot_profiles:
        # Test bot matching
        matched_bot = test_bot_matching(user_id)
        
        if matched_bot:
            # Test starting chat session
            session_id = test_start_chat_session(user_id, matched_bot["bot_id"])
            
            if session_id:
                # Test getting user sessions
                test_get_user_sessions(user_id)
                
                # Test getting chat messages
                test_get_chat_messages(session_id)
                
                # Test WebSocket chat
                test_websocket_chat(session_id, user_id)
                
                # Test content moderation
                test_content_moderation(session_id, user_id)
    
    # Print summary
    print("\n===== TEST SUMMARY =====")
    print(f"Total tests: {test_results['passed'] + test_results['failed']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print("========================\n")
    
    # Return overall success/failure
    return test_results["failed"] == 0

if __name__ == "__main__":
    run_all_tests()
