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
- [ ] Git installed on the Pi
- [ ] Network connectivity verified
- [ ] Python 3 available on the system

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
- [ ] Create `pi_utility.service.template` file with:
  - [ ] Service description
  - [ ] `After=network.target` (wait for network)
  - [ ] `WorkingDirectory=%%APP_DIR%%` placeholder
  - [ ] `User=%%APP_USER%%` placeholder
  - [ ] `ExecStart` using venv's Gunicorn:
    - [ ] Path: `%%APP_DIR%%/venv/bin/gunicorn`
    - [ ] Bind to `0.0.0.0:5000`
    - [ ] Workers: 2 (lightweight for Pi)
    - [ ] Module: `app:app`
  - [ ] `Restart=always` (auto-restart on crash)
  - [ ] `RestartSec=3` (wait 3 seconds before restart)
  - [ ] `WantedBy=multi-user.target`

### 3.2 Installation Script (install.sh)
- [ ] Create `install.sh` bash script with:

#### Prerequisite Checks
- [ ] Check for sudo privileges (required for installation)
- [ ] Print welcome message with script purpose

#### System Dependencies
- [ ] Run `sudo apt update`
- [ ] Install `python3-pip` package
- [ ] Install `python3-venv` package
- [ ] Verify installations successful

#### Project Setup
- [ ] Determine absolute path to project directory (`APP_DIR=$(pwd)`)
- [ ] Determine current user (`APP_USER=$(whoami)`)
- [ ] Print detected values for confirmation

#### Python Environment
- [ ] Create virtual environment: `python3 -m venv venv`
- [ ] Upgrade pip in venv: `venv/bin/pip install --upgrade pip`
- [ ] Install requirements: `venv/bin/pip install -r requirements.txt`
- [ ] Verify installations successful

#### Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Check if `.env` already exists (don't overwrite)
- [ ] Remind user to edit `.env` with their API key

#### Systemd Service
- [ ] Read `pi_utility.service.template` file
- [ ] Replace `%%APP_DIR%%` with actual path using `sed`
- [ ] Replace `%%APP_USER%%` with actual user using `sed`
- [ ] Save output as `pinet_api.service` (generated file)
- [ ] Copy generated file to `/etc/systemd/system/`
- [ ] Run `sudo systemctl daemon-reload`
- [ ] Run `sudo systemctl enable pinet_api.service`
- [ ] Run `sudo systemctl start pinet_api.service`

#### Final Status
- [ ] Check service status: `systemctl status pinet_api.service`
- [ ] Print success message with:
  - [ ] Reminder to edit `.env` with API_KEY
  - [ ] API URL (e.g., `http://<pi_ip>:5000`)
  - [ ] Commands to check logs: `journalctl -u pinet_api.service -f`
  - [ ] Commands to restart: `sudo systemctl restart pinet_api.service`

#### Script Polish
- [ ] Make script executable: `chmod +x install.sh`
- [ ] Add proper error handling (exit on errors)
- [ ] Add comments explaining each step
- [ ] Use colored output for better readability (optional)

---

## Phase 4: Testing & Validation

### 4.1 Remote Test Script (test_app.py)
- [ ] Create `test_app.py` Python script with:

#### User Input
- [ ] Prompt for Pi base URL (e.g., `http://192.168.1.50:5000`)
- [ ] Prompt for API_KEY from Pi's `.env` file
- [ ] Prompt for target IP address (for ping test)
- [ ] Prompt for target MAC address (for WoL test)
- [ ] Strip whitespace from inputs

#### Test Execution
- [ ] Test FR1: Health Check (`GET /`)
  - [ ] Send request without API key
  - [ ] Print status code and response JSON
  - [ ] Verify status is "running"
- [ ] Test FR2: Ping Host (`GET /ping/<ip>`)
  - [ ] Send request with API key in `X-API-Key` header
  - [ ] Print status code and response JSON
  - [ ] Verify IP address echoed back correctly
- [ ] Test FR3: Wake-on-LAN (`POST /wol`)
  - [ ] Send request with API key and MAC in JSON body
  - [ ] Print status code and response JSON
  - [ ] Verify success message

#### Output Formatting
- [ ] Print clear test headers for each endpoint
- [ ] Format JSON output with indentation
- [ ] Use colors or formatting for pass/fail (optional)
- [ ] Handle network errors gracefully
- [ ] Print summary at the end

### 4.2 Manual Testing Checklist
- [ ] Test health check from browser
- [ ] Test ping with valid IP
- [ ] Test ping with invalid IP (verify 400 error)
- [ ] Test ping without API key (verify 401 error)
- [ ] Test WoL with valid MAC address
- [ ] Test WoL with invalid MAC (verify 400 error)
- [ ] Test WoL without API key (verify 401 error)
- [ ] Test with wrong API key (verify 401 error)
- [ ] Verify logs are captured in systemd journal
- [ ] Test service restart: `sudo systemctl restart pinet_api.service`
- [ ] Test service survives reboot

---

## Phase 5: Non-Functional Requirements Validation

### NFR1: Performance
- [ ] Test response time < 5 seconds (excluding ping delay)
- [ ] Monitor CPU usage with `htop` or `top`
- [ ] Monitor memory usage (should fit in 427MB)
- [ ] Test under light concurrent load (5-10 requests)

### NFR2: Reliability & Availability
- [ ] Verify service starts on boot
- [ ] Verify service auto-restarts after crash
  - [ ] Test: `sudo kill -9 <gunicorn_pid>`
  - [ ] Check: Service should restart within seconds
- [ ] Verify service waits for network (network.target)

### NFR3: Deployment
- [ ] Verify all files are in Git repository
- [ ] Test fresh clone and install on clean Pi
- [ ] Test update process:
  - [ ] Pull changes from repository
  - [ ] Restart service
  - [ ] Verify updates applied

### NFR4: Configuration
- [ ] Verify no hard-coded credentials in code
- [ ] Verify `.env` is excluded from Git
- [ ] Verify `.env.example` is committed
- [ ] Test loading environment variables from `.env`
- [ ] Verify API_KEY and API_PORT are configurable

### NFR5: Security
- [ ] Verify root endpoint (`/`) is unauthenticated
- [ ] Verify `/ping` requires API key
- [ ] Verify `/wol` requires API key
- [ ] Verify wrong API key returns 401
- [ ] Verify missing API key returns 401
- [ ] Test IP injection attempts (should be blocked)
- [ ] Test MAC injection attempts (should be blocked)

### NFR6: Logging
- [ ] Verify service startup is logged
- [ ] Verify successful ping requests are logged with IP
- [ ] Verify successful WoL requests are logged with MAC
- [ ] Verify invalid IP/MAC attempts are logged
- [ ] Verify unauthorized attempts are logged
- [ ] Verify errors are logged to stderr
- [ ] Check logs: `journalctl -u pinet_api.service -n 50`

---

## Phase 6: Documentation & Repository

### 6.1 Repository Setup
- [ ] Initialize Git repository (if not already done)
- [ ] Add remote to GitHub (or preferred Git host)
- [ ] Commit all files with descriptive messages
- [ ] Push to remote repository

### 6.2 README Documentation
- [ ] Create `README.md` with:
  - [ ] Project description and purpose
  - [ ] Features list (health check, ping, WoL)
  - [ ] Hardware requirements
  - [ ] Installation instructions (clone + run install.sh)
  - [ ] Configuration instructions (edit .env)
  - [ ] Usage examples (curl commands for each endpoint)
  - [ ] Testing instructions (run test_app.py)
  - [ ] Troubleshooting section
  - [ ] License information

### 6.3 Additional Documentation
- [ ] Ensure `docs/SRS.md` is up to date
- [ ] Add API endpoint documentation (optional: OpenAPI/Swagger)
- [ ] Document service management commands
- [ ] Document log viewing commands

---

## Phase 7: Final Validation & Deployment

### 7.1 Pre-Deployment Checklist
- [ ] All code reviewed and tested
- [ ] All security requirements met
- [ ] All performance requirements met
- [ ] Documentation complete
- [ ] `.gitignore` properly configured
- [ ] No sensitive data in repository

### 7.2 Deployment to Production Pi
- [ ] Clone repository to Pi: `git clone <repo_url>`
- [ ] Navigate to project directory
- [ ] Run installation script: `sudo bash install.sh`
- [ ] Edit `.env` with strong API key
- [ ] Verify service is running: `systemctl status pinet_api.service`
- [ ] Test all endpoints from remote machine using `test_app.py`

### 7.3 Post-Deployment Validation
- [ ] Service accessible from local network
- [ ] All endpoints responding correctly
- [ ] Logs being captured properly
- [ ] Service survives Pi reboot
- [ ] Monitor for first 24 hours for stability

---

## Maintenance & Updates

### Regular Maintenance Tasks
- [ ] Check logs periodically: `journalctl -u pinet_api.service`
- [ ] Monitor system resources: `htop`
- [ ] Keep OS updated: `sudo apt update && sudo apt upgrade`
- [ ] Rotate API key periodically for security

### Update Procedure
- [ ] SSH into Pi
- [ ] Navigate to project directory
- [ ] Pull changes: `git pull origin main`
- [ ] Update dependencies: `venv/bin/pip install -r requirements.txt`
- [ ] Restart service: `sudo systemctl restart pinet_api.service`
- [ ] Verify service is running properly

---

## Troubleshooting Guide

### Common Issues
- [ ] **Service won't start**: Check logs with `journalctl -u pinet_api.service -xe`
- [ ] **401 Errors**: Verify API key matches between `.env` and test script
- [ ] **Permission denied**: Ensure `install.sh` was run with sudo
- [ ] **Port already in use**: Check if another service is using port 5000
- [ ] **Ping not working**: Verify Pi has network access and ping command available
- [ ] **WoL not working**: Ensure target device has WoL enabled in BIOS

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

- [ ] All functional requirements (FR1-FR5) implemented
- [ ] All non-functional requirements (NFR1-NFR6) validated
- [ ] All files created and committed to repository
- [ ] Installation script tested on fresh Pi
- [ ] Remote test script validates all endpoints
- [ ] Documentation complete and accurate
- [ ] Service stable and reliable on target hardware
- [ ] Project successfully deployed and operational

---

**Project Status**: ⬜ Not Started | 🟨 In Progress | ✅ Complete

**Last Updated**: [To be filled during implementation]

**Notes**: Use this checklist to track implementation progress. Check off items as they are completed. Update status and notes as needed.