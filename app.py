"""
PiNet API - Network Diagnostics and Control API
A lightweight Flask API for Raspberry Pi to perform ping checks and Wake-on-LAN
"""

import os
import re
import sys
import logging
import subprocess
from functools import wraps

from flask import Flask, jsonify, request
from dotenv import load_dotenv
from wakeonlan import send_magic_packet

# =============================================================================
# Configuration & Setup
# =============================================================================

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Configure logging to stdout/stderr for systemd journal capture
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
API_KEY = os.getenv('API_KEY')
API_PORT = int(os.getenv('API_PORT', 5000))

# Validate that API_KEY is configured
if not API_KEY:
    logger.error("API_KEY not found in environment variables. Please configure .env file.")
    sys.exit(1)

logger.info("PiNet API starting up...")

# =============================================================================
# Authentication & Security
# =============================================================================

def require_api_key(f):
    """
    Decorator to require API key authentication for protected endpoints.
    Expects API key in 'X-API-Key' header.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key')

        if not provided_key:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr} - No API key provided")
            return jsonify({"status": "error", "message": "API key required"}), 401

        if provided_key != API_KEY:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr} - Invalid API key")
            return jsonify({"status": "error", "message": "Invalid API key"}), 401

        return f(*args, **kwargs)

    return decorated_function

# =============================================================================
# Input Validation
# =============================================================================

def validate_ip_address(ip_address):
    """
    Validate IPv4 address format to prevent command injection.

    Args:
        ip_address (str): IP address string to validate

    Returns:
        bool: True if valid IPv4 format, False otherwise
    """
    # IPv4 regex pattern: matches 0.0.0.0 to 255.255.255.255
    ipv4_pattern = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )

    if not ip_address or not isinstance(ip_address, str):
        return False

    return bool(ipv4_pattern.match(ip_address.strip()))

def validate_mac_address(mac_address):
    """
    Validate MAC address format.
    Supports formats: XX:XX:XX:XX:XX:XX, XX-XX-XX-XX-XX-XX, XXXXXXXXXXXX

    Args:
        mac_address (str): MAC address string to validate

    Returns:
        bool: True if valid MAC format, False otherwise
    """
    if not mac_address or not isinstance(mac_address, str):
        return False

    # Remove whitespace
    mac_address = mac_address.strip()

    # MAC address patterns (colon, hyphen, or no separator)
    mac_patterns = [
        re.compile(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'),  # XX:XX:XX:XX:XX:XX
        re.compile(r'^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$'),  # XX-XX-XX-XX-XX-XX
        re.compile(r'^[0-9A-Fa-f]{12}$')                       # XXXXXXXXXXXX
    ]

    return any(pattern.match(mac_address) for pattern in mac_patterns)

# =============================================================================
# API Endpoints
# =============================================================================

@app.route('/', methods=['GET'])
def health_check():
    """
    FR1: Service Health Check
    Unauthenticated endpoint to verify the API is running.

    Returns:
        JSON response with service status
    """
    return jsonify({
        "service": "PiNet API",
        "status": "running"
    }), 200

@app.route('/ping/<ip_address>', methods=['GET'])
@require_api_key
def ping_host(ip_address):
    """
    FR2: Ping Host
    Check if a host is reachable on the network via ICMP ping.

    Args:
        ip_address (str): Target IP address to ping

    Returns:
        JSON response with ping result (online/offline) or error
    """
    # Validate IP address format
    if not validate_ip_address(ip_address):
        logger.warning(f"Invalid IP address format received: {ip_address}")
        return jsonify({
            "status": "error",
            "message": "Invalid IP address format."
        }), 400

    try:
        # Execute ping command with single packet and timeout
        # -c 1: Send only 1 packet
        # -W 2: Wait maximum 2 seconds for response
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', ip_address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )

        # Check return code (0 = success/online, non-zero = failure/offline)
        if result.returncode == 0:
            logger.info(f"Ping successful: {ip_address} is online")
            return jsonify({
                "ip_address": ip_address,
                "status": "online"
            }), 200
        else:
            logger.info(f"Ping failed: {ip_address} is offline")
            return jsonify({
                "ip_address": ip_address,
                "status": "offline"
            }), 200

    except subprocess.TimeoutExpired:
        logger.info(f"Ping timeout: {ip_address} is offline")
        return jsonify({
            "ip_address": ip_address,
            "status": "offline"
        }), 200

    except Exception as e:
        logger.error(f"Error pinging {ip_address}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal error executing ping"
        }), 500

@app.route('/wol', methods=['POST'])
@require_api_key
def wake_on_lan():
    """
    FR3: Wake-on-LAN
    Send a WoL magic packet to wake a sleeping device.

    Expects JSON body: {"mac_address": "XX:XX:XX:XX:XX:XX"}

    Returns:
        JSON response with success or error message
    """
    # Parse JSON request body
    data = request.get_json()

    if not data:
        logger.warning("WoL request received with no JSON body")
        return jsonify({
            "status": "error",
            "message": "Request body must be JSON"
        }), 400

    mac_address = data.get('mac_address')

    if not mac_address:
        logger.warning("WoL request received without mac_address field")
        return jsonify({
            "status": "error",
            "message": "Missing mac_address field in request body"
        }), 400

    # Validate MAC address format
    if not validate_mac_address(mac_address):
        logger.warning(f"Invalid MAC address format received: {mac_address}")
        return jsonify({
            "status": "error",
            "message": "Invalid MAC address format."
        }), 400

    try:
        # Send Wake-on-LAN magic packet
        send_magic_packet(mac_address)
        logger.info(f"Wake-on-LAN packet sent successfully to {mac_address}")

        return jsonify({
            "status": "success",
            "message": f"Wake-on-LAN packet sent to {mac_address}"
        }), 200

    except Exception as e:
        logger.error(f"Error sending WoL packet to {mac_address}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to send Wake-on-LAN packet"
        }), 500

# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    logger.warning(f"404 Not Found: {request.url}")
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    logger.error(f"500 Internal Server Error: {str(error)}")
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
    return jsonify({
        "status": "error",
        "message": "An unexpected error occurred"
    }), 500

# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == '__main__':
    # Development server configuration
    # Note: In production, this app will be run via Gunicorn (see systemd service)
    logger.info(f"Starting development server on 0.0.0.0:{API_PORT}")
    app.run(
        host='0.0.0.0',  # Listen on all network interfaces
        port=API_PORT,
        debug=False       # Disable debug mode for security
    )