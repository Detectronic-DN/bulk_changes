import os
import asyncio
import argparse
import json
from src.authentication.authenticate import authenticate
from src.oneEdge.oneEdgeApi import OneEdgeApi
from src.bulk_changes.creating_commands import *
from src.bulk_changes.reading_file import *

async def main():
    parser = argparse.ArgumentParser(description='Process a file and generate commands.')
    parser.add_argument('file_path', help='The path to the file to be processed')
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist.")
        return

    API_URL = "https://api-de.devicewise.com/api"
    api = OneEdgeApi(API_URL)
    await authenticate(api)

    options = {
        '1': {
            'prompt': 'Enter the tag names separated by commas: ',
            'func': create_commands_tags,
            'validation': lambda x: all(tag.strip() for tag in x.split(',')) 
        },
        '2': {
            'prompt': 'Enter the profile name: ',
            'func': create_commands_device_profile,
            'validation': lambda x: x.strip() != '',
            'post_process': get_profile_id
        },
        '3': {
            'prompt': 'Enter the thing name: ',
            'func': create_commands_thing_def,
            'validation': lambda x: x.strip() != '',
            'post_process': get_thing_def_key
        },
        '4': {
            'prompt': '',
            'func': create_commands_settings
        },
        '5': {
            'prompt': '',
            'func': create_commands_undeploy
        },
        '6': {
            'prompt': 'Enter the Tag name to delete: ',
            'func': create_commands_delete_tag,
            'validation': lambda x: all(tag.strip() for tag in x.split(','))
        }
    }

    while True:
        print("Welcome to OneEdge Bulk Changes!")
        print("1. Adding tags to a list of IMEIs")
        print("2. Change device profile to IMEIs")
        print("3. Change Thing_def to IMEIs")
        print("4. Add attributes settings to all IMEIs")
        print("5. Undeploy or change data destination for removed loggers")
        print("6. Remove a tag from a list of IMEIs")
        print("q. Quit")

        choice = input("Enter your choice: ").strip()

        if choice.lower() == 'q':
            print("Closing session...")
            session = await api.close_session()
            if session.get("1", {}).get("success"):
                print("session closed successfully.")
            break

        selected_option = options.get(choice)
        if selected_option:
            try:
                if choice == '4':
                    imeis, settings = read_imei_and_setting(args.file_path)
                    commands_json = await selected_option['func'](imeis, settings)
                    
                else:
                    input_value = input(selected_option['prompt']).strip()
                    if selected_option.get('validation') and not selected_option['validation'](str(input_value)):
                        print("Invalid input. Please try again.")
                        continue
                    imeis = read_imeis(args.file_path)
                    if 'post_process' in selected_option:
                        input_value = await selected_option['post_process'](api, str(input_value))
                    else:
                        input_value = input_value
                    commands_json = await selected_option['func'](imeis, input_value)
            except Exception as e:
                print(f"Error: {str(e)}")
                continue
        else:
            print("Invalid choice. Please enter a valid number.")
            continue

        print("Publishing commands...")
        await api.run_commands(commands_json)
        print("imei {} updated successfully.".format(imeis))


if __name__ == "__main__":
    asyncio.run(main())
