import os
import argparse
import asyncio
import pwinput
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from src.bulk_changes.create_commands import (
    create_command_delete_things,
    create_commands_tags,
    create_commands_settings,
    create_commands_undeploy,
    create_commands_thing_def,
    create_commands_device_profile,
    create_commands_delete_tag,
)
from src.bulk_changes.get_data import read_imei_and_setting, read_imei_only
from src.logger.logger import Logger
from src.OneEdge.OneEdgeAPI import OneEdgeApi, OneEdgeApiError
from src.bulk_changes.undeploy_process import undeploy_process

logger = Logger(__name__)
load_dotenv("config/.env")


async def add_settings(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Reads IMEI numbers and settings from a file and creates commands to update settings.

    :param file_path: Path to the input file containing IMEI numbers and settings.
    :return: A dictionary containing the created commands, or None if an error occurs.
    """
    try:
        logger.info("Reading the file...")
        ids, settings = await read_imei_and_setting(file_path)
        logger.info(f"Read {len(ids)} devices from the file.")
        logger.info("Creating commands...")
        commands_json = await create_commands_settings(ids, settings)
        logger.info(f"Created commands for {len(commands_json)} devices.")
        return commands_json
    except Exception as e:
        logger.error(f"Error processing add settings: {e}")
        return None


async def apply_device_profile(
    file_path: str, profile_id: str
) -> Optional[Dict[str, Any]]:
    """
    Reads IMEI numbers from a file and creates commands to apply a device profile.

    :param file_path: Path to the input file containing IMEI numbers.
    :param profile_id: The ID of the profile to apply.
    :return: A dictionary containing the created commands, or None if an error occurs.
    """
    try:
        logger.info("Reading the file...")
        ids = await read_imei_only(file_path)
        logger.info(f"Read {len(ids)} devices from the file.")
        logger.info("Creating commands...")
        commands_json = await create_commands_device_profile(ids, profile_id)
        logger.info(f"Created commands for {len(commands_json)} devices.")
        return commands_json
    except Exception as e:
        logger.error(f"Error processing apply device profile: {e}")
        return None


async def add_tags(file_path: str, tags: List[str]) -> Optional[Dict[str, Any]]:
    """
    Reads IMEI numbers from a file and creates commands to add tags to devices.

    :param file_path: Path to the input file containing IMEI numbers.
    :param tags: List of tags to add to the devices.
    :return: A dictionary containing the created commands, or None if an error occurs.
    """
    try:
        logger.info("Reading the file...")
        ids = await read_imei_only(file_path)
        logger.info(f"Read {len(ids)} devices from the file.")
        logger.info("Creating commands...")
        commands_json = await create_commands_tags(ids, tags)
        logger.info(f"Created commands for {len(commands_json)} devices.")
        return commands_json
    except Exception as e:
        logger.error(f"Error processing add tags: {e}")
        return None


async def change_thing_definition(
    file_path: str, thing_key: str
) -> Optional[Dict[str, Any]]:
    """
    Reads IMEI numbers from a file and creates commands to change the thing definition.

    :param file_path: Path to the input file containing IMEI numbers.
    :param thing_key: The new thing definition key to apply.
    :return: A dictionary containing the created commands, or None if an error occurs.
    """
    try:
        logger.info("Reading the file...")
        ids = await read_imei_only(file_path)
        logger.info(f"Read {len(ids)} devices from the file.")
        logger.info("Creating commands...")
        commands_json = await create_commands_thing_def(ids, thing_key)
        logger.info(f"Created commands for {len(commands_json)} devices.")
        return commands_json
    except Exception as e:
        logger.error(f"Error processing change thing definition: {e}")
        return None


async def undeploy_devices(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Reads IMEI numbers from a file, undeploy devices, and creates commands to undeploy devices in OneEdge.

    :param file_path: Path to the input file containing IMEI numbers.
    :return: A dictionary containing the created commands, or None if an error occurs.
    """
    try:
        logger.info("Reading the file...")
        ids = await read_imei_only(file_path)
        logger.info(f"Read {len(ids)} devices from the file.")

        # Perform the undeploy process
        logger.info("Starting undeploy process...")
        undeploy_process(ids)
        logger.info("Undeploy process completed.")

        logger.info("Creating OneEdge undeploy commands...")
        commands_json = await create_commands_undeploy(ids)
        logger.info(f"Created commands for {len(commands_json)} devices.")
        return commands_json
    except Exception as e:
        logger.error(f"Error processing undeploy devices: {e}")
        return None


async def delete_tags(file_path: str, tags: List[str]) -> Optional[Dict[str, Any]]:
    """
    Reads IMEI numbers from a file and creates commands to delete tags from devices.

    :param file_path: Path to the input file containing IMEI numbers.
    :param tags: List of tags to delete from the devices.
    :return: A dictionary containing the created commands, or None if an error occurs.
    """
    try:
        logger.info("Reading the file...")
        ids = await read_imei_only(file_path)
        logger.info(f"Read {len(ids)} devices from the file.")
        logger.info("Creating commands...")
        commands_json = await create_commands_delete_tag(ids, tags)
        logger.info(f"Created commands for {len(commands_json)} devices.")
        return commands_json
    except Exception as e:
        logger.error(f"Error processing delete tags: {e}")
        return None


async def delete_things_by_tags(tags: List[str]) -> Optional[Dict[str, Any]]:
    """
    Creates commands to delete things based on tags.

    :param tags: List of tags. Things with all these tags will be deleted.
    :return: A dictionary containing the created commands, or None if an error occurs.
    """
    try:
        logger.info("Creating commands to delete things based on tags...")
        commands_json = await create_command_delete_things(tags=tags)
        logger.info(f"Created commands for deleting things with tags: {tags}.")
        return commands_json
    except Exception as e:
        logger.error(f"Error processing delete things by tags: {e}")
        return None


async def delete_things_by_keys(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Reads IMEI numbers from a file and creates commands to delete things by their keys.

    :param file_path: Path to the input file containing IMEI numbers.
    :return: A dictionary containing the created commands, or None if an error occurs.

    """
    try:
        logger.info("Reading the file...")
        ids = await read_imei_only(file_path)
        logger.info(f"Read {len(ids)} devices from the file.")
        logger.info("Creating commands...")
        commands_json = await create_command_delete_things(thing_keys=ids)
        logger.info(f"Created commands for {len(commands_json)} devices.")
        return commands_json
    except Exception as e:
        logger.error(f"Error processing delete things by keys: {e}")
        return None


async def process_commands(api: OneEdgeApi, commands: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes the given commands by publishing them to the OneEdge API.

    :param api: An authenticated instance of OneEdgeApi.
    :param commands: A dictionary containing the commands to be processed.
    :return: A dictionary containing the results of the command execution.
    :raises OneEdgeApiError: If there is an error in publishing the commands.
    """
    try:
        results: Dict[str, Any] = await api.run_commands(commands)
        return results
    except OneEdgeApiError as e:
        logger.error(f"Error publishing commands: {e}")
        raise


async def authenticate_user() -> OneEdgeApi:
    """
    Authenticates the user with the OneEdge API using environment variables for credentials.

    :return: An instance of OneEdgeApi with the user authenticated.
    :raises OneEdgeApiError: If authentication fails.
    """
    try:
        api = OneEdgeApi(os.getenv("API_URL"))
        username: str = os.getenv("TELIT_USERNAME", "")
        password: str = os.getenv("TELIT_PASSWORD", "")
        if not username:
            username = input("Enter Telit Username: ")
            password = pwinput.pwinput(prompt="Enter Telit Password: ")

        await api.authenticate_user(
            username=username,
            password=password
        )

        logger.info("User authenticated successfully.")
        return api

    except OneEdgeApiError as e:
        logger.error(f"Authentication failed: {e}")
        raise


async def close_api_session(api: Any) -> None:
    """
    Closes the API session.

    :param api: The API object.
    :raises Exception: If there is an error closing the session.

    Example:
        await close_api_session(api)
    """
    try:
        session: Dict[str, Dict[str, bool]] = await api.close_session()
        if session.get("success", False):
            logger.info("Session closed successfully.")
        else:
            logger.warning("Failed to close session properly.")
    except Exception as e:
        logger.error(f"Error closing session: {e}")
        raise


async def execute_command(
    command_func: callable, *args, **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Executes the provided command function with the given arguments and handles the session.

    :param command_func: The function to execute.
    :param args: Arguments to pass to the function.
    :param kwargs: Keyword arguments to pass to the function.
    :return: The result of the command function or None if an error occurs.
    """
    api = None
    try:
        api = await authenticate_user()
        commands = await command_func(*args, **kwargs)
        if commands:
            logger.info("Command execution successful, publishing commands...")
            result = await process_commands(api, commands)
            logger.info("Commands published successfully.")
            return result
        else:
            logger.error("Command execution returned no result.")
            return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None
    finally:
        if api:
            await close_api_session(api)


async def main():
    """
    Parses command line arguments and executes the corresponding command function.

    :return: None
    """
    parser = argparse.ArgumentParser(
        description="Command Line Tool for Device Management"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add Settings Command
    parser_add_settings = subparsers.add_parser(
        "add-settings", help="Add settings to devices"
    )
    parser_add_settings.add_argument(
        "file_path",
        type=str,
        help="Path to the file containing IMEI numbers and settings",
    )

    # Apply Device Profile Command
    parser_apply_profile = subparsers.add_parser(
        "apply-profile", help="Apply a profile to devices"
    )
    parser_apply_profile.add_argument(
        "file_path", type=str, help="Path to the file containing IMEI numbers"
    )
    parser_apply_profile.add_argument(
        "profile_id", type=str, help="Profile ID to apply"
    )

    # Add Tags Command
    parser_add_tags = subparsers.add_parser("add-tags", help="Add tags to devices")
    parser_add_tags.add_argument(
        "file_path", type=str, help="Path to the file containing IMEI numbers"
    )
    parser_add_tags.add_argument(
        "tags", type=str, nargs="+", help="List of tags to add"
    )

    # Change Thing Definition Command
    parser_change_def = subparsers.add_parser(
        "change-def", help="Change thing definition of devices"
    )
    parser_change_def.add_argument(
        "file_path", type=str, help="Path to the file containing IMEI numbers"
    )
    parser_change_def.add_argument(
        "thing_key", type=str, help="New thing definition key"
    )

    # Undeploy Devices Command
    parser_undeploy = subparsers.add_parser("undeploy", help="Undeploy devices")
    parser_undeploy.add_argument(
        "file_path", type=str, help="Path to the file containing IMEI numbers"
    )

    # Delete Tags Command
    parser_delete_tags = subparsers.add_parser(
        "delete-tags", help="Delete tags from devices"
    )
    parser_delete_tags.add_argument(
        "file_path", type=str, help="Path to the file containing IMEI numbers"
    )
    parser_delete_tags.add_argument(
        "tags", type=str, nargs="+", help="List of tags to delete"
    )

    # Delete Things by Tags Command
    parser_delete_things_tags = subparsers.add_parser(
        "delete-things-tags", help="Delete things by tags"
    )
    parser_delete_things_tags.add_argument(
        "tags", type=str, nargs="+", help="List of tags to identify things for deletion"
    )

    # Delete Things by Keys Command
    parser_delete_things_keys = subparsers.add_parser(
        "delete-things-keys", help="Delete things by their keys"
    )
    parser_delete_things_keys.add_argument(
        "file_path", type=str, help="Path to the file containing IMEI numbers"
    )

    args = parser.parse_args()

    try:
        if args.command == "add-settings":
            await execute_command(add_settings, args.file_path)
        elif args.command == "apply-profile":
            await execute_command(apply_device_profile, args.file_path, args.profile_id)
        elif args.command == "add-tags":
            await execute_command(add_tags, args.file_path, args.tags)
        elif args.command == "change-def":
            await execute_command(
                change_thing_definition, args.file_path, args.thing_key
            )
        elif args.command == "undeploy":
            await execute_command(undeploy_devices, args.file_path)
        elif args.command == "delete-tags":
            await execute_command(delete_tags, args.file_path, args.tags)
        elif args.command == "delete-things-tags":
            await execute_command(delete_things_by_tags, args.tags)
        elif args.command == "delete-things-keys":
            await execute_command(delete_things_by_keys, args.file_path)
        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
