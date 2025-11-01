#!/usr/bin/env python3

"""
PiNet API Client
A Python client library for interacting with the PiNet API
"""

import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class HealthStatus:
    """Health check response data"""
    service: str
    status: str
    is_running: bool


@dataclass
class PingResult:
    """Ping result response data"""
    ip_address: str
    is_online: bool
    status: str


@dataclass
class WakeOnLanResult:
    """Wake-on-LAN result response data"""
    success: bool
    message: str
    mac_address: str


class PiNetAPIError(Exception):
    """Base exception for PiNet API errors"""
    pass


class AuthenticationError(PiNetAPIError):
    """Raised when API authentication fails"""
    pass


class ValidationError(PiNetAPIError):
    """Raised when input validation fails"""
    pass


class NetworkError(PiNetAPIError):
    """Raised when network communication fails"""
    pass


class PiNetClient:
    """
    Client for interacting with PiNet API

    Example usage:
        client = PiNetClient("http://192.168.1.50:5000", "your_api_key")

        # Check service health
        health = client.check_health()
        print(f"Service is running: {health.is_running}")

        # Check if host is online
        result = client.is_host_online("8.8.8.8")
        print(f"Host is online: {result.is_online}")

        # Wake up a host
        wol_result = client.wake_host("AA:BB:CC:DD:EE:FF")
        print(f"WoL sent: {wol_result.success}")
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 10):
        """
        Initialize PiNet API client

        Args:
            base_url: Base URL of the PiNet API (e.g., "http://192.168.1.50:5000")
            api_key: API key for authentication
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Make HTTP request to the API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/ping/8.8.8.8")
            json_data: JSON data for POST requests
            require_auth: Whether to include API key header

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If input validation fails
            NetworkError: If network request fails
            PiNetAPIError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"

        # Prepare headers
        headers = {}
        if not require_auth and 'X-API-Key' in self.session.headers:
            # Temporarily remove API key for unauthenticated endpoints
            headers = dict(self.session.headers)
            del headers['X-API-Key']
        else:
            headers = dict(self.session.headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                headers=headers,
                timeout=self.timeout
            )

            # Handle HTTP errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid or missing API key")
            elif response.status_code == 400:
                error_msg = response.json().get('message', 'Validation error')
                raise ValidationError(error_msg)
            elif response.status_code >= 400:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                raise PiNetAPIError(f"API error: {error_msg}")

            return response.json()

        except requests.exceptions.Timeout:
            raise NetworkError(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise NetworkError(f"Failed to connect to {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error: {str(e)}")
        except ValueError as e:
            raise PiNetAPIError(f"Invalid JSON response: {str(e)}")

    def check_health(self) -> HealthStatus:
        """
        Check if the PiNet API service is running

        Returns:
            HealthStatus object with service information

        Raises:
            NetworkError: If unable to reach the service
            PiNetAPIError: If the response is invalid

        Example:
            >>> client = PiNetClient("http://192.168.1.50:5000", "api_key")
            >>> health = client.check_health()
            >>> print(f"Service: {health.service}, Running: {health.is_running}")
        """
        data = self._make_request('GET', '/', require_auth=False)

        return HealthStatus(
            service=data.get('service', 'Unknown'),
            status=data.get('status', 'unknown'),
            is_running=data.get('status') == 'running'
        )

    def is_host_online(self, ip_address: str) -> PingResult:
        """
        Check if a host is online by pinging it

        Args:
            ip_address: IP address to ping (e.g., "192.168.1.100" or "8.8.8.8")

        Returns:
            PingResult object with ping status

        Raises:
            AuthenticationError: If API key is invalid
            ValidationError: If IP address format is invalid
            NetworkError: If unable to reach the API
            PiNetAPIError: For other API errors

        Example:
            >>> client = PiNetClient("http://192.168.1.50:5000", "api_key")
            >>> result = client.is_host_online("8.8.8.8")
            >>> if result.is_online:
            ...     print(f"{result.ip_address} is online!")
            ... else:
            ...     print(f"{result.ip_address} is offline")
        """
        data = self._make_request('GET', f'/ping/{ip_address}')

        return PingResult(
            ip_address=data.get('ip_address', ip_address),
            status=data.get('status', 'unknown'),
            is_online=data.get('status') == 'online'
        )

    def wake_host(self, mac_address: str) -> WakeOnLanResult:
        """
        Send Wake-on-LAN magic packet to wake up a host

        Args:
            mac_address: MAC address of the host to wake up
                        (e.g., "AA:BB:CC:DD:EE:FF" or "AA-BB-CC-DD-EE-FF")

        Returns:
            WakeOnLanResult object with operation status

        Raises:
            AuthenticationError: If API key is invalid
            ValidationError: If MAC address format is invalid
            NetworkError: If unable to reach the API
            PiNetAPIError: For other API errors

        Example:
            >>> client = PiNetClient("http://192.168.1.50:5000", "api_key")
            >>> result = client.wake_host("AA:BB:CC:DD:EE:FF")
            >>> if result.success:
            ...     print(f"WoL packet sent: {result.message}")
            ... else:
            ...     print("Failed to send WoL packet")
        """
        json_data = {
            'mac_address': mac_address
        }

        data = self._make_request('POST', '/wol', json_data=json_data)

        return WakeOnLanResult(
            success=data.get('status') == 'success',
            message=data.get('message', ''),
            mac_address=mac_address
        )

    def ping_and_wake(self, ip_address: str, mac_address: str, wake_if_offline: bool = True) -> Dict[str, Any]:
        """
        Convenience method: Ping a host and optionally wake it if offline

        Args:
            ip_address: IP address to check
            mac_address: MAC address to use for Wake-on-LAN
            wake_if_offline: Whether to send WoL packet if host is offline (default: True)

        Returns:
            Dictionary with ping result and WoL result (if sent)

        Example:
            >>> client = PiNetClient("http://192.168.1.50:5000", "api_key")
            >>> result = client.ping_and_wake("192.168.1.100", "AA:BB:CC:DD:EE:FF")
            >>> if result['was_online']:
            ...     print("Host was already online")
            >>> elif result['wol_sent']:
            ...     print("Host was offline, WoL packet sent")
        """
        # Check if host is online
        ping_result = self.is_host_online(ip_address)

        result = {
            'ip_address': ip_address,
            'was_online': ping_result.is_online,
            'wol_sent': False,
            'wol_result': None
        }

        # Wake if offline and requested
        if not ping_result.is_online and wake_if_offline:
            wol_result = self.wake_host(mac_address)
            result['wol_sent'] = True
            result['wol_result'] = wol_result

        return result

    def close(self):
        """Close the underlying HTTP session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage and testing
if __name__ == '__main__':
    import sys

    # Example configuration
    BASE_URL = "http://192.168.1.50:5000"
    API_KEY = "your_api_key_here"

    print("PiNet API Client - Example Usage\n")
    print("=" * 60)

    # Create client (can also use context manager)
    try:
        with PiNetClient(BASE_URL, API_KEY) as client:

            # 1. Check health
            print("\n1. Checking service health...")
            try:
                health = client.check_health()
                print(f"   Service: {health.service}")
                print(f"   Status: {health.status}")
                print(f"   Running: {health.is_running}")
            except PiNetAPIError as e:
                print(f"   Error: {e}")

            # 2. Ping a host
            print("\n2. Checking if host is online...")
            try:
                result = client.is_host_online("8.8.8.8")
                print(f"   IP: {result.ip_address}")
                print(f"   Online: {result.is_online}")
                print(f"   Status: {result.status}")
            except PiNetAPIError as e:
                print(f"   Error: {e}")

            # 3. Send Wake-on-LAN
            print("\n3. Sending Wake-on-LAN packet...")
            try:
                result = client.wake_host("AA:BB:CC:DD:EE:FF")
                print(f"   Success: {result.success}")
                print(f"   Message: {result.message}")
            except PiNetAPIError as e:
                print(f"   Error: {e}")

            # 4. Ping and wake (convenience method)
            print("\n4. Ping and wake if offline...")
            try:
                result = client.ping_and_wake("192.168.1.100", "AA:BB:CC:DD:EE:FF")
                print(f"   Was online: {result['was_online']}")
                print(f"   WoL sent: {result['wol_sent']}")
            except PiNetAPIError as e:
                print(f"   Error: {e}")

    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Done!")