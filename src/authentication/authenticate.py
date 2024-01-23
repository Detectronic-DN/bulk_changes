import asyncio
from pwinput import pwinput
from src.oneEdge.oneEdgeApi import AuthState, OneEdgeApiError
from src.utils.logger import create_logger

logger = create_logger(__name__)

async def authenticate(config, api):
    """
    Authenticates with the OneEdge API.
    """
    for _ in range(3):
        if api.auth_state == AuthState.AUTHENTICATED or await attempt_authentication(config, api):
            if await verify_auth_state(api):
                logger.info("Successfully authenticated with the OneEdge API.")
                return True
            else:
                logger.error("Failed to verify authentication state.")
                return False
        else:
            logger.info("Authentication attempt failed, retrying...")
            await asyncio.sleep(5)

    logger.error("Failed to authenticate with the OneEdge API after multiple attempts.")
    return False


async def verify_auth_state(api):
    """
    Verifies the current authentication state of the API.
    """
    try:
        await api.verify_auth_state()
        if api.auth_state == AuthState.AUTHENTICATED:
            logger.info("Authentication state verified.")
            return True
    except OneEdgeApiError as e:
        logger.error(f"Error verifying authentication state: {str(e)}")
    return False

async def attempt_authentication(config, api):
    """
    Attempts to authenticate with the OneEdge API.
    """
    username = config.get("username") or input("Enter your Telit username: ")
    password = config.get("password") or pwinput(prompt="Enter your Telit password: ", mask="*")

    if not username or not password:
        logger.error("Username or password not provided.")
        return False

    try:
        if await api.authenticate(username, password):
            return await handle_auth_response(api)
    except OneEdgeApiError as e:
        logger.error(f"Authentication failed: {str(e)}")

    return False


async def handle_auth_response(api):
    """
    Handles the response after an authentication attempt.
    """
    if api.auth_state == AuthState.WAITING_FOR_MFA:
        mfa_code = input("Enter your MFA code: ")
        try:
            return await api.authenticate(api.username, mfa_code)
        except OneEdgeApiError as e:
            logger.error(f"MFA Authentication failed: {str(e)}")
    elif api.last_error == -90000:
        logger.info("Session expired. Re-authenticating...")
        api._delete_session_id()
    elif api.last_error is not None:
        logger.error("Authentication failed with error code: {}".format(api.last_error))

    return False