# PiNet API

A lightweight, secure REST API for network diagnostics and control, designed to run on Raspberry Pi hardware.

## Overview

PiNet API provides a simple HTTP interface for performing basic network operations:
- **Health Checks**: Verify the service is running
- **Host Ping**: Check if network devices are online/offline
- **Wake-on-LAN**: Remotely wake sleeping computers

Built specifically for low-resource environments like the Raspberry Pi 1, this API serves as a network utility accessible from any device on your local network.

## Features

- 🏥 **Service Health Check** - Simple endpoint to verify API availability
- 🔍 **Host Status Check** - ICMP ping to determine device reachability
- ⚡ **Wake-on-LAN** - Send magic packets to wake sleeping devices
- 🔐 **API Key Authentication** - Secure access with configurable keys
- 🚀 **Lightweight & Fast** - Optimized for Raspberry Pi 1 (ARM v6, 427MB RAM)
- 📝 **Comprehensive Logging** - systemd journal integration for debugging
- 🔄 **Auto-restart** - systemd ensures service reliability
- 🐍 **Python Client Library** - Easy integration into Python applications

## Hardware Requirements

**Tested Configuration:**
- **Device**: Raspberry Pi 1 Model B
- **Architecture**: ARMv6l (ARM1176 @ 700MHz)
- **Memory**: 512MB total (427MB usable)
- **OS**: Raspberry Pi OS (Legacy, 32-bit) Lite

**Also compatible with:**
- Raspberry Pi 2/3/4/5
- Raspberry Pi Zero/Zero W
- Any Linux system with Python 3.7+

## Quick Start

### Prerequisites

Ensure the following are installed on your Raspberry Pi:
```bash
# Install Git and Python tools
sudo apt update
sudo apt install -y git
```

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/michalkoterba/PiNet_API.git
   cd PiNet_API
   ```

2. **Run the automated installation script:**
   ```bash
   sudo bash install.sh
   ```

   The script will:
   - Install system dependencies
   - Create a Python virtual environment
   - Install Python packages
   - Generate `.env` configuration file
   - Install and start the systemd service

3. **Configure your API key:**
   ```bash
   # Option 1: Use the key generator (recommended)
   python3 generate_api_key.py

   # Option 2: Edit manually
   nano .env
   # Set: API_KEY=your_secure_random_key_here
   ```

4. **Restart the service:**
   ```bash
   sudo systemctl restart pinet_api.service
   ```

5. **Verify it's running:**
   ```bash
   # Check service status
   systemctl status pinet_api.service

   # Test the health endpoint
   curl http://localhost:5000/
   ```

## Configuration

All configuration is stored in the `.env` file:

```bash
# API Security
API_KEY=your_secure_api_key_here

# Server Configuration
API_PORT=5000
```

**Security Note:** The API key should be a cryptographically secure random string. Use the included `generate_api_key.py` script to generate one:

```bash
python3 generate_api_key.py
```

## Usage

### API Endpoints

#### 1. Health Check (Unauthenticated)

Check if the service is running:

```bash
curl http://192.168.1.50:5000/
```

**Response:**
```json
{
  "service": "PiNet API",
  "status": "running"
}
```

---

#### 2. Ping Host (Authenticated)

Check if a host is reachable on the network:

```bash
curl -H "X-API-Key: your_api_key_here" \
  http://192.168.1.50:5000/ping/8.8.8.8
```

**Response (Online):**
```json
{
  "ip_address": "8.8.8.8",
  "status": "online"
}
```

**Response (Offline):**
```json
{
  "ip_address": "192.168.1.100",
  "status": "offline"
}
```

**Error Response (Invalid IP):**
```json
{
  "status": "error",
  "message": "Invalid IP address format."
}
```

---

#### 3. Wake-on-LAN (Authenticated)

Send a Wake-on-LAN magic packet to wake a sleeping device:

```bash
curl -X POST \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF"}' \
  http://192.168.1.50:5000/wol
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Wake-on-LAN packet sent to AA:BB:CC:DD:EE:FF"
}
```

**Error Response (Invalid MAC):**
```json
{
  "status": "error",
  "message": "Invalid MAC address format."
}
```

---

### Python Client Library

Use the included Python client for easy integration:

```python
from pinet_client import PiNetClient

# Initialize client
with PiNetClient("http://192.168.1.50:5000", "your_api_key") as client:

    # Check service health
    health = client.check_health()
    print(f"Service running: {health.is_running}")

    # Check if host is online
    result = client.is_host_online("192.168.1.100")
    if result.is_online:
        print("Host is online!")
    else:
        print("Host is offline, sending WoL...")
        wol = client.wake_host("AA:BB:CC:DD:EE:FF")
        print(f"WoL sent: {wol.success}")
```

See `pinet_client.py` for full documentation and examples.

---

### Remote Testing

Test all endpoints from any machine using the included test script:

```bash
# Install requests library (if not already installed)
pip3 install requests

# Run the test script
python3 test_app.py
```

The script will prompt you for:
- Pi base URL (e.g., `http://192.168.1.50:5000`)
- API key
- Test IP address for ping
- Test MAC address for WoL

It will then execute comprehensive tests and display results.

## Service Management

The API runs as a systemd service (`pinet_api.service`):

```bash
# Check status
systemctl status pinet_api.service

# Start service
sudo systemctl start pinet_api.service

# Stop service
sudo systemctl stop pinet_api.service

# Restart service
sudo systemctl restart pinet_api.service

# Enable auto-start on boot
sudo systemctl enable pinet_api.service

# Disable auto-start
sudo systemctl disable pinet_api.service

# View logs (last 50 lines)
journalctl -u pinet_api.service -n 50

# View logs (follow in real-time)
journalctl -u pinet_api.service -f
```

## Project Structure

```
PiNet_API/
├── app.py                          # Main Flask application
├── pinet_client.py                 # Python client library
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── .env                           # Environment configuration (created during install)
├── .gitignore                     # Git ignore rules
├── pi_utility.service.template    # systemd service template
├── install.sh                     # Automated installation script
├── generate_api_key.py            # API key generator utility
├── test_app.py                    # Remote testing script
├── docs/
│   ├── SRS.md                     # Software Requirements Specification
│   ├── IMPLEMENTATION_PLAN.md     # Development checklist
│   └── PRE_DEPLOYMENT_CHECKLIST.md # Pre-deployment validation
└── README.md                      # This file
```

## Development

### Local Testing (Development Mode)

For development/testing without systemd:

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export API_KEY=test_key_12345
export API_PORT=5000

# Run Flask development server
python3 app.py
```

The API will be available at `http://localhost:5000`

### Updating the Service

To update an existing installation:

```bash
# Navigate to project directory
cd PiNet_API

# Pull latest changes
git pull origin main

# Update dependencies (if changed)
venv/bin/pip install -r requirements.txt

# Restart service
sudo systemctl restart pinet_api.service
```

## Troubleshooting

### Service won't start

```bash
# Check detailed logs
journalctl -u pinet_api.service -xe

# Common issues:
# - Missing or invalid .env file
# - Invalid API_KEY in .env
# - Port 5000 already in use
# - Missing Python dependencies
```

### 401 Unauthorized errors

- Verify the API key matches between `.env` and your client
- Ensure the `X-API-Key` header is set correctly
- Check service logs for authentication attempts

### Permission denied errors

- Ensure `install.sh` was run with `sudo`
- Verify file permissions: `ls -la .env`
- Check service runs as correct user: `systemctl status pinet_api.service`

### Port already in use

```bash
# Check what's using port 5000
sudo lsof -i :5000

# Change port in .env
nano .env
# Set: API_PORT=5001

# Restart service
sudo systemctl restart pinet_api.service
```

### Ping not working

- Verify Pi has network connectivity: `ping 8.8.8.8`
- Ensure target device allows ICMP (ping) requests
- Check firewall rules on target device

### Wake-on-LAN not working

- Verify target device has WoL enabled in BIOS/UEFI
- Ensure target device is connected via Ethernet (WiFi WoL is unreliable)
- Check target device's network card supports WoL
- Verify MAC address is correct
- WoL packets must be sent on the same subnet/VLAN

## Security Considerations

- **API Key**: Always use a strong, randomly generated API key
- **Network Access**: The API binds to `0.0.0.0`, making it accessible on all network interfaces
- **Firewall**: Consider restricting access using iptables or Pi-hole
- **HTTPS**: For production use over untrusted networks, place behind an HTTPS reverse proxy (nginx, Caddy)
- **Authentication**: Only the health check endpoint is unauthenticated; all others require API key

## Performance

Tested on Raspberry Pi 1:
- **Response time**: < 500ms (excluding ping delay)
- **Memory usage**: ~50-80MB
- **CPU usage**: < 5% idle, < 15% under load
- **Concurrent requests**: Handles 5-10 simultaneous requests comfortably

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) - Micro web framework
- Uses [Gunicorn](https://gunicorn.org/) - Python WSGI HTTP Server
- Wake-on-LAN powered by [wakeonlan](https://pypi.org/project/wakeonlan/) library

## Support

For issues, questions, or contributions:
- **Issues**: [GitHub Issues](https://github.com/your-username/PiNet_API/issues)
- **Documentation**: See `docs/SRS.md` for detailed specifications
- **Testing**: Use `test_app.py` for comprehensive endpoint validation

---

**Made with ❤️ for Raspberry Pi enthusiasts**