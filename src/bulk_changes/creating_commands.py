from src.oneEdge.oneEdgeApi import OneEdgeApiError
from src.utils.logger import create_logger

logger = create_logger(__name__)


async def get_profile_id(one_edge_api, profile_name):
    """
    Get profile ID from the OneEdge API.
    """
    try:
        response = await one_edge_api.run_command({
            "command": "lwm2m.profile.list",
            "params": {
                "limit": 100,
                "offset": 0
            }
        })

        profile_list = response.get("params", {}).get("result", [])
        
        for profile in profile_list:
            if profile.get('name') == profile_name:
                return profile['id']

        print(f"Profile name '{profile_name}' not found.")
        return None 
    except OneEdgeApiError as e:
        logger.error(f"Error while fetching profile: {e}")
        return None  

async def get_thing_def_key(one_edge_api, thing_name):
    """
    Get thing definition key from the OneEdge API.
    """
    try:
        response = await one_edge_api.run_command({
            "command": "thing_def.list"
        })

        thing_def_list = response.get("params", {}).get("result", [])
        
        for thing_def in thing_def_list:
            if thing_def.get('name') == thing_name:
                return thing_def['key']

        print(f"Thing definition name '{thing_name}' not found.")
        return None  # Thing definition not found
    except OneEdgeApiError as e:
        logger.error(f"Failed to get thing definition list: {e}")
        return None  # Handle the error and return an appropriate value

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