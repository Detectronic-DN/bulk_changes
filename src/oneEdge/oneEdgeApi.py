"""
OneEdge API Module

This module provides a class to interact with the OneEdge API.
"""
import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
from cachetools import TTLCache

from src.logger.logger import Logger

logger = Logger(__name__)


class AuthState(Enum):
    """Authentication state"""
    AUTHENTICATED = 2
    NOT_AUTHENTICATED = 0
    WAITING_FOR_MFA = 1


class OneEdgeApiError(Exception):
    """OneEdge API Error"""

    def __init__(self, message: str):
        """
        Initializes a new instance of the class.

        Args:
            message (str): The error message.
        """
        self.message = message
        super().__init__(message)


class OneEdgeApi:
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    ITERATION_LIMIT: int = 100

    def __init__(self, endpoint_url: str):
        """
        Initializes a new instance of the OneEdgeApi class.

        Args:
            endpoint_url (str): The URL of the OneEdge API endpoint.
        """
        self.endpoint_url: str = endpoint_url
        self._session_cache: TTLCache = TTLCache(maxsize=1, ttl=28800)
        self._last_error: Optional[int] = None
        self._auth_state: AuthState = AuthState.NOT_AUTHENTICATED
        self.username: str = None

    @property
    def session_id(self) -> Optional[str]:
        """Gets the session id"""
        return self._session_cache.get('session_id')

    @session_id.setter
    def session_id(self, value: Optional[str]) -> None:
        """Sets the session id"""
        self._session_cache['session_id'] = value
        self._auth_state = self._calculate_auth_state()

    @property
    def last_error(self) -> Optional[int]:
        """Gets the last error"""
        return self._last_error

    @last_error.setter
    def last_error(self, value: Optional[int]) -> None:
        """Sets the last error"""
        self._last_error = value
        self._auth_state = self._calculate_auth_state()

    @property
    def auth_state(self) -> AuthState:
        """Gets the authentication state"""
        return self._auth_state

    @auth_state.setter
    def auth_state(self, state: AuthState) -> None:
        """Sets the authentication state"""
        if state != self._auth_state:
            self._auth_state = state

    def _calculate_auth_state(self) -> AuthState:
        """
        Calculate the authentication state based on the current session ID
        and last error.

        Returns:
            AuthState: The calculated authentication state.
        """
        if self.session_id is not None:
            return AuthState.AUTHENTICATED
        if self.last_error == -90041:
            return AuthState.WAITING_FOR_MFA
        if self.last_error == -90000:
            return AuthState.NOT_AUTHENTICATED
        return AuthState.NOT_AUTHENTICATED

    async def run_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single command.

        Args:
            command (Dict[str, Any]): The command to be executed.

        Returns:
            Dict[str, Any]: The result of the command.

        Raises:
            OneEdgeApiError: If an error occurs while making the request.
        """
        try:
            result = await self.run_commands({'1': command})
            return result.get('1', result)
        except OneEdgeApiError as e:
            logger.exception("An error occurred while making the request", error=str(e))
            raise

    async def run_commands(self, cmds: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run multiple commands asynchronously.

        Args:
            cmds (Dict[str, Dict[str, Any]]): The commands to be executed.

        Returns:
            Dict[str, Any]: The results of the commands.

        Raises:
            OneEdgeApiError: If failed to receive a response from the API.
        """
        payload: Dict[str, Any] = {'auth': {'sessionId': self.session_id}}
        payload.update(cmds)

        response_data: Optional[Dict[str, Any]] = None
        for retry_count in range(self.MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.endpoint_url, json=payload) as response:
                        response_data = await response.json()
                        break
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error("An error occurred while making the request",
                             error=str(e), retry_count=retry_count)
                if retry_count < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    logger.error("Failed to make the request after multiple retries",
                                 max_retries=self.MAX_RETRIES)

        if response_data is None:
            logger.error("Failed to receive a response")
            raise OneEdgeApiError("Failed to receive a response from the API.")

        return self._process_response(response_data, cmds)

    def _process_response(self, response_data: Dict[str, Any], cmds: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the API response.

        Args:
            response_data (Dict[str, Any]): The response data from the API.
            cmds (Dict[str, Any]): The original commands sent to the API.

        Returns:
            Dict[str, Any]: The processed results.
        """
        results: Dict[str, Any] = response_data if response_data else {}

        if 'success' in response_data and not response_data['success']:
            for cmd_key in cmds:
                results[cmd_key] = {'success': False, 'errorCodes': response_data['errorCodes']}
        else:
            results['success'] = True
            results['errorCodes'] = []

        if results['errorCodes']:
            self.last_error = results['errorCodes'][0]
        else:
            self.last_error = None

        return results

    async def run_iterated_command(self, cmd: Dict[str, Any]) -> List[Any]:
        """
        Run an iterated command with pagination.

        Args:
            cmd (Dict[str, Any]): The command to be executed iteratively.

        Returns:
            List[Any]: The aggregated results from all iterations.
        """
        cmd['params'].update({
            'iterator': 'new',
            'useSearch': True,
            'limit': 2000,
            'showCount': False
        })

        results: List[Any] = []
        for iteration in range(self.ITERATION_LIMIT):
            result = await self.run_command(cmd)
            if not result['success']:
                logger.warning("Iterated command unsuccessful", iteration=iteration)
                return results

            results.extend(result['params']['result'])
            cmd['params']['iterator'] = result['params']['iterator']

            await asyncio.sleep(0.5)

        logger.warning("Reached maximum iteration limit", limit=self.ITERATION_LIMIT)
        return results

    async def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with the API using provided credentials.

        Args:
            username (str): The username.
            password (str): The password.

        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        auth_payload: Dict[str, Dict[str, Any]] = {
            "auth": {
                "command": "api.authenticate",
                "params": {
                    "username": username,
                    "password": password
                }
            }
        }

        try:
            result = await self.run_commands(auth_payload)
            auth_response = result.get('auth', {})

            if auth_response.get('success'):
                self.session_id = auth_response['params'].get('sessionId')
                self.auth_state = AuthState.AUTHENTICATED
                logger.info("Authentication successful", username=username)
                return True
            else:
                self.last_error = auth_response.get('errorCodes', [None])[0]
                self.auth_state = AuthState.NOT_AUTHENTICATED
                return False
        except OneEdgeApiError as error:
            logger.exception("An error occurred while authenticating", error=str(error))
            return False

    async def close_session(self) -> Optional[Dict[str, Any]]:
        """
        Close the session with the API.

        Returns:
            Optional[Dict[str, Any]]: The response from the API, or None if an error occurred.

        Raises:
            OneEdgeApiError: If an error occurs while closing the session.
        """
        try:
            res = await self.run_command({
                "command": "session.end",
                "params": {"id": self.session_id}
            })

            if res is None:
                logger.error("Received 'None' response when closing the session")
                return None

            if not res.get('success'):
                logger.error("Error closing session", error_codes=res.get('errorCodes'))
            else:
                logger.info("Session closed successfully")
                return res
        except OneEdgeApiError as e:
            logger.exception("An error occurred while closing the session", error=str(e))
            raise

    async def verify_auth_state(self) -> None:
        """
        Check the authentication status.

        Raises:
            OneEdgeApiError: If an error occurs while verifying the authentication state.
        """
        try:
            if not self.session_id or self.session_id in ["None", "null"]:
                self.session_id = None
                self.auth_state = AuthState.NOT_AUTHENTICATED
                logger.info("Auth state set to NOT_AUTHENTICATED due to invalid session ID")
                return

            request = await self.run_command({"command": "session.info"})
            if request["success"]:
                self.auth_state = AuthState.AUTHENTICATED
                logger.info("Auth state verified as AUTHENTICATED")
            else:
                self.session_id = None
                self.auth_state = AuthState.NOT_AUTHENTICATED
                logger.warning("Auth state set to NOT_AUTHENTICATED after failed verification")
        except OneEdgeApiError as e:
            logger.exception("An error occurred while verifying the authentication state", error=str(e))
            raise

    async def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticates the user with the OneEdge API.

        Args:
            username (str): The username.
            password (str): The password.

        Returns:
            bool: True if authentication was successful, False otherwise.
        """
        for attempt in range(self.MAX_RETRIES):
            if self.auth_state == AuthState.AUTHENTICATED or await self._attempt_authentication(username, password):
                if await self._verify_auth_state():
                    logger.info("Successfully authenticated with the OneEdge API", username=username)
                    return True
                else:
                    logger.error("Failed to verify authentication state", username=username)
                    return False
            else:
                logger.warning("Authentication attempt failed, retrying", attempt=attempt + 1)
                await asyncio.sleep(self.RETRY_DELAY)
        logger.error("Failed to authenticate with the OneEdge API after multiple attempts", username=username)
        return False

    async def _verify_auth_state(self) -> bool:
        """
        Verifies the current authentication state of the API.

        Returns:
            bool: True if authentication state is verified, False otherwise.
        """
        try:
            await self.verify_auth_state()
            if self.auth_state == AuthState.AUTHENTICATED:
                logger.info("Authentication state verified")
                return True
        except OneEdgeApiError as e:
            logger.error("Error verifying authentication state", error=str(e))
        return False

    async def _attempt_authentication(self, username: str, password: str) -> bool:
        """
        Attempts to authenticate with the OneEdge API.

        Args:
            username (str): The username.
            password (str): The password.

        Returns:
            bool: True if authentication attempt was successful, False otherwise.
        """
        if not username or not password:
            logger.error("Username or password not provided")
            return False
        try:
            return await self.authenticate(username, password)
        except OneEdgeApiError as e:
            logger.error("Authentication failed", error=str(e))
        return False

    async def _handle_auth_response(self) -> bool:
        """
        Handles the response after an authentication attempt.

        Returns:
            bool: True if the response was handled successfully, False otherwise.
        """
        if self.auth_state == AuthState.WAITING_FOR_MFA:
            mfa_code: str = input("Enter your MFA code: ")
            try:
                return await self.authenticate(self.username, mfa_code)
            except OneEdgeApiError as e:
                logger.error("MFA Authentication failed", error=str(e))
        elif self.last_error == -90000:
            logger.info("Session expired. Re-authenticating...")
            self.session_id = None
        elif self.last_error is not None:
            logger.error("Authentication failed", error_code=self.last_error)
        return False
