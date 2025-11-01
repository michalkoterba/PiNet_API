# Software Requirements Specification (SRS)
# PiNet API

## 1. Introduction

### 1.1 Purpose
This document specifies the requirements for the "PiNet API," a lightweight, secure software application. The purpose of this application is to provide a simple, network-accessible API (Application Programming Interface) for performing basic network diagnostics and control functions from a low-power, single-board computer.

### 1.2 Scope
The application will function as a standalone web service running on the target hardware. It will be capable of:
1.  Responding to authenticated HTTP requests to check the network status (online/offline) of any host on the local network via an ICMP ping.
2.  Responding to authenticated HTTP requests to send a Wake-on-LAN (WoL) magic packet to a specified MAC address.
3.  Providing a basic, unauthenticated health check endpoint to confirm the service is operational.

### 1.3 Target Hardware & Deployment
* **Host Hardware:** Raspberry Pi 1 (Confirmed)
* **Processor Architecture:** `armv6l` (ARM1176 @ 700MHz)
* **System Memory:** `427Mi` (Usable from 512MB total)
* **Operating System:** Raspberry Pi OS (Legacy, 32-bit) Lite
* **Deployment Method:** Code will be managed via a Git/GitHub repository and run as a `systemd` service on the host.

## 2. Overall Description

### 2.1 Product Perspective
The PiNet API is a self-contained, standalone backend service. It is not intended to be a public-facing server but rather a local-network utility secured by an API key. It will operate headless (no GUI) and be managed via SSH for deployment and maintenance.

### 2.2 Product Functions
The application will expose three (3) primary functions via an HTTP API:

1.  **Host Status Check:** The ability to "ping" a given IP address to determine if the device is reachable on the network.
2.  **Wake-on-LAN (WoL):** The ability to broadcast a WoL magic packet to wake a sleeping, WoL-enabled computer.
3.  **Service Health Check:** A simple endpoint to confirm the API service itself is running and responsive.

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 FR1: Service Health Check
* **ID:** FR1
* **Requirement:** The service shall provide a root (`/`) endpoint to verify its operational status. This is the only endpoint that **does not** require authentication.
* **Endpoint:** `GET /`
* **Response (Success):**
    * `Status Code: 200 OK`
    * `Body (JSON): {"service": "PiNet API", "status": "running"}`

#### 3.1.2 FR2: Ping Host
* **ID:** FR2
* **Requirement:** The service shall accept an authenticated request with an IP address and return the reachability status of that host.
* **Endpoint:** `GET /ping/<ip_address>`
* **Input:** `<ip_address>` (string, e.g., "192.168.1.10")
* **Process:**
    1.  The service **must** validate the request contains a valid API Key (see NFR5).
    2.  The service **must** validate the incoming `<ip_address>` string to ensure it is a valid and safe IP address format (e.g., using a regular expression) to prevent command injection.
    3.  If valid, the service will execute a system `ping` command targeting the specified IP.
* **Response (Host Online):**
    * `Status Code: 200 OK`
    * `Body (JSON): {"ip_address": "...", "status": "online"}`
* **Response (Host Offline):**
    * `Status Code: 200 OK`
    * `Body (JSON): {"ip_address": "...", "status": "offline"}`
* **Response (Error - Invalid IP):**
    * `Status Code: 400 Bad Request`
    * `Body (JSON): {"status": "error", "message": "Invalid IP address format."}`
* **Response (Error - Unauthorized):**
    * `Status Code: 401 Unauthorized`

#### 3.1.3 FR3: Send Wake-on-LAN (WoL)
* **ID:** FR3
* **Requirement:** The service shall accept an authenticated request containing a MAC address and broadcast a WoL magic packet to that address.
* **Endpoint:** `POST /wol`
* **Input:** `Request Body (JSON): {"mac_address": "..."}`
* **Process:**
    1.  The service **must** validate the request contains a valid API Key (see NFR5).
    2.  The service **must** validate the incoming `mac_address` string.
    3.  If valid, the service will craft and broadcast a WoL magic packet.
* **Response (Success):**
    * `Status Code: 200 OK`
    * `Body (JSON): {"status": "success", "message": "Wake-on-LAN packet sent to ..."}`
* **Response (Error - Invalid MAC):**
    * `Status Code: 400 Bad Request`
    * `Body (JSON): {"status": "error", "message": "Invalid MAC address format."}`
* **Response (Error - Unauthorized):**
    * `Status Code: 401 Unauthorized`

#### 3.1.4 FR4: Automated Installation Script
* **ID:** FR4
* **Requirement:** The project repository shall include a Bash script (`install.sh`) to automate the full setup. The script is intended to be run *from within* the root directory of the manually cloned repository.
* **Process:** The script **shall** perform the following actions:
    1.  Check for `sudo` privileges (required for installing packages and managing `systemd`).
    2.  Update the `apt` package list (`sudo apt update`).
    3.  Install system-level dependencies: `python3-pip` and `python3-venv` (Git is assumed to be present as the user cloned the repo).
    4.  Determine the absolute path to the current project directory (e.g., `APP_DIR=$(pwd)`).
    5.  Determine the current user (e.g., `APP_USER=$(whoami)`).
    6.  Create a Python virtual environment in the current directory (e.g., `python3 -m venv venv`).
    7.  Install all Python dependencies from `requirements.txt` into the new virtual environment (e.g., `venv/bin/pip install -r requirements.txt`).
    8.  Copy `.env.example` to `.env`.
    9.  **Dynamically create the service file:** Read the `pi_utility.service.template` file, replace placeholders (e.g., `%%APP_DIR%%`, `%%APP_USER%%`) with the correct values, and save the result as a new file (e.g., `pinet_api.service`).
    10. Copy the *newly generated* `pinet_api.service` file into the systemd directory (`/etc/systemd/system/`).
    11. Reload the `systemd` daemon (`sudo systemctl daemon-reload`).
    12. Enable the `pinet_api.service` to start on boot (`sudo systemctl enable pinet_api.service`).
    13. Start the `pinet_api.service` immediately (`sudo systemctl start pinet_api.service`).
    14. Print a final status message indicating success, reminding the user to edit `.env` with their `API_KEY`, and showing the URL the API is running on (e.g., `http://<pi_ip>:5000`).

#### 3.1.5 FR5: Remote Test Script
* **ID:** FR5
* **Requirement:** The project repository shall include a separate Python script (`test_app.py`) for remotely testing the deployed API.
* **Process:** This script is intended to be run from any machine *other than* the Pi (e.g., a developer's laptop) to test the API over the network.
* **Functionality:** The script **shall**:
    1.  Prompt the user for the Pi's base URL (e.g., `http://192.168.1.50:5000`).
    2.  Prompt the user for the `API_KEY` (from the Pi's `.env` file).
    3.  Prompt the user for a target IP to ping (for testing FR2).
    4.  Prompt the user for a target MAC address (for testing FR3).
    5.  Execute a test for each API endpoint (FR1, FR2, FR3), passing the `API_KEY` in an `X-API-Key` HTTP header for authenticated endpoints.
    6.  Print the HTTP status code and JSON response for each test to the console in a clear, human-readable format.

### 3.2 Non-Functional Requirements

#### 3.2.1 NFR1: Performance (Resource Constraints)
* The application **must** be lightweight, prioritizing low CPU and memory usage.
* The application **must** run efficiently on the confirmed `armv6l` CPU and `427Mi` of available RAM.
* The API should respond to any request in under 5 seconds (excluding the natural delay of the `ping` command itself).

#### 3.2.2 NFR2: Reliability & Availability
* The service **must** run as a persistent background process.
* The service **must** automatically start on system boot after the network is available.
* The service **must** automatically restart if the application process crashes.
* This will be achieved by running the application as a `systemd` service.

#### 3.2.3 NFR3: Deployment
* All application code (`app.py`, `requirements.txt`, `pi_utility.service.template`, `install.sh`, `.env.example`, `.gitignore`, `test_app.py`) **must** be stored and version-controlled in a Git repository (e.g., on GitHub).
* Deployment to the Pi will be performed by cloning the repository and running the `install.sh` script.
* Updates will be performed by pulling changes from the repository and restarting the service.

#### 3.2.4 NFR4: Configuration
* The application **must not** contain hard-coded credentials or user-specific configuration.
* All configuration **must** be loaded at runtime from an environment file named `.env`.
* The `.env` file itself **must** be excluded from version control (via the `.gitignore` file).
* A template file named `.env.example` **must** be included in the repository to document required variables, such as `API_KEY` and `API_PORT`.

#### 3.2.5 NFR5: Security & Access Control
* All API endpoints, **except** for the root health check (`/`), **must** be protected.
* Protected endpoints **must** require a valid API key to be passed in an `X-API-Key` HTTP header.
* The secret `API_KEY` will be defined in the `.env` file.
* If a request is made to a protected endpoint without a key, or with an incorrect key, the service **must** return an `HTTP 401 Unauthorized` response.

#### 3.2.6 NFR6: Logging
* The application **must** log key events and errors to `stdout` and `stderr` to allow for `systemd` journal capture.
* Key events to log include:
    * Service startup.
    * Successful WoL request (logging the MAC address).
    * Successful Ping request (logging the IP).
* Errors to log include:
    * Failed validation (invalid IP or MAC).
    * Unauthorized access attempts.
    * Internal application errors.

### 3.3 Technology Constraints
To meet the strict performance requirements (NFR1), the following technology stack is mandated:

* **Language:** Python 3
* **API Framework:** Flask (a "micro-framework")
* **Web Server:** Gunicorn (as a lightweight WSGI runner)
* **Dependencies:** `venv` will be used for Python environment isolation.
* **Libraries:** `python-dotenv` (for loading `.env` files), `wakeonlan`, `gunicorn`.
* **Containerization:** **Docker will not be used**, as it is infeasible on the `armv6l` CPU and would violate the low-resource constraints.
* **Ping Functionality:** Will be implemented by shelling out to the system's native `ping` command via the `subprocess` module.
* **WoL Functionality:** Will be implemented using the `wakeonlan` Python library.