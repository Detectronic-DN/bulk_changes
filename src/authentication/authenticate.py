import os
import asyncio
import pyotp
from pwinput import pwinput
from src.oneEdge.oneEdgeApi import OneEdgeApiError, AuthState
from src.utils.logger import create_logger, log_info, log_error
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), "/home/dinesh_detectronic/telit/config/.env.development")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

CONFIG = {
    "username": os.getenv("TELIT_USERNAME"),
    "password": os.getenv("TELIT_PASSWORD"),
    "shared_secret": os.getenv("TELIT_MFA"),
}

if not CONFIG["username"] or not CONFIG["password"]:
    CONFIG["username"] = input("Enter your Telit username: ")
    CONFIG["password"] = pwinput(prompt= "Enter your Telit password: ", mask="*")

logger = create_logger(__name__)

async def authenticate(api):
    """
    Authenticate the OneEdge API.
    """
    max_retries = 3
    retry_delay = 5

    for _ in range(max_retries):
        if api.auth_state == AuthState.AUTHENTICATED:
            break

        if not CONFIG["username"] or not CONFIG["password"]:
            logger.error(
                "Invalid username or password. Please check the configuration.")
            break  

        try:
            await authenticate_with_username_password(api, logger)
            if api.auth_state == AuthState.AUTHENTICATED:
                break  # Break after successful authentication
        except OneEdgeApiError as error:
            logger.error("Authentication failed: %s", str(error))
            if str(error) == "API error occurred: -90041":
                if CONFIG["shared_secret"] is not None:
                    mfa_code = pyotp.TOTP(CONFIG["shared_secret"]).now()
                else:
                    mfa_code = input("Enter your MFA code: ")

                await authenticate_with_mfa(api, logger, mfa_code)
                if api.auth_state == AuthState.AUTHENTICATED:
                    break  # Break after successful MFA

        await asyncio.sleep(retry_delay)  # Wait before retrying


async def authenticate_with_username_password(api, logger):
    """
    Authenticate with username and password.
    """
    username = CONFIG["username"]
    password = CONFIG["password"]

    try:
        await api.login(username, password)
        log_info(logger, "Authenticated")
    except OneEdgeApiError as error:
        raise error


async def authenticate_with_mfa(api, logger, mfa_code):
    """
    Authenticate with multi-factor authentication (MFA).
    """
    try:
        await api.login(CONFIG["username"], mfa_code)
        log_info(logger, "Authenticated with MFA")
    except OneEdgeApiError as error:
        log_error(logger, f"Authentication failed: {error}")

