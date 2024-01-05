"""
OneEdge API Module

This module provides a class to interact with the OneEdge API.
"""
from enum import Enum
import os
import json
import time
import aiohttp
import asyncio
from src.utils.logger import create_logger

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
        """
        self.message = message
        super().__init__(message)


class OneEdgeApi:
    FOLDER_NAME = "session_data"
    FILE_NAME = "session_id.txt"

    def __init__(self, endpoint_url):
        """
        Initializes a new instance of the class.
        """
        self.endpoint_url = endpoint_url
        self._session_id = self._read_session_id()
        self._last_error = None
        self._auth_state = AuthState.NOT_AUTHENTICATED

    def _session_file_path(self):
        """
        Returns the file path of the session file.
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        folder_path = os.path.join(dir_path, self.FOLDER_NAME)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return os.path.join(folder_path, self.FILE_NAME)

    def _read_session_id(self):
        """
        Reads the session ID from the session file.

        Returns:
            str: The session ID read from the file, or None if the file does not exist or is invalid.
        """
        file_path = self._session_file_path()
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
                if file_content:
                    try:
                        data = json.loads(file_content)
                        if time.time() - data["created_at"] > 28800:
                            self._delete_session_id()
                            return None
                        return data["session_id"]
                    except json.JSONDecodeError:
                        logger.error("Error decoding JSON from the file. The file might be corrupted.")
                        self._delete_session_id()
                        return None
            file.close()
        return None

    def _write_session_id(self, session_id):
        """
        Writes the given session ID to the session file.

        Args:
            session_id (str): The session ID to be written to the file.

        Returns:
            None
        """
        file_path = self._session_file_path()
        with open(file_path, 'w', encoding='utf-8') as file:
            data = {
                "session_id": session_id,
                "created_at": time.time()
            }
            file.write(json.dumps(data, indent=4))
        file.close()

    def _delete_session_id(self):
        """
        Delete the session file.
        """
        file_path = self._session_file_path()
        if os.path.exists(file_path):
            os.remove(file_path)
        self.session_id = None
        self._auth_state = AuthState.NOT_AUTHENTICATED
        self.last_error = None

    @property
    def session_id(self):
        """Gets the session id"""
        return self._session_id

    @session_id.setter
    def session_id(self, value):
        """Sets the session id"""
        self._session_id = value
        self._write_session_id(value)
        self._auth_state = self._calculate_auth_state()

    @property
    def last_error(self):
        """Gets the last error"""
        return self._last_error

    @last_error.setter
    def last_error(self, value):
        """Sets the last error"""
        self._last_error = value
        self._auth_state = self._calculate_auth_state()

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

    def _calculate_auth_state(self):
        """
        Calculate the authentication state based on the current session ID
        and last error.
        """
        if self.session_id is not None:
            return AuthState.AUTHENTICATED
        elif self.last_error == -90041:
            return AuthState.WAITING_FOR_MFA
        elif self.last_error == -90000:
            return AuthState.NOT_AUTHENTICATED
        return AuthState.NOT_AUTHENTICATED

    async def run_command(self, command):
        """
        Run a single command.
        """
        try:
            result = await self.run_commands({
                '1': command
            })
            return result.get('1', result)
        except OneEdgeApiError as e:
            logger.exception(
                "An error occurred while making the request: %s", e)

    async def run_commands(self, cmds):
        """
        Run multiple commands asynchronously.
        """
        payload = {
            'auth': {
                'sessionId': self.session_id
            }
        }
        for key, value in cmds.items():
            payload[key] = value

        # print("payLoad: ",json.dumps(payload, indent=4))

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint_url, json=payload) as response:
                    response_data = await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"An error occurred while making the request: {e}")

        results = response_data

        if response_data is None:
            logger.error(
                "An error occurred while making the request: %s", response_data)

        # print("results:" ,json.dumps(results, indent=4))

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
        else:
            self.last_error = None

        return results

    async def run_iterated_command(self, cmd):
        """
        Run an iterated command with pagination.

        Args:
            cmd (dict): The command to be executed iteratively.

        Returns:
            list: The aggregated results from all iterations.
        """
        cmd['params'].update({
            'iterator': 'new',
            'useSearch': True,
            'limit': 2000,
            'showCount': False
        })

        results = []
        max_iterations = 100

        while max_iterations > 0:
            result = await self.run_command(cmd)
            if not result['success']:
                return results

            results.extend(result['params']['result'])
            cmd['params']['iterator'] = result['params']['iterator']

            await asyncio.sleep(0.5)
            max_iterations -= 1

        if max_iterations == 0:
            logger.error("Warning: Reached maximum iteration limit.")

        return results

    async def authenticate(self, username, password):
        """
        Authenticate with the API using provided credentials.
        """
        auth_payload = {
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
            # print(json.dumps(result, indent=4))
            auth_response = result.get('auth', {})

            if auth_response.get('success'):
                self.session_id = auth_response['params'].get('sessionId')
                self._auth_state = AuthState.AUTHENTICATED
                return True
            else:
                self.last_error = auth_response.get('errorCodes', [None])[0]
                self.auth_state = AuthState.NOT_AUTHENTICATED
                return False
        except OneEdgeApiError as error:
            logger.exception(
                "An error occurred while authenticating: %s", error)

    async def close_session(self):
        """
        Close the session with the API.
        """
        try:
            res = await self.run_command({
                "command": "session.end",
                "params": {
                    "id": self.session_id
                }
            })

            if res is None:
                logger.error("Received 'None' response when closing the session.")
                return

            if not res.get('success'):
                logger.error(f"Error closing session: {res.get('errorCodes')}")
            else:
                return res

            self._delete_session_id()
        except OneEdgeApiError as e:
            error_message = str(e) if e else "Unknown error"
            logger.exception(f"An error occurred while closing the session: {error_message}")
            raise OneEdgeApiError(f"API error occurred: {error_message}") from e


    async def verify_auth_state(self):
        """
        Check the authentication status.
        """
        try:
            if not self.session_id or self.session_id == "None" or self.session_id == "null":
                self._auth_state = AuthState.NOT_AUTHENTICATED
                return

            # Request session information to verify current state
            request = await self.run_command({"command": "session.info"})
            if request["success"]:
                self._auth_state = AuthState.AUTHENTICATED
            else:
                self.session_id = None
                self._auth_state = AuthState.NOT_AUTHENTICATED

        except OneEdgeApiError as e:
            error_message = str(e) if e else "Unknown error"
            logger.exception(f"An error occurred while verifying the authentication state: {error_message}")
            raise OneEdgeApiError(f"API error occurred: {error_message}") from e

