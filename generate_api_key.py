#!/usr/bin/env python3

"""
PiNet API - API Key Generator
Generates a secure random API key and updates the .env file
"""

import os
import secrets
import string
import sys

# ANSI color codes for formatted output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message: str) -> None:
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str) -> None:
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str) -> None:
    """Print an info message"""
    print(f"{Colors.CYAN}➜ {message}{Colors.END}")

def print_warning(message: str) -> None:
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def generate_api_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure random API key

    Args:
        length: Length of the API key (default: 32)

    Returns:
        Secure random API key string
    """
    # Use URL-safe characters (letters, numbers, - and _)
    return secrets.token_urlsafe(length)

def update_env_file(env_path: str, api_key: str) -> bool:
    """
    Update the .env file with the new API key

    Args:
        env_path: Path to the .env file
        api_key: The new API key to set

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read the current .env file
        if not os.path.exists(env_path):
            print_error(f".env file not found at: {env_path}")
            print_info("Please create .env from .env.example first:")
            print_info("  cp .env.example .env")
            return False

        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find and update the API_KEY line
        updated = False
        new_lines = []

        for line in lines:
            if line.strip().startswith('API_KEY='):
                # Replace the API_KEY line
                new_lines.append(f'API_KEY={api_key}\n')
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            print_error("API_KEY line not found in .env file")
            print_info("Please ensure your .env file has an API_KEY= line")
            return False

        # Write the updated content back
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        return True

    except Exception as e:
        print_error(f"Failed to update .env file: {str(e)}")
        return False

def main():
    """Main execution"""
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}PiNet API - API Key Generator{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print()

    # Determine .env file path (same directory as this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')

    print_info(f"Looking for .env file at: {env_path}")

    # Generate API key
    print_info("Generating secure API key...")
    api_key = generate_api_key(32)
    print_success(f"Generated API key: {Colors.BOLD}{api_key}{Colors.END}")

    # Ask for confirmation
    print()
    print_warning("This will replace the existing API_KEY in your .env file.")
    response = input(f"{Colors.BOLD}Continue? (y/n): {Colors.END}").strip().lower()

    if response not in ['y', 'yes']:
        print_info("Operation cancelled by user")
        sys.exit(0)

    # Update .env file
    print()
    print_info("Updating .env file...")

    if update_env_file(env_path, api_key):
        print_success("API key successfully updated in .env file!")
        print()
        print(f"{Colors.BOLD}Your new API key:{Colors.END}")
        print(f"  {Colors.GREEN}{api_key}{Colors.END}")
        print()
        print_info("Next steps:")
        print("  1. Keep this API key secure")
        print("  2. Restart the PiNet API service if it's running:")
        print("     sudo systemctl restart pinet_api.service")
        print("  3. Update any client applications with the new API key")
        print()
        sys.exit(0)
    else:
        print_error("Failed to update .env file")
        print()
        print_info("Manual steps:")
        print(f"  1. Open your .env file: nano {env_path}")
        print(f"  2. Set API_KEY={api_key}")
        print()
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)