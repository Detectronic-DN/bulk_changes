from typing import List, Dict, Optional, Any, Union
from src.oneEdge.oneEdgeAPI import OneEdgeApi, OneEdgeApiError
from src.logger.logger import Logger

logger = Logger(__name__)


async def get_profile_id(one_edge_api: OneEdgeApi, profile_name: str) -> Optional[str]:
    """
    Get profile ID from the oneEdge API.

    :param one_edge_api: Instance of OneEdgeApi.
    :param profile_name: Name of the profile to search for.
    :return: Profile ID if found, None otherwise.
    :raises OneEdgeApiError: If there's an error communicating with the API.

    Example:
        profile_id = await get_profile_id(one_edge_api, "Standard Profile")
        if profile_id:
            print(f"Profile ID: {profile_id}")
        else:
            print("Profile not found.")
    """
    try:
        response = await one_edge_api.run_command(
            {"command": "lwm2m.profile.list", "params": {"limit": 100, "offset": 0}}
        )

        profile_list = response.get("params", {}).get("result", [])

        for profile in profile_list:
            if profile.get("name") == profile_name:
                return profile["id"]

        logger.warning(f"Profile name '{profile_name}' not found.")
        return None
    except OneEdgeApiError as e:
        logger.error(f"Error while fetching profile: {e}")
        raise


async def get_thing_def_key(one_edge_api: OneEdgeApi, thing_name: str) -> Optional[str]:
    """
    Get thing definition key from the oneEdge API.

    :param one_edge_api: Instance of OneEdgeApi.
    :param thing_name: Name of the thing definition to search for.
    :return: Thing definition key if found, None otherwise.
    :raises OneEdgeApiError: If there's an error communicating with the API.

    Example:
        thing_def_key = await get_thing_def_key(one_edge_api, "Temperature Sensor")
        if thing_def_key:
            print(f"Thing Definition Key: {thing_def_key}")
        else:
            print("Thing definition not found.")
    """
    try:
        response = await one_edge_api.run_command({"command": "thing_def.list"})

        thing_def_list = response.get("params", {}).get("result", [])

        for thing_def in thing_def_list:
            if thing_def.get("name") == thing_name:
                return thing_def["key"]

        logger.warning(f"Thing definition name '{thing_name}' not found.")
        return None
    except OneEdgeApiError as e:
        logger.error(f"Failed to get thing definition list: {e}")
        raise


async def create_commands_tags(
        imei_list: List[str], tags_list: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Creates commands to add tags to devices.

    :param imei_list: A list of IMEI numbers.
    :param tags_list: A list of tags to add.
    :return: A dictionary containing the created commands.

    Example:
        imei_list = ["123456789012345", "987654321098765"]
        tags_list = ["sensor", "active"]
        commands = await create_commands_tags(imei_list, tags_list)
        print(commands)
    """
    try:
        return {
            str(i): {
                "command": "thing.tag.add",
                "params": {"thingKey": imei_number, "tags": tags_list},
            }
            for i, imei_number in enumerate(imei_list, 1)
        }
    except Exception as e:
        logger.error(f"Error creating tag commands: {e}")
        raise


async def create_commands_device_profile(
        imei_list: List[str], profile_id: str
) -> Dict[str, Dict[str, Any]]:
    """
    Creates commands to change device profiles.

    :param imei_list: A list of IMEI numbers.
    :param profile_id: The ID of the profile to apply.
    :return: A dictionary containing the created commands.

    Example:
        imei_list = ["123456789012345", "987654321098765"]
        profile_id = "profile_123"
        commands = await create_commands_device_profile(imei_list, profile_id)
        print(commands)
    """
    try:
        return {
            str(i): {
                "command": "lwm2m.device.profile.change",
                "params": {"thingKey": imei_number, "profileId": profile_id},
            }
            for i, imei_number in enumerate(imei_list, 1)
        }
    except Exception as e:
        logger.error(f"Error creating device profile commands: {e}")
        raise


async def create_commands_settings(
        imei_list: List[str], value_list: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Creates commands to publish attribute settings changes.

    :param imei_list: A list of IMEI numbers.
    :param value_list: A list of associated values.
    :return: A dictionary containing the created commands.
    :raises ValueError: If imei_list and value_list have different lengths.

    Example:
        imei_list = ["123456789012345", "987654321098765"]
        value_list = ["DM=Alarm,SI=900", "DI=86400"]
        commands = await create_commands_settings(imei_list, value_list)
        print(commands)
    """
    if len(imei_list) != len(value_list):
        logger.error("IMEI list and value list must have the same length")
        raise ValueError("IMEI list and value list must have the same length")

    try:
        return {
            str(i): {
                "command": "attribute.publish",
                "params": {
                    "thingKey": imei_number,
                    "key": "att_settings_change",
                    "value": value,
                },
            }
            for i, (imei_number, value) in enumerate(
                zip(imei_list, value_list), start=1
            )
        }
    except Exception as e:
        logger.error(f"Error creating settings commands: {e}")
        raise


async def create_commands_thing_def(
        imei_list: List[str], thing_key: str
) -> Dict[str, Dict[str, Any]]:
    """
    Creates commands to change thing definitions.

    :param imei_list: A list of IMEI numbers.
    :param thing_key: The new thing definition key to apply.
    :return: A dictionary containing the created commands.

    Example:
        imei_list = ["123456789012345", "987654321098765"]
        thing_key = "new_def_key"
        commands = await create_commands_thing_def(imei_list, thing_key)
        print(commands)
    """
    try:
        return {
            str(i): {
                "command": "thing.def.change",
                "params": {
                    "key": imei_number,
                    "newDefKey": thing_key,
                    "dropProps": False,
                    "dropAttrs": True,
                    "dropAlarms": True,
                },
            }
            for i, imei_number in enumerate(imei_list, start=1)
        }
    except Exception as e:
        logger.error(f"Error creating thing definition commands: {e}")
        raise


async def create_commands_undeploy(imei_list: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Creates commands to undeploy devices by clearing their data destination.

    :param imei_list: A list of IMEI numbers.
    :return: A dictionary containing the created commands.

    Example:
        imei_list = ["123456789012345", "987654321098765"]
        commands = await create_commands_undeploy(imei_list)
        print(commands)
    """
    try:
        return {
            str(i): {
                "command": "attribute.publish",
                "params": {
                    "thingKey": imei_number,
                    "key": "data_destination",
                    "value": "",
                },
            }
            for i, imei_number in enumerate(imei_list, start=1)
        }
    except Exception as e:
        logger.error(f"Error creating undeploy commands: {e}")
        raise


async def create_commands_delete_tag(
        imei_list: List[str], tags_list: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Creates commands to delete tags from devices.

    :param imei_list: A list of IMEI numbers.
    :param tags_list: A list of tags to delete.
    :return: A dictionary containing the created commands.

    Example:
        imei_list = ["123456789012345", "987654321098765"]
        tags_list = ["sensor", "inactive"]
        commands = await create_commands_delete_tag(imei_list, tags_list)
        print(commands)
    """
    try:
        return {
            str(i): {
                "command": "thing.tag.delete",
                "params": {"thingKey": imei_number, "tags": tags_list},
            }
            for i, imei_number in enumerate(imei_list, start=1)
        }
    except Exception as e:
        logger.error(f"Error creating delete tag commands: {e}")
        raise


async def create_commands_delete_tags(
        thing_keys: Union[str, List[str]], tags_to_remove: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Creates commands to delete specified tags from one or more things.

    :param thing_keys: A single thing key or a list of thing keys to remove tags from.
    :param tags_to_remove: A list of tags to be removed from the specified thing(s).
    :return: A dictionary containing the created commands.
    :raises ValueError: If tags_to_remove is empty.

    Example:
        thing_keys = ["thing_123", "thing_456"]
        tags_to_remove = ["outdated", "inactive"]
        commands = await create_commands_delete_tags(thing_keys, tags_to_remove)
        print(commands)
    """
    if not tags_to_remove:
        logger.error("tags_to_remove list cannot be empty")
        raise ValueError("tags_to_remove list cannot be empty")

    try:
        if isinstance(thing_keys, str):
            thing_keys = [thing_keys]

        return {
            str(i): {
                "command": "thing.tag.delete",
                "params": {"thingKey": thing_key, "tags": tags_to_remove},
            }
            for i, thing_key in enumerate(thing_keys, start=1)
        }
    except Exception as e:
        logger.error(f"Error creating delete tag commands: {e}")
        raise


async def create_command_delete_things(
        thing_keys: Optional[Union[str, List[str]]] = None,
        thing_ids: Optional[Union[str, List[str]]] = None,
        tags: Optional[List[str]] = None,
        query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a command to delete things based on various criteria.

    :param thing_keys: A single thing key or a list of thing keys to delete.
    :param thing_ids: A single thing ID or a list of thing IDs to delete.
    :param tags: A list of tags. Things with all these tags will be deleted.
    :param query: A query string to match things for deletion.
    :return: A dictionary containing the command and its parameters.
    :raises ValueError: If no deletion criteria are provided or if multiple criteria are provided.

    Example:
        # Example 1: Delete by thing keys
        commands = await create_command_delete_things(thing_keys=["thing_123", "thing_456"])
        print(commands)

        # Example 2: Delete by tags
        commands = await create_command_delete_things(tags=["obsolete"])
        print(commands)
    """
    if sum([bool(thing_keys), bool(thing_ids), bool(tags), bool(query)]) != 1:
        logger.error("Exactly one deletion criteria must be provided")
        raise ValueError("Exactly one deletion criteria must be provided")

    params: Dict[str, Any] = {}

    if thing_keys:
        params["key"] = thing_keys if isinstance(thing_keys, list) else [thing_keys]
    elif thing_ids:
        params["id"] = thing_ids if isinstance(thing_ids, list) else [thing_ids]
    elif tags:
        params["tag"] = tags
    elif query:
        params["query"] = query

    try:
        return {"command": "thing.delete", "params": params}
    except Exception as e:
        logger.error(f"Error creating delete things command: {e}")
        raise
