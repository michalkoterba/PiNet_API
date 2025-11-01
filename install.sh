#!/bin/bash

################################################################################
# PiNet API - Automated Installation Script
# This script automates the complete setup of the PiNet API service
################################################################################

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}➜ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

################################################################################
# Welcome Message
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  PiNet API - Installation Script"
echo "════════════════════════════════════════════════════════════"
echo ""
print_info "This script will install and configure the PiNet API service"
echo ""

################################################################################
# Prerequisite Checks
################################################################################

print_info "Checking prerequisites..."

# Check if running with sudo privileges
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run with sudo privileges"
    echo "Please run: sudo bash install.sh"
    exit 1
fi

print_success "Running with sudo privileges"

# Get the real user (not root when using sudo)
REAL_USER="${SUDO_USER:-$USER}"
if [ "$REAL_USER" = "root" ]; then
    print_warning "Running as root user. Service will run as root."
fi

################################################################################
# System Dependencies
################################################################################

print_info "Updating package list..."
apt update -qq || {
    print_error "Failed to update package list"
    exit 1
}
print_success "Package list updated"

print_info "Installing system dependencies..."

# Install python3-pip
if ! command -v pip3 &> /dev/null; then
    print_info "Installing python3-pip..."
    apt install -y python3-pip > /dev/null 2>&1 || {
        print_error "Failed to install python3-pip"
        exit 1
    }
    print_success "python3-pip installed"
else
    print_success "python3-pip already installed"
fi

# Install python3-venv
if ! dpkg -l | grep -q python3-venv; then
    print_info "Installing python3-venv..."
    apt install -y python3-venv > /dev/null 2>&1 || {
        print_error "Failed to install python3-venv"
        exit 1
    }
    print_success "python3-venv installed"
else
    print_success "python3-venv already installed"
fi

################################################################################
# Project Setup
################################################################################

print_info "Configuring project paths..."

# Determine the absolute path to the project directory
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="$REAL_USER"

print_success "Project directory: $APP_DIR"
print_success "Service will run as user: $APP_USER"

# Verify we're in the correct directory (check for app.py)
if [ ! -f "$APP_DIR/app.py" ]; then
    print_error "app.py not found in current directory"
    print_error "Please run this script from the PiNet_API project root"
    exit 1
fi

################################################################################
# Python Virtual Environment
################################################################################

print_info "Setting up Python virtual environment..."

# Create virtual environment
if [ ! -d "$APP_DIR/venv" ]; then
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv" || {
        print_error "Failed to create virtual environment"
        exit 1
    }
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Upgrade pip in virtual environment
print_info "Upgrading pip..."
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip > /dev/null 2>&1 || {
    print_error "Failed to upgrade pip"
    exit 1
}
print_success "pip upgraded"

# Install Python dependencies
print_info "Installing Python dependencies from requirements.txt..."
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" > /dev/null 2>&1 || {
    print_error "Failed to install Python dependencies"
    exit 1
}
print_success "Python dependencies installed"

################################################################################
# Configuration
################################################################################

print_info "Setting up configuration..."

# Copy .env.example to .env if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    sudo -u "$APP_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env" || {
        print_error "Failed to copy .env.example to .env"
        exit 1
    }
    print_success ".env file created from .env.example"
    print_warning "IMPORTANT: You must edit .env and set your API_KEY before using the service"
else
    print_success ".env file already exists (not overwriting)"
fi

# Set proper permissions on .env
chmod 600 "$APP_DIR/.env"
chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
print_success "Permissions set on .env file"

################################################################################
# Systemd Service Setup
################################################################################

print_info "Configuring systemd service..."

# Read the template and replace placeholders
if [ ! -f "$APP_DIR/pi_utility.service.template" ]; then
    print_error "pi_utility.service.template not found"
    exit 1
fi

# Replace placeholders using sed
sed -e "s|%%APP_DIR%%|$APP_DIR|g" \
    -e "s|%%APP_USER%%|$APP_USER|g" \
    "$APP_DIR/pi_utility.service.template" > "$APP_DIR/pinet_api.service" || {
    print_error "Failed to generate service file"
    exit 1
}
print_success "Service file generated: pinet_api.service"

# Copy service file to systemd directory
cp "$APP_DIR/pinet_api.service" /etc/systemd/system/pinet_api.service || {
    print_error "Failed to copy service file to /etc/systemd/system/"
    exit 1
}
print_success "Service file installed to /etc/systemd/system/"

# Reload systemd daemon
print_info "Reloading systemd daemon..."
systemctl daemon-reload || {
    print_error "Failed to reload systemd daemon"
    exit 1
}
print_success "systemd daemon reloaded"

# Enable service to start on boot
print_info "Enabling pinet_api service to start on boot..."
systemctl enable pinet_api.service || {
    print_error "Failed to enable service"
    exit 1
}
print_success "Service enabled"

# Start the service
print_info "Starting pinet_api service..."
systemctl start pinet_api.service || {
    print_error "Failed to start service"
    print_info "Check logs with: journalctl -u pinet_api.service -xe"
    exit 1
}
print_success "Service started"

################################################################################
# Final Status Check
################################################################################

# Wait a moment for service to initialize
sleep 2

# Check service status
print_info "Checking service status..."
if systemctl is-active --quiet pinet_api.service; then
    print_success "Service is running!"
else
    print_error "Service failed to start"
    print_info "Checking status..."
    systemctl status pinet_api.service --no-pager
    exit 1
fi

################################################################################
# Installation Complete
################################################################################

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Installation Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""

# Get the local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')

print_success "PiNet API service is running"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit the configuration file:"
echo "     nano $APP_DIR/.env"
echo ""
echo "  2. Set a secure API_KEY in the .env file"
echo "     Example: API_KEY=your_secure_random_key_here"
echo ""
echo "  3. Restart the service after changing configuration:"
echo "     sudo systemctl restart pinet_api.service"
echo ""
echo "API Access:"
echo "  • Local:    http://localhost:5000"
echo "  • Network:  http://$LOCAL_IP:5000"
echo ""
echo "Useful commands:"
echo "  • Check status:     systemctl status pinet_api.service"
echo "  • View logs:        journalctl -u pinet_api.service -f"
echo "  • Restart service:  sudo systemctl restart pinet_api.service"
echo "  • Stop service:     sudo systemctl stop pinet_api.service"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""