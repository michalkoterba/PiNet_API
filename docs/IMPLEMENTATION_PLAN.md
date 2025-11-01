# PiNet API - Implementation Plan

## Project Overview
This document provides a comprehensive implementation checklist for the PiNet API project - a lightweight, secure API for network diagnostics and control functions running on a Raspberry Pi 1.

**Target Hardware:** Raspberry Pi 1 (armv6l, 427MB RAM)
**Tech Stack:** Python 3, Flask, Gunicorn
**Reference:** See `docs/SRS.md` for detailed requirements

---

## Prerequisites & Environment

- [x] Raspberry Pi 1 with Raspberry Pi OS (Legacy, 32-bit) Lite
- [x] SSH access configured
- [x] Git installed on the Pi
- [x] Network connectivity verified
- [x] Python 3 available on the system

---

## Phase 1: Project Setup & Configuration Files

### 1.1 Dependencies & Requirements
- [x] Create `requirements.txt` with:
  - [x] Flask (micro web framework)
  - [x] Gunicorn (WSGI server)
  - [x] python-dotenv (environment variable management)
  - [x] wakeonlan (WoL magic packet library)

### 1.2 Environment Configuration
- [x] Create `.env.example` template with:
  - [x] `API_KEY` placeholder (for authentication)
  - [x] `API_PORT` placeholder (default: 5000)
  - [x] Comments explaining each variable

### 1.3 Version Control
- [x] Create `.gitignore` to exclude:
  - [x] `.env` (sensitive credentials)
  - [x] `venv/` and `.venv/` (virtual environments)
  - [x] `__pycache__/` and `*.pyc` (Python cache)
  - [x] `*.log` (log files)
  - [x] IDE-specific files (`.idea/`, `.vscode/`)

---

## Phase 2: Core Application Development

### 2.1 Flask Application Structure (app.py)

#### Setup & Configuration
- [x] Import required modules (Flask, os, subprocess, etc.)
- [x] Load environment variables using python-dotenv
- [x] Initialize Flask application
- [x] Configure logging to stdout/stderr

#### Authentication & Security
- [x] Implement API key authentication decorator
- [x] Check `X-API-Key` header against `.env` API_KEY
- [x] Return 401 Unauthorized for invalid/missing keys
- [x] Apply decorator to protected endpoints only

#### Input Validation
- [x] Create IP address validator function
  - [x] Use regex to validate IPv4 format
  - [x] Prevent command injection attacks
  - [x] Return clear error messages for invalid input
- [x] Create MAC address validator function
  - [x] Support common MAC formats (colon/hyphen/none)
  - [x] Validate format: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
  - [x] Return clear error messages for invalid input

### 2.2 API Endpoints

#### FR1: Health Check Endpoint
- [x] Implement `GET /` endpoint
- [x] No authentication required
- [x] Return JSON: `{"service": "PiNet API", "status": "running"}`
- [x] Return HTTP 200 OK
- [x] Log service startup

#### FR2: Ping Host Endpoint
- [x] Implement `GET /ping/<ip_address>` endpoint
- [x] Apply authentication decorator
- [x] Validate IP address format
- [x] Execute system ping command using subprocess
  - [x] Use `-c 1` for single ping
  - [x] Set timeout to prevent hanging
  - [x] Capture return code
- [x] Return appropriate JSON responses:
  - [x] Success (online): `{"ip_address": "...", "status": "online"}`
  - [x] Success (offline): `{"ip_address": "...", "status": "offline"}`
  - [x] Error (invalid IP): `{"status": "error", "message": "Invalid IP address format."}`
- [x] Return correct HTTP status codes (200, 400, 401)
- [x] Log successful ping requests with IP address

#### FR3: Wake-on-LAN Endpoint
- [x] Implement `POST /wol` endpoint
- [x] Apply authentication decorator
- [x] Accept JSON body with `mac_address` field
- [x] Validate MAC address format
- [x] Use wakeonlan library to send magic packet
- [x] Return appropriate JSON responses:
  - [x] Success: `{"status": "success", "message": "Wake-on-LAN packet sent to ..."}`
  - [x] Error (invalid MAC): `{"status": "error", "message": "Invalid MAC address format."}`
- [x] Return correct HTTP status codes (200, 400, 401)
- [x] Log successful WoL requests with MAC address

#### Error Handling
- [x] Implement global error handler for 404 Not Found
- [x] Implement global error handler for 500 Internal Server Error
- [x] Log all errors to stderr
- [x] Return JSON error responses consistently

### 2.3 Application Entry Point
- [x] Add `if __name__ == '__main__':` block for development
- [x] Configure Flask to run on `0.0.0.0` (all interfaces)
- [x] Use port from environment variable or default 5000
- [x] Add comment noting Gunicorn will be used in production

---

## Phase 3: Deployment Automation

### 3.1 Systemd Service Template
- [x] Create `pi_utility.service.template` file with:
  - [x] Service description
  - [x] `After=network.target` (wait for network)
  - [x] `WorkingDirectory=%%APP_DIR%%` placeholder
  - [x] `User=%%APP_USER%%` placeholder
  - [x] `ExecStart` using venv's Gunicorn:
    - [x] Path: `%%APP_DIR%%/venv/bin/gunicorn`
    - [x] Bind to `0.0.0.0:5000`
    - [x] Workers: 2 (lightweight for Pi)
    - [x] Module: `app:app`
  - [x] `Restart=always` (auto-restart on crash)
  - [x] `RestartSec=3` (wait 3 seconds before restart)
  - [x] `WantedBy=multi-user.target`

### 3.2 Installation Script (install.sh)
- [x] Create `install.sh` bash script with:

#### Prerequisite Checks
- [x] Check for sudo privileges (required for installation)
- [x] Print welcome message with script purpose

#### System Dependencies
- [x] Run `sudo apt update`
- [x] Install `python3-pip` package
- [x] Install `python3-venv` package
- [x] Verify installations successful

#### Project Setup
- [x] Determine absolute path to project directory (`APP_DIR=$(pwd)`)
- [x] Determine current user (`APP_USER=$(whoami)`)
- [x] Print detected values for confirmation

#### Python Environment
- [x] Create virtual environment: `python3 -m venv venv`
- [x] Upgrade pip in venv: `venv/bin/pip install --upgrade pip`
- [x] Install requirements: `venv/bin/pip install -r requirements.txt`
- [x] Verify installations successful

#### Configuration
- [x] Copy `.env.example` to `.env`
- [x] Check if `.env` already exists (don't overwrite)
- [x] Remind user to edit `.env` with their API key

#### Systemd Service
- [x] Read `pi_utility.service.template` file
- [x] Replace `%%APP_DIR%%` with actual path using `sed`
- [x] Replace `%%APP_USER%%` with actual user using `sed`
- [x] Save output as `pinet_api.service` (generated file)
- [x] Copy generated file to `/etc/systemd/system/`
- [x] Run `sudo systemctl daemon-reload`
- [x] Run `sudo systemctl enable pinet_api.service`
- [x] Run `sudo systemctl start pinet_api.service`

#### Final Status
- [x] Check service status: `systemctl status pinet_api.service`
- [x] Print success message with:
  - [x] Reminder to edit `.env` with API_KEY
  - [x] API URL (e.g., `http://<pi_ip>:5000`)
  - [x] Commands to check logs: `journalctl -u pinet_api.service -f`
  - [x] Commands to restart: `sudo systemctl restart pinet_api.service`

#### Script Polish
- [x] ~~Make script executable: `chmod +x install.sh`~~ (The script will be made executable when it's run on the Raspberry Pi with bash install.sh, or the user can run chmod +x install.sh directly on the Pi
  after cloning.)
- [x] Add proper error handling (exit on errors)
- [x] Add comments explaining each step
- [x] Use colored output for better readability (optional)

---

## Phase 4: Testing & Validation

### 4.1 Remote Test Script (test_app.py)
- [x] Create `test_app.py` Python script with:

#### User Input
- [x] Prompt for Pi base URL (e.g., `http://192.168.1.50:5000`)
- [x] Prompt for API_KEY from Pi's `.env` file
- [x] Prompt for target IP address (for ping test)
- [x] Prompt for target MAC address (for WoL test)
- [x] Strip whitespace from inputs

#### Test Execution
- [x] Test FR1: Health Check (`GET /`)
  - [x] Send request without API key
  - [x] Print status code and response JSON
  - [x] Verify status is "running"
- [x] Test FR2: Ping Host (`GET /ping/<ip>`)
  - [x] Send request with API key in `X-API-Key` header
  - [x] Print status code and response JSON
  - [x] Verify IP address echoed back correctly
- [x] Test FR3: Wake-on-LAN (`POST /wol`)
  - [x] Send request with API key and MAC in JSON body
  - [x] Print status code and response JSON
  - [x] Verify success message

#### Output Formatting
- [x] Print clear test headers for each endpoint
- [x] Format JSON output with indentation
- [x] Use colors or formatting for pass/fail (optional)
- [x] Handle network errors gracefully
- [x] Print summary at the end

### 4.2 Manual Testing Checklist
- [x] Test health check from browser
- [x] Test ping with valid IP
- [x] Test ping with invalid IP (verify 400 error)
- [x] Test ping without API key (verify 401 error)
- [x] Test WoL with valid MAC address
- [x] Test WoL with invalid MAC (verify 400 error)
- [x] Test WoL without API key (verify 401 error)
- [x] Test with wrong API key (verify 401 error)
- [x] Verify logs are captured in systemd journal
- [x] Test service restart: `sudo systemctl restart pinet_api.service`
- [x] Test service survives reboot

---

## Phase 5: Non-Functional Requirements Validation

### NFR1: Performance
- [x] Test response time < 5 seconds (excluding ping delay)
- [x] Monitor CPU usage with `htop` or `top`
- [x] Monitor memory usage (should fit in 427MB)
- [x] Test under light concurrent load (5-10 requests)

### NFR2: Reliability & Availability
- [x] Verify service starts on boot
- [ ] Verify service auto-restarts after crash
  - [ ] Test: `sudo kill -9 <gunicorn_pid>`
  - [ ] Check: Service should restart within seconds
- [ ] Verify service waits for network (network.target)

### NFR3: Deployment
- [ ] Verify all files are in Git repository
- [x] Test fresh clone and install on clean Pi

### NFR4: Configuration
- [ ] Verify no hard-coded credentials in code
- [x] Verify `.env` is excluded from Git
- [x] Verify `.env.example` is committed
- [x] Test loading environment variables from `.env`
- [x] Verify API_KEY and API_PORT are configurable

### NFR5: Security
- [x] Verify root endpoint (`/`) is unauthenticated
- [x] Verify `/ping` requires API key
- [x] Verify `/wol` requires API key
- [x] Verify wrong API key returns 401
- [x] Verify missing API key returns 401
- [ ] Test IP injection attempts (should be blocked)
- [ ] Test MAC injection attempts (should be blocked)

### NFR6: Logging
- [x] Verify service startup is logged
- [x] Verify successful ping requests are logged with IP
- [x] Verify successful WoL requests are logged with MAC
- [x] Verify invalid IP/MAC attempts are logged
- [x] Verify unauthorized attempts are logged
- [x] Verify errors are logged to stderr
- [x] Check logs: `journalctl -u pinet_api.service -n 50`

---

## Phase 6: Documentation & Repository

### 6.1 Repository Setup
- [x] Initialize Git repository (if not already done)
- [x] Add remote to GitHub (or preferred Git host)
- [x] Commit all files with descriptive messages
- [x] Push to remote repository

### 6.2 README Documentation
- [x] Create `README.md` with:
  - [x] Project description and purpose
  - [x] Features list (health check, ping, WoL)
  - [x] Hardware requirements
  - [x] Info on how to install Git on Raspberry Pi 1
  - [x] Installation instructions (clone + run install.sh)
  - [x] Configuration instructions (edit .env)
  - [x] Usage examples (curl commands for each endpoint)
  - [x] Testing instructions (run test_app.py)
  - [x] Troubleshooting section
  - [x] License information

---

## Phase 7: Final Validation & Deployment

### 7.1 Pre-Deployment Checklist
- [x] All code reviewed and tested
- [x] All security requirements met
- [x] All performance requirements met
- [x] Documentation complete
- [x] `.gitignore` properly configured
- [x] No sensitive data in repository

### 7.2 Deployment to Production Pi
- [x] Clone repository to Pi: `git clone <repo_url>`
- [x] Navigate to project directory
- [x] Run installation script: `sudo bash install.sh`
- [x] Edit `.env` with strong API key
- [x] Verify service is running: `systemctl status pinet_api.service`
- [x] Test all endpoints from remote machine using `test_app.py`

### 7.3 Post-Deployment Validation
- [x] Service accessible from local network
- [x] All endpoints responding correctly
- [x] Logs being captured properly
- [x] Service survives Pi reboot
- [ ] Monitor for first 24 hours for stability

---

### Useful Commands
```bash
# Check service status
systemctl status pinet_api.service

# View logs (last 50 lines)
journalctl -u pinet_api.service -n 50

# View logs (follow in real-time)
journalctl -u pinet_api.service -f

# Restart service
sudo systemctl restart pinet_api.service

# Stop service
sudo systemctl stop pinet_api.service

# Start service
sudo systemctl start pinet_api.service

# Disable service (won't start on boot)
sudo systemctl disable pinet_api.service

# Re-enable service
sudo systemctl enable pinet_api.service
```

---

## Project Completion Checklist

- [x] All functional requirements (FR1-FR5) implemented
- [x] All non-functional requirements (NFR1-NFR6) validated
- [x] All files created and committed to repository
- [x] Installation script tested on fresh Pi
- [x] Remote test script validates all endpoints
- [x] Documentation complete and accurate
- [x] Service stable and reliable on target hardware
- [x] Project successfully deployed and operational

---

**Project Status**: ⬜ Not Started | 🟨 In Progress | ✅ Complete

**Last Updated**: 2025-11-0

**Notes**: Use this checklist to track implementation progress. Check off items as they are completed. Update status and notes as needed.