import os
import platform
import subprocess
import warnings
from contextlib import contextmanager
from typing import Optional, List, Generator

from cryptography.utils import CryptographyDeprecationWarning

with warnings.catch_warnings(action="ignore", category=CryptographyDeprecationWarning):
    import paramiko
from src.logger.logger import Logger
from dotenv import load_dotenv

logger: Logger = Logger(__name__)
load_dotenv("config/.env")


def is_vpn_connected(dns_suffix: str) -> Optional[bool]:
    """
    Check if the VPN is connected by verifying the presence of a specific DNS suffix.

    :param dns_suffix: The DNS suffix to check for VPN connection.
    :return: True if VPN is connected, False if not, and None if an error occurs.
    """
    try:
        if platform.system() == "Windows":
            command: List[str] = ["ipconfig", "/all"]
        elif platform.system() == "Linux":
            command: List[str] = ["nmcli", "dev", "show"]
        else:
            logger.error("Unsupported operating system.")
            return None

        result: subprocess.CompletedProcess = subprocess.run(
            command, capture_output=True, text=True, check=True
        )
        return any(
            dns_suffix in line
            for line in result.stdout.splitlines()
            if "Connection-specific DNS Suffix" in line or "IP4.DNS" in line
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running network command: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None


@contextmanager
def ssh_connection(
        hostname: str, username: str, private_key_path: Optional[str] = None
) -> Generator[Optional[paramiko.SSHClient], None, None]:
    """
    Create an SSH connection to the specified host.

    :param hostname: The IP address or hostname of the SSH server.
    :param username: The SSH username.
    :param private_key_path: Path to the private key file (optional).
    :return: A generator yielding an SSHClient object or None if connection fails.
    """
    ssh_client: Optional[paramiko.SSHClient] = None
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if private_key_path:
            private_key: paramiko.RSAKey = paramiko.RSAKey.from_private_key_file(
                private_key_path
            )
            ssh_client.connect(hostname, username=username, pkey=private_key)
        else:
            ssh_client.connect(hostname, username=username)

        logger.info(f"Successfully connected to SSH server at {hostname}.")
        yield ssh_client
    except paramiko.AuthenticationException:
        logger.error(f"Authentication failed when connecting to {hostname}.")
        yield None
    except paramiko.SSHException as sshException:
        logger.error(f"Could not establish SSH connection: {sshException}")
        yield None
    except Exception as e:
        logger.error(f"An error occurred while connecting to the SSH server: {e}")
        yield None
    finally:
        if ssh_client:
            ssh_client.close()


def execute_sql_query(
        ssh_client: paramiko.SSHClient, db_path: str, sql_query: str, params: tuple = ()
) -> Optional[str]:
    """
    Execute an SQL query on the remote SQLite database.

    :param ssh_client: The SSH client connected to the server.
    :param db_path: The path to the SQLite database on the remote server.
    :param sql_query: The SQL query to execute.
    :param params: The parameters for the SQL query.
    :return: The result of the SQL query as a string, or None if an error occurs.
    """
    try:
        param_string = ','.join(f"{p}" for p in params)
        formatted_query = sql_query.format(param_string)
        command: str = f"sqlite3 {db_path} \"{formatted_query}\""
        stdin, stdout, stderr = ssh_client.exec_command(command)
        result: str = stdout.read().decode()
        error: str = stderr.read().decode()
        if error:
            logger.error(f"Error executing SQL query: {error}")
            return None
        return result
    except Exception as e:
        logger.error(f"An error occurred while executing SQL query: {e}")
        return None


def construct_select_query(table_name: str) -> str:
    """
    Construct a parameterized SELECT query.

    :param table_name: The name of the table to query.
    :return: A parameterized SELECT query string.
    """
    return f"SELECT * FROM {table_name} WHERE imei IN ({{}});"


def construct_delete_query(table_name: str) -> str:
    """
    Construct a parameterized DELETE query.

    :param table_name: The name of the table to delete from.
    :return: A parameterized DELETE query string.
    """
    return f"DELETE FROM {table_name} WHERE imei IN ({{}});"


def count_results(result: Optional[str]) -> int:
    """
    Count the number of results returned by the SQL query.

    :param result: The raw output from the SQL query execution.
    :return: The number of records found.
    """
    if result is None:
        return 0
    return len(result.strip().split("\n")) if result.strip() else 0


def undeploy_process(imei_list: List[str]) -> None:
    """
    Process devices: check for VPN connection, execute SQL queries, and remove devices.

    :param imei_list: List of IMEI numbers to check and delete.
    :return: None
    """
    dns_suffix: str = os.getenv("DNS_SUFFIX", "")
    ssh_hostname: str = os.getenv("SSH_HOSTNAME", "")
    ssh_username: str = os.getenv("SSH_USERNAME", "")
    db_path: str = os.getenv("SQLITE3_DBPATH", "")
    table_name: str = os.getenv("SQLITE3_TABLE", "")

    vpn_connected: Optional[bool] = is_vpn_connected(dns_suffix)

    if vpn_connected:
        logger.info("VPN is connected. Attempting to connect to SSH server.")
        with ssh_connection(
                hostname=ssh_hostname, username=ssh_username, private_key_path=None
        ) as ssh_client:
            if ssh_client:
                select_query: str = construct_select_query(table_name)
                select_result: Optional[str] = execute_sql_query(
                    ssh_client,
                    db_path,
                    select_query,
                    (",".join(f"'{imei}'" for imei in imei_list),),
                )

                if select_result is not None:
                    count: int = count_results(select_result)
                    logger.info(
                        f"Number of devices found: {count} out of {len(imei_list)}"
                    )

                    if count > 0:
                        delete_query: str = construct_delete_query(table_name)
                        delete_result: Optional[str] = execute_sql_query(
                            ssh_client,
                            db_path,
                            delete_query,
                            (",".join(f"'{imei}'" for imei in imei_list),),
                        )
                        if delete_result is not None:
                            logger.info(
                                "Devices with the specified IMEIs have been deleted."
                            )
                        else:
                            logger.error("Failed to delete devices.")
                    else:
                        logger.info("No devices found to delete.")
                else:
                    logger.error("Failed to execute select query.")
            else:
                logger.error("Failed to establish SSH connection.")
    elif vpn_connected is False:
        logger.info("VPN is not connected. Cannot proceed to SSH connection.")
    else:
        logger.error("VPN status is unknown. Cannot proceed to SSH connection.")
