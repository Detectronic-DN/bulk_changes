from src.oneEdge.oneEdgeApi import OneEdgeApiError
from src.utils.logger import create_logger

logger = create_logger(__name__)


async def get_profile_id(one_edge_api, profile_name):
    """
    get profile list from the OneEdge API.
    """
    profile_id_found = None
    try:
        response = await one_edge_api.run_command({
            "command": "lwm2m.profile.list",
            "params": {
                "limit": 100,
                "offset": 0
            }
          })
        profile_ids = [item['id'] for item in response["params"]['result']]
        device_profiles = [item['name'] for item in response["params"]['result']]
        profile_list = dict(zip(profile_ids, device_profiles))
        for profile_id, profile_name in profile_list.items():
            if profile_name == profile_name:
                profile_id_found = profile_id
                break  # Stop searching once the name is found
            else:
                print(f"Profile name '{profile_name}' not found.")
        return profile_id_found
    except OneEdgeApiError as e:
        logger.error(f"Failed to get profile list: {e}")
        return None


async def get_thing_def_key(one_edge_api, thing_name):
    """
    get thing_def list from the OneEdge API.
    """
    thing_def_key_found = None
    try:
        response = await one_edge_api.run_command({
            "command": "thing_def.list"
        })
        thing_def_key = [item['key'] for item in response["params"]['result']]
        thing_def_name = [item['name'] for item in response["params"]['result']]
        thing_def_list = dict(zip(thing_def_key, thing_def_name))
        for thing_def_key, thing_def_name in thing_def_list.items():
            if thing_def_name == thing_name:
                thing_def_key_found = thing_def_key
                break  # Stop searching once the name is found
            else:
                print(f"Profile name '{thing_name}' not found.")
        return thing_def_key_found    
    except OneEdgeApiError as e:
        logger.error(f"Failed to get profile list: {e}")
        return None

async def create_commands_tags(imei_list, tags_list):
    """
    Creates commands based on the given column data.

    Parameters:
        column_data (list): A list of column data.

    Returns:
        dict: A dictionary containing the created commands.
    """
    return {
        str(i): {
            "command": "thing.tag.add",
            "params": {
                "thingKey": imei_number,
                "tags": tags_list
            }
        }
        for i, imei_number in enumerate(imei_list, 1)
    }


async def create_commands_device_profile(imei_list, profile_id):
    """
    Creates commands based on the given column data.

    Parameters:
        column_data (list): A list of column data.

    Returns:
        dict: A dictionary containing the created commands.
    """
    return {
        str(i): {
           "command": "lwm2m.device.profile.change",
           "params": {
                "thingKey": imei_number,
                "profileId": profile_id
            }
        }
        for i, imei_number in enumerate(imei_list, 1)
    }

async def create_commands_settings(imei_list, value_list):
    """
    Creates commands based on the given IMEI list and associated values.

    Parameters:
        imei_list (list): A list of IMEI numbers.
        value_list (list): A list of associated values.

    Returns:
        dict: A dictionary containing the created commands with incremental keys as strings.
    """
    return {
        str(i): {
            "command": "attribute.publish",
            "params": {
                "thingKey": imei_number,
                "key": "att_settings_change",
                "value": value
            }
        }
       for i, (imei_number, value) in enumerate(zip(imei_list, value_list), start=1)
    }

async def create_commands_thing_def(imei_list, thing_key):
    """
    Creates commands based on the given IMEI list.

    Parameters:
        imei_list (list): A list of IMEI numbers.

    Returns:
        dict: A dictionary containing the created commands with incremental keys as strings.
    """
    return {
        str(i): {
            "command": "thing.def.change",
            "params": {
                "key": imei_number,
                "newDefKey": f"{thing_key}",
                "dropProps": False,
                "dropAttrs": True,
                "dropAlarms": True
            }
        }
       for i, imei_number in enumerate(imei_list, start=1)
    }


async def create_commands_undeploy(imei_list):
    """
    Creates commands based on the given IMEI list.

    Parameters:
        imei_list (list): A list of IMEI numbers.

    Returns:
        dict: A dictionary containing the created commands with incremental keys as strings.
    """
    return {
        str(i): {
            "command": "attribute.publish",
            "params": {
                "thingKey": imei_number,
                "key": "data_destination",
                "value": ""
            }
        }
       for i, imei_number in enumerate(imei_list, start=1)
    }


async def create_commands_delete_tag(imei_list, tags_list):
    """
    Creates commands based on the given IMEI list.

    Parameters:
        imei_list (list): A list of IMEI numbers.

    Returns:
        dict: A dictionary containing the created commands with incremental keys as strings.
    """
    return {
        str(i): {
            "command": "thing.tag.delete",
            "params": {
                "thingKey": imei_number,
                "tags": tags_list
            }
        }
       for i, imei_number in enumerate(imei_list, start=1)
    }