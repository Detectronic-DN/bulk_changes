import os
import asyncio
from pwinput import pwinput
from src.oneEdge.oneEdgeApi import AuthState, OneEdgeApiError
from src.utils.logger import create_logger
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "/home/dinesh_detectronic/telit/config/.env.development")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

logger = create_logger(__name__)

CONFIG = {
    "username": os.getenv("TELIT_USERNAME"),
    "password": os.getenv("TELIT_PASSWORD"),
    "shared_secret": os.getenv("TELIT_MFA"),
}

async def authenticate(api):
    """
    Authenticates with the OneEdge API.
    """
    max_attempts = 3
    attempts = 0
    delay = 5
    mfa_code = None
    if api.auth_state == AuthState.AUTHENTICATED:
        await api.verify_auth_state()
        
    while api.auth_state != AuthState.AUTHENTICATED and attempts < max_attempts:
        if api.auth_state == AuthState.NOT_AUTHENTICATED:

            if not CONFIG["username"] or not CONFIG["password"]:
                CONFIG["username"] = input("Enter your Telit username: ")
                CONFIG["password"] = pwinput(prompt= "Enter your Telit password: ", mask="*")

            username = CONFIG["username"]
            password = CONFIG["password"]

            if not username or not password:
                logger.error("Username or password not provided.")
                break
            try:
                result = await api.authenticate(username, password)
                await asyncio.sleep(1)
                if not result:
                    if api.last_error == -90041:
                        api.auth_state = AuthState.WAITING_FOR_MFA
                        logger.info("MFA authentication required.")
                        if not mfa_code:
                            mfa_code = input("Enter your MFA code: ")
                        try:
                            await asyncio.sleep(2)
                            await api.authenticate(username, mfa_code)
                            await asyncio.sleep(1)
                        except OneEdgeApiError as e:
                            logger.error(f"Authentication failed: %s", str(e))
                            continue
                    elif api.last_error == -90000:
                        logger.info("Session expired. Re-authenticating...")
                        api._delete_session_id()
                        continue
                    else:
                        logger.error("Authentication failed.")
                        break
            except OneEdgeApiError as e:
                logger.error(f"Authentication failed: %s", str(e))
                break
            
        attempts += 1
        await asyncio.sleep(delay)

    if api.auth_state == AuthState.AUTHENTICATED:
        logger.info("Successfully authenticated with the OneEdge API.")
    else:
        logger.error("Failed to authenticate with the OneEdge API.")
