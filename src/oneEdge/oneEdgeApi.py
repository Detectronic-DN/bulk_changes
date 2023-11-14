"""
OneEdge API Module

This module provides a class to interact with the OneEdge API.
"""
import aiohttp
import asyncio
from cachetools import TTLCache
from src.utils.logger import create_logger
from enum import Enum


session_id_cache = TTLCache(maxsize=1, ttl=3600)
logger = create_logger(__name__)


class AuthState(Enum):
    """Authentication state"""
    AUTHENTICATED = 2
    NOT_AUTHENTICATED = 0
    WAITING_FOR_MFA = 1


class OneEdgeApiError(Exception):
    """OneEdge API Error"""

    def __init__(self, message):
        """
        Initializes a new instance of the class.

        Args:
            message (str): The message to be stored in the object.

        Returns:
            None
        """
        self.message = message
        super().__init__(message)


class OneEdgeApi:
    endpoint_url = None
    _session_id = None
    _last_error = None
    _auth_state = AuthState.NOT_AUTHENTICATED

    def __init__(self, endpoint_url):
        """
        Initializes a new instance of the class.

        Args:
            message (str): The message to be stored in the object.

        Returns:
            None
        """
        self.endpoint_url = endpoint_url
        self._session_id = session_id_cache.get('session_id')
        self._last_error = None
        self._auth_state = AuthState.NOT_AUTHENTICATED

    @property
    def session_id(self):
        """Gets the session id"""
        return session_id_cache.get('session_id', None) or self._session_id
    
    @session_id.setter
    def session_id(self, value):
        """Sets the session id"""
        session_id_cache['session_id'] = value
        self._session_id = value
        self.auth_state = self._calculate_auth_state()
        session_id_cache['session_id'] = self._session_id

    @property
    def last_error(self):
        """Gets the last error"""
        return self._last_error

    @last_error.setter
    def last_error(self, value):
        """Sets the last error"""
        self._last_error = value
        self.auth_state = self._calculate_auth_state()

    @property
    def auth_state(self):
        """Gets the authentication state"""
        return self._auth_state

    @auth_state.setter
    def auth_state(self, state):
        """Sets the authentication state"""
        if state == self._auth_state:
            return
        self._auth_state = state
    
    @classmethod
    async def create(cls, endpoint_url):
        """Class method to initialize OneEdgeApi with async operations."""
        self = OneEdgeApi(endpoint_url)
        # Perform any async initializations here if needed
        return self

    def _calculate_auth_state(self):
        """
        Calculate the authentication state based on the current session ID and last error.

        Returns:
            AuthState: The authentication state determined by the function.
        """
        if self.session_id is not None:
            return AuthState.AUTHENTICATED
        elif self.last_error == -90041:
            return AuthState.WAITING_FOR_MFA
        elif self.last_error == -90000:
            return AuthState.NOT_AUTHENTICATED
        return AuthState.NOT_AUTHENTICATED

    async def verify_auth_state(self):
        """Check the authentication status."""
        result = await self.run_command({
            "command": "session.info"
        })
        if result["success"]:
            self.session_id = result["params"]["id"]
        else:
            self.session_id = None
            self.auth_state = AuthState.NOT_AUTHENTICATED

    async def login(self, username, password):
        """
        Login to the OneEdge API.

        Args:
            username (str): The username to be used for authentication.
            password (str): The password to be used for authentication.

        Returns:
            bool: True if login was successful, otherwise False.
        """
        result = await self.run_commands({
            "auth": {
                "command": "api.authenticate",
                "params": {
                    "username": username,
                    "password": password
                }
            }
        })
        if result['auth']['success'] and 'sessionId' in result['auth']['params']:
            self.session_id = result['auth']['params']['sessionId']
            return True
        else:
            self.session_id = None
            self.auth_state = AuthState.NOT_AUTHENTICATED
            return False    


    async def run_commands(self, cmds):
        """
        Run multiple commands asynchronously.

        Args:
            cmds (dict): The commands to be executed.

        Returns:
            dict: The results of the commands.
        """
        payload = {
            'auth': {
                'sessionId': self.session_id
            }
        }

        for key, value in cmds.items():
            payload[key] = value

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint_url, json=payload) as response:
                response_data = await response.json()

        results = response_data

        if 'success' in response_data and not response_data['success']:
            for cmd_key in cmds:
                results[cmd_key] = {
                    'success': False,
                    'errorCodes': response_data['errorCodes']
                }
        else:
            results['success'] = True
            results['errorCodes'] = []

        if results['errorCodes']:
            self.last_error = results['errorCodes'][0]
            self.auth_state = self._calculate_auth_state()
            if self.auth_state == AuthState.WAITING_FOR_MFA:
                raise OneEdgeApiError("API error occurred: -90041")
            elif results['errorCodes'][0] == -90005:
                await asyncio.sleep(10)
                raise OneEdgeApiError("API error occurred: -90005")
        else:
            self.last_error = None

        return results

    async def clear_session(self):
        """
        Clear the session.
        """
        session_id_cache['session_id'] = None
        self.session_id = None
        self.auth_state = AuthState.NOT_AUTHENTICATED
        self.last_error = None

    async def run_command(self, command):
        """
        Run a single command.
        """
        result = await self.run_commands({
            '1': command
        })
        return result['1'] if '1' in result else result

    async def run_iterated_command(self, cmd, loop_protection_limit=100, wait_time=0.5):
        """
        Run an iterated command with pagination support.
        
        Args:
            cmd (dict): Command to run with parameters.
            loop_protection_limit (int): Max number of iterations to protect against infinite loops.
            wait_time (float): Time to wait between iterations to respect API rate limits.

        Returns:
            list: Accumulated results from iterated command runs.
        """
        cmd['params']['iterator'] = 'new'
        cmd['params']['useSearch'] = True
        cmd['params']['limit'] = 2000
        cmd['params']['showCount'] = False

        results = []
        loop_protection = loop_protection_limit

        while loop_protection > 0:
            result = await self.run_command(cmd)
            if not result['success']:
                logger.error(f"Iterated command failed: {result.get('error')}")
                break

            batch_results = result['params'].get('result', [])
            if isinstance(batch_results, list):
                results.extend(batch_results)
            else:
                logger.error('Received non-list batch_results from API')
                break

            next_iterator = result['params'].get('iterator')
            if next_iterator and next_iterator != 'new':
                cmd['params']['iterator'] = next_iterator
            else:
                logger.info('No more results to iterate over, exiting.')
                break

            await asyncio.sleep(wait_time)
            loop_protection -= 1

        if loop_protection == 0:
            logger.warning(
                "Loop protection fired - the command may not have retrieved all results.")

        return results

    async def close_session(self):
        """
        Close the session.
        This method sends a command to end the session and sets the session ID to None.

        Returns:
            The result of running the command.
        """
        result = await self.run_command({
            "command": "session.end",
            "params": {
                "id": self.session_id
            }
        })
        self.session_id = None
        self.auth_state = AuthState.NOT_AUTHENTICATED
        self.last_error = None
        return result