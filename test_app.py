#!/usr/bin/env python3

"""
PiNet API - Remote Test Script
Tests all API endpoints from a remote machine
"""

import sys
import json
import requests
from typing import Dict, Any, Tuple

# ANSI color codes for formatted output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str) -> None:
    """Print a formatted section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}\n")

def print_test(test_name: str) -> None:
    """Print a test name"""
    print(f"{Colors.BOLD}{Colors.BLUE}TEST: {test_name}{Colors.END}")

def print_success(message: str) -> None:
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str) -> None:
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message: str) -> None:
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message: str) -> None:
    """Print an info message"""
    print(f"{Colors.CYAN}➜ {message}{Colors.END}")

def format_json(data: Dict[str, Any]) -> str:
    """Format JSON data with indentation"""
    return json.dumps(data, indent=2)

def get_user_input() -> Tuple[str, str, str, str]:
    """
    Prompt user for test configuration

    Returns:
        Tuple of (base_url, api_key, test_ip, test_mac)
    """
    print_header("PiNet API - Remote Test Script")
    print("This script will test all API endpoints on your PiNet API server.\n")

    # Get base URL
    base_url = input(f"{Colors.BOLD}Enter Pi base URL (e.g., http://192.168.1.50:5000): {Colors.END}").strip()
    if not base_url:
        print_error("Base URL is required")
        sys.exit(1)

    # Remove trailing slash if present
    base_url = base_url.rstrip('/')

    # Get API key
    api_key = input(f"{Colors.BOLD}Enter API_KEY (from Pi's .env file): {Colors.END}").strip()
    if not api_key:
        print_error("API_KEY is required")
        sys.exit(1)

    # Get test IP address
    test_ip = input(f"{Colors.BOLD}Enter target IP address for ping test (e.g., 8.8.8.8): {Colors.END}").strip()
    if not test_ip:
        print_error("Target IP address is required")
        sys.exit(1)

    # Get test MAC address
    test_mac = input(f"{Colors.BOLD}Enter target MAC address for WoL test (e.g., AA:BB:CC:DD:EE:FF): {Colors.END}").strip()
    if not test_mac:
        print_error("Target MAC address is required")
        sys.exit(1)

    return base_url, api_key, test_ip, test_mac

def test_health_check(base_url: str) -> bool:
    """
    Test FR1: Health Check endpoint

    Args:
        base_url: Base URL of the API

    Returns:
        True if test passed, False otherwise
    """
    print_test("FR1: Health Check (GET /)")

    try:
        response = requests.get(f"{base_url}/", timeout=10)

        print_info(f"Status Code: {response.status_code}")

        try:
            data = response.json()
            print_info(f"Response Body:\n{format_json(data)}")
        except json.JSONDecodeError:
            print_error("Response is not valid JSON")
            return False

        # Verify response
        if response.status_code == 200:
            if data.get('service') == 'PiNet API' and data.get('status') == 'running':
                print_success("Health check passed!")
                return True
            else:
                print_error("Response data does not match expected format")
                return False
        else:
            print_error(f"Expected status code 200, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_ping_host(base_url: str, api_key: str, target_ip: str) -> bool:
    """
    Test FR2: Ping Host endpoint

    Args:
        base_url: Base URL of the API
        api_key: API key for authentication
        target_ip: IP address to ping

    Returns:
        True if test passed, False otherwise
    """
    print_test(f"FR2: Ping Host (GET /ping/{target_ip})")

    headers = {
        'X-API-Key': api_key
    }

    try:
        response = requests.get(f"{base_url}/ping/{target_ip}", headers=headers, timeout=10)

        print_info(f"Status Code: {response.status_code}")

        try:
            data = response.json()
            print_info(f"Response Body:\n{format_json(data)}")
        except json.JSONDecodeError:
            print_error("Response is not valid JSON")
            return False

        # Verify response
        if response.status_code == 200:
            if data.get('ip_address') == target_ip and data.get('status') in ['online', 'offline']:
                print_success(f"Ping test passed! Host is {data.get('status')}")
                return True
            else:
                print_error("Response data does not match expected format")
                return False
        else:
            print_error(f"Expected status code 200, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_wake_on_lan(base_url: str, api_key: str, target_mac: str) -> bool:
    """
    Test FR3: Wake-on-LAN endpoint

    Args:
        base_url: Base URL of the API
        api_key: API key for authentication
        target_mac: MAC address to send WoL packet to

    Returns:
        True if test passed, False otherwise
    """
    print_test(f"FR3: Wake-on-LAN (POST /wol)")

    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }

    payload = {
        'mac_address': target_mac
    }

    try:
        response = requests.post(f"{base_url}/wol", headers=headers, json=payload, timeout=10)

        print_info(f"Status Code: {response.status_code}")

        try:
            data = response.json()
            print_info(f"Response Body:\n{format_json(data)}")
        except json.JSONDecodeError:
            print_error("Response is not valid JSON")
            return False

        # Verify response
        if response.status_code == 200:
            if data.get('status') == 'success' and 'Wake-on-LAN packet sent' in data.get('message', ''):
                print_success("Wake-on-LAN test passed!")
                return True
            else:
                print_error("Response data does not match expected format")
                return False
        else:
            print_error(f"Expected status code 200, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_invalid_ip(base_url: str, api_key: str) -> bool:
    """
    Test error handling for invalid IP address

    Args:
        base_url: Base URL of the API
        api_key: API key for authentication

    Returns:
        True if test passed, False otherwise
    """
    print_test("Error Handling: Invalid IP Address")

    headers = {
        'X-API-Key': api_key
    }

    invalid_ip = "999.999.999.999"

    try:
        response = requests.get(f"{base_url}/ping/{invalid_ip}", headers=headers, timeout=10)

        print_info(f"Status Code: {response.status_code}")

        try:
            data = response.json()
            print_info(f"Response Body:\n{format_json(data)}")
        except json.JSONDecodeError:
            print_error("Response is not valid JSON")
            return False

        # Verify response
        if response.status_code == 400:
            if data.get('status') == 'error' and 'Invalid IP address format' in data.get('message', ''):
                print_success("Invalid IP error handling passed!")
                return True
            else:
                print_error("Response data does not match expected format")
                return False
        else:
            print_error(f"Expected status code 400, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_missing_api_key(base_url: str, target_ip: str) -> bool:
    """
    Test authentication with missing API key

    Args:
        base_url: Base URL of the API
        target_ip: IP address to ping

    Returns:
        True if test passed, False otherwise
    """
    print_test("Security: Missing API Key")

    try:
        response = requests.get(f"{base_url}/ping/{target_ip}", timeout=10)

        print_info(f"Status Code: {response.status_code}")

        try:
            data = response.json()
            print_info(f"Response Body:\n{format_json(data)}")
        except json.JSONDecodeError:
            print_error("Response is not valid JSON")
            return False

        # Verify response
        if response.status_code == 401:
            print_success("Missing API key handling passed!")
            return True
        else:
            print_error(f"Expected status code 401, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_wrong_api_key(base_url: str, target_ip: str) -> bool:
    """
    Test authentication with wrong API key

    Args:
        base_url: Base URL of the API
        target_ip: IP address to ping

    Returns:
        True if test passed, False otherwise
    """
    print_test("Security: Wrong API Key")

    headers = {
        'X-API-Key': 'wrong_api_key_12345'
    }

    try:
        response = requests.get(f"{base_url}/ping/{target_ip}", headers=headers, timeout=10)

        print_info(f"Status Code: {response.status_code}")

        try:
            data = response.json()
            print_info(f"Response Body:\n{format_json(data)}")
        except json.JSONDecodeError:
            print_error("Response is not valid JSON")
            return False

        # Verify response
        if response.status_code == 401:
            print_success("Wrong API key handling passed!")
            return True
        else:
            print_error(f"Expected status code 401, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def main():
    """Main test execution"""

    # Get user input
    base_url, api_key, test_ip, test_mac = get_user_input()

    # Track test results
    results = []

    # Run tests
    print_header("Running API Tests")

    # Functional tests
    results.append(("Health Check", test_health_check(base_url)))
    print()

    results.append(("Ping Host", test_ping_host(base_url, api_key, test_ip)))
    print()

    results.append(("Wake-on-LAN", test_wake_on_lan(base_url, api_key, test_mac)))
    print()

    # Error handling tests
    results.append(("Invalid IP", test_invalid_ip(base_url, api_key)))
    print()

    # Security tests
    results.append(("Missing API Key", test_missing_api_key(base_url, test_ip)))
    print()

    results.append(("Wrong API Key", test_wrong_api_key(base_url, test_ip)))
    print()

    # Print summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print()
    print(f"{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print_success("All tests passed! ✓")
        sys.exit(0)
    else:
        print_error(f"{total - passed} test(s) failed")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)