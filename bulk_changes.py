import argparse
import asyncio
from src.authentication.authenticate import authenticate
from src.oneEdge.oneEdgeApi import OneEdgeApi
from src.utils.logger import create_logger
from src.bulk_changes.creating_commands import *
from src.bulk_changes.reading_file import *
from typing import List, Optional, Dict, Any


logger = create_logger(__name__)

config = {
    "API_URL": "https://api-de.devicewise.com/api"
}


async def get_user_choice() -> str:
    """
    Prompts the user to choose an option and returns the choice as a string.

    Returns:
        str: The user's choice.
    """
    print("\nPlease choose an option:")
    options: List[str] = [
        "1. Adding tags to a list of IMEIs",
        "2. Change device profile to IMEIs",
        "3. Change Thing_def to IMEIs",
        "4. Add attributes settings to all IMEIs",
        "5. Undeploy or change data destination for removed loggers",
        "q. Quit"
    ]
    for option in options:
        print(option)
    choice: str = input("Enter your choice: ")
    return choice


async def add_tags(file_path: str) -> Optional[str]:
    """
    Adds tags to a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        Optional[str]: The commands in JSON format, or None if there was an error.
    """
    tag_names_input = input("Enter the tag names separated by commas: ")
    tag_names = [tag.strip() for tag in tag_names_input.split(',')]

    try:
        print("Reading the file...")
        imeis = read_imeis(file_path)
        print("Creating commands...")
        commands_json = await create_commands_tags(imeis, tag_names)
        return commands_json
    except Exception as e:
        logger.error(f"Error processing option 1: {e}")
        return None


async def change_device_profile(file_path: str) -> Optional[Dict[str, str]]:
    """Change the device profile.

    Args:
        file_path (str): The path to the file containing the IMEIs.

    Returns:
        dict: The commands JSON if successful, None otherwise.
    """
    profiles: Dict[str, str] = get_profile_id()
    profile_name: str = input("Enter the profile name: ")
    profile_id: Optional[str] = profiles.get(profile_name)

    if not profile_id:
        print("Error: Profile name not found.")
        return None
    try:
        print("Reading the file...")
        imeis = read_imeis(file_path)
        print("Creating commands...")
        commands_json = await create_commands_device_profile(imeis, profile_id)
        return commands_json
    except Exception as e:
        logger.error(f"Error processing option 2: {e}")
        return None


async def change_thing_def(file_path: str) -> Optional[Dict[str, str]]:
    """
    Change the thing definition based on the given file path.

    Args:
        file_path (str): The path to the file containing the IMEIs.

    Returns:
        Optional[Dict[str, str]]: The commands JSON if successful, None otherwise.
    """
    thing_defs: Dict[str, str] = get_thing_def_key()
    thing_name: str = input("Enter the thing name: ")
    thing_def_key: Optional[str] = thing_defs.get(thing_name)

    if thing_def_key:
        try:
            print("Reading the file...")
            imeis = read_imeis(file_path)
            print("Creating commands...")
            commands_json = await create_commands_device_profile(imeis, thing_def_key)
            return commands_json
        except Exception as e:
            logger.error(f"Error processing option 3: {e}")
    else:
        print("Error: Thing name not found.")
    return None


async def add_settings(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Reads the file at the given path and creates commands based on the IMEIs and settings.

    Args:
        file_path (str): The path of the file to read.

    Returns:
        Optional[Dict[str, Any]]: The commands as a JSON object, or None if there was an error.
    """
    try:
        print("Reading the file...")
        imeis, settings = read_imei_and_setting(file_path)
        print("Creating commands...")
        commands_json = await create_commands_settings(imeis, settings)
        return commands_json
    except Exception as e:
        logger.error(f"Error processing option 4: {e}")
        return None


async def undeploy(file_path: str) -> Optional[str]:
    """
    Read the file at the given `file_path` and create undeploy commands
    based on the IMEIs found in the file.

    Args:
        file_path: The path to the file containing the IMEIs.

    Returns:
        A JSON string containing the undeploy commands, or None if there
        was an error processing the file.
    """
    try:
        logger.info("Reading the file...")
        imeis = read_imeis(file_path)
        logger.info("Creating commands...")
        commands_json = await create_commands_undeploy(imeis)
        return commands_json
    except Exception as e:
        logger.error(f"Error processing option 5: {e}")
        return None


async def remove_tags(file_path: str) -> Optional[List[str]]:
    """
    Remove tags from a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        List[str]: The commands in JSON format to remove the tags, or None if there was an error.
    """
    try:
        tag_names_input = input("Enter the tag names separated by commas: ")
        tag_names = [tag.strip() for tag in tag_names_input.split(',')]
        logger.info("Reading the file...")
        imeis = read_imeis(file_path)
        logger.info("Creating commands...")
        commands_json = await create_commands_delete_tag(imeis, tag_names)
        return commands_json
    except Exception as e:
        logger.error(f"Error processing option 6: {e}")
        return None


async def publish_commands(api: OneEdgeApi, commands_json: Dict[str, Any]) -> None:
    """
    Publishes commands using the OneEdge API.

    Args:
        api (OneEdgeApi): The authenticated API object.
        commands_json (Dict[str, Any]): A dictionary representing the commands to be published.

    Returns:
        None
    """
    try:
        print("Publishing commands...")
        results: Dict[str, Any] = await api.run_commands(commands_json)
        return results
    except Exception as e:
        logger.error(f"Error publishing commands: {e}")


async def close_api_session(api: Any) -> None:
    """
    Close the API session.

    Args:
        api (Any): The API object.

    Raises:
        Exception: If there is an error closing the session.
    """
    try:
        session: Dict[str, Dict[str, bool]] = await api.close_session()
        if session.get('success'):
            logger.info("Session closed successfully.")
        else:
            logger.warning("Failed to close session properly.")
    except Exception as e:
        logger.error(f"Error closing session: {e}")


async def authenticate_and_verify(config, api):
    """
    Authenticate and verify the API session.

    Args:
        config: Configuration data needed for authentication.
        api: API client object to authenticate and verify.

    Returns:
        bool: True if the session is authenticated and verified, False otherwise.
    """
    if not api.session_id:
        logger.info("Authenticating to telit")
        is_authenticated = await authenticate(config, api)
        if not is_authenticated:
            logger.error("Authentication failed")
            return False
    else:
        await api.verify_auth_state()
        logger.info("Session already authenticated")
    return True


async def process_user_choice(choice, file_path, api):
    """
    Process user choice and execute corresponding function.
    """
    choice_to_function = {
        '1': add_tags,
        '2': change_device_profile,
        '3': change_thing_def,
        '4': add_settings,
        '5': undeploy,
        '6': remove_tags,
    }

    if choice not in choice_to_function:
        logger.warning("Invalid choice. Please enter a valid number.")
        return

    try:
        commands_json = await choice_to_function[choice](file_path)
        if commands_json:
            results = await publish_commands(api, commands_json)
            if results.get('success'):
                logger.info("Successfully updated.")
            else:
                logger.error("Failed to update")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


async def main() -> None:
    """
    Process a file and generate commands based on user choices.
    """
    parser = argparse.ArgumentParser(
        description='Process a file and generate commands.')
    parser.add_argument(
        'file_path', help='The path to the file to be processed')
    args = parser.parse_args()

    if not config["API_URL"]:
        logger.error("API_URL environment variable is not set.")
        return

    api = OneEdgeApi(config["API_URL"])

    if not await authenticate_and_verify(config, api):
        return

    logger.info("Connected!")

    try:
        while True:
            try:
                choice = await asyncio.wait_for(get_user_choice(), timeout=10)
            except asyncio.TimeoutError:
                logger.info("No input received. Exiting the program.")
                break

            if choice == 'q':
                logger.info("Closing the session and exiting the program.")
                break

            await process_user_choice(choice, args.file_path, api)
    finally:
        await close_api_session(api)
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
