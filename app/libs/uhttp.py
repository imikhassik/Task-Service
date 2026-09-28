"""
HTTP/HTTPS request processing


Works on tope of HTTPX library adding the following functions:
    - DNS request logging
    - response logging
    - request to IP address with Host header
    - set default User-Agent
"""
import logging
import httpx
import socket
import random
from typing import Optional, Dict, Any, Union, List, Tuple
from enum import Enum


# Function for retrieving session_id from context
from .session_context import get_session_id_str


__version__ = '1.0.1'


# Library constants
DEFAULT_TIMEOUT = 30.0
DEFAULT_USER_AGENT = "EiticaPuzzle/1.0"
DEFAULT_LOGGER_NAME = "HTTPClient"



class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"



class HTTPClient:
    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        log_dns: bool = False,
        log_responses: bool = False,
        resolve_ip: bool = False,
        verify_ssl: bool = True,
    ):
        """
        HTTP client initialization.


        :param timeout: Request timeout in seconds
        :param user_agent: User-Agent for requests
        :param log_dns: Log DNS requests
        :param log_responses: Log server responses
        :param resolve_ip: Use the IP address from DNS instead of the domain
        :param verify_ssl: Verify SSL certificates
        """
        self.timeout = timeout
        self.user_agent = user_agent
        self.log_dns = log_dns
        self.log_responses = log_responses
        self.resolve_ip = resolve_ip
        self.verify_ssl = verify_ssl
        self._client = None  # Store the client here to properly close all connections on exit


        if self.log_dns or self.log_responses:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(DEFAULT_LOGGER_NAME)
            self.logger.setLevel(logging.INFO)


    def _log(self, level):
        if self.log_dns or self.log_responses:
            self.logger.setLevel(level)


    def log_info(self):
        self._log(logging.INFO)


    def log_debug(self):
        self._log(logging.DEBUG)


    def _resolve_domain_to_ip(self, domain: str) -> Optional[Tuple[str, List[str]]]:
        """
        Resolves a domain name to IP address(es), returns a randomly selected IP and a list of all IPs.


        :param domain: Domain name to resolve
        :return: Tuple of (selected IP, list of all IPs) or None on error
        """
        try:
            # Get all IPv4 addresses for the domain
            addr_info = socket.getaddrinfo(domain, None, family=socket.AF_INET, proto=socket.IPPROTO_TCP)
            ip_addresses = list({info[4][0] for info in addr_info})  # Unique IPs
            
            if not ip_addresses:
                if self.log_dns:
                    self.logger.warning(f"No IP addresses found for domain: {domain}")
                return None
            
            # Select a random IP from the list
            selected_ip = random.choice(ip_addresses) # NOQA: S311
            
            if self.log_dns:
                self.logger.info(f"DNS lookup: {domain} -> {ip_addresses} (selected: {selected_ip})")
            
            return selected_ip, ip_addresses
        except Exception as e:
            if self.log_dns:
                self.logger.error(f"DNS lookup failed for {domain}: {e}")
            return None


    def _add_session_header(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """
        Adds X-Session-ID to the headers if it is available.


        Args:
            headers: Original headers


        Returns:
            Dict[str, str]: Headers with the added X-Session-ID
        """
        if headers is None:
            headers = {}


        # Do not overwrite it if the header was explicitly set already
        if 'X-Session-ID' not in headers:
            session_id = get_session_id_str()
            if session_id:
                headers['X-Session-ID'] = session_id


        return headers



    async def _get_client(self) -> httpx.AsyncClient:
        """Gets or creates the client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        return self._client


    async def close(self):
        """Explicitly closes the client"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


    async def _make_request(
        self,
        method: HTTPMethod,
        url: str,
        endpoint: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Union[Dict[str, Any], List[Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Universal method for making HTTP requests.


        :param method: HTTP method
        :param url: Base URL
        :param endpoint: Endpoint (will be combined with the URL)
        :param params: Request parameters
        :param json: Data to send in JSON format
        :param headers: Request headers
        :param kwargs: Additional parameters for httpx
        :return: httpx response object
        """
        # Combine URL and endpoint
        full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else url


        # Prepare headers
        final_headers = headers or {}
        # Add a header for end-to-end session tracking
        final_headers = self._add_session_header( final_headers )
        final_headers.setdefault("User-Agent", self.user_agent)


        # Settings for using an IP from DNS
        if self.resolve_ip:
            try:
                from urllib.parse import urlparse


                parsed_url = urlparse(full_url)
                domain = parsed_url.hostname


                if domain:
                    # Get IP address(es)
                    resolution = self._resolve_domain_to_ip(domain)
                    if resolution:
                        ip, all_ips = resolution
                        
                        # Modify URL and headers
                        full_url = full_url.replace(domain, ip)
                        final_headers["Host"] = domain
                        
                        if self.log_dns:
                            self.logger.info(f"Using IP: {ip} from available: {all_ips} for domain: {domain}")
            except Exception as e:
                if self.log_dns:
                    self.logger.error(f"DNS resolution failed: {e}")


        # Get the client through _get_client()
        client = await self._get_client()


        try:
            response = await client.request(
                method=method.value,
                url=full_url,
                params=params,
                json=json,
                headers=final_headers,
                **kwargs,
            )


            if self.log_responses:
                self.logger.info(
                    f"Response: {method.value} {full_url} - {response.status_code}"
                )
                # Attempt to parse JSON from the response body
                try:
                    parsed_json = response.json()
                    self.logger.debug(f"Response JSON: {parsed_json}")  # If JSON is valid, log it
                except Exception:
                    # In all other cases, inspect the response as-is
                    if response.content:
                        self.logger.debug(f"Response content: {response.text}")


            return response


        except Exception as e:
            # Log request errors if needed
            if self.log_responses:
                self.logger.error(f"Request failed: {str(e)}")
            raise



    async def get(
        self,
        url: str,
        endpoint: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request(
            HTTPMethod.GET, url, endpoint, params=params, headers=headers, **kwargs
        )


    async def post(
        self,
        url: str,
        endpoint: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Union[Dict[str, Any], List[Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request(
            HTTPMethod.POST,
            url,
            endpoint,
            params=params,
            json=json,
            headers=headers,
            **kwargs,
        )


    async def put(
        self,
        url: str,
        endpoint: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Union[Dict[str, Any], List[Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request(
            HTTPMethod.PUT,
            url,
            endpoint,
            params=params,
            json=json,
            headers=headers,
            **kwargs,
        )


    async def delete(
        self,
        url: str,
        endpoint: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request(
            HTTPMethod.DELETE, url, endpoint, params=params, headers=headers, **kwargs
        )


    async def patch(
        self,
        url: str,
        endpoint: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Union[Dict[str, Any], List[Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._make_request(
            HTTPMethod.PATCH,
            url,
            endpoint,
            params=params,
            json=json,
            headers=headers,
            **kwargs,
        )