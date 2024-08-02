# Bulk Changes CLI Tool

## 1. Introduction

The Device Management CLI Tool is a command-line interface designed for managing devices. It allows users to perform various operations on devices via OneEdge API. It supports various operations, including device settings configuration, profile application, and tag management. The tool is implemented in Python and uses asynchronous programming to enhance performance.

## 2. Installation

Before running the application, ensure that you have Python installed on your system. This application requires Python 3.6 or later.

**Install Dependencies**

If pip is recognized as a command, you can use:

```shell
pip install -r requirements.txt
```

If you encounter an error stating that pip is not recognized as an internal or external command, you can use:

```shell
py -m pip install --user -r requirements.txt
```

## 3. Usage

To use the CLI tool, execute the `bulk_changes.py` script with the appropriate command and arguments. The general syntax is:

```sh
python bulk_changes.py <command> [arguments]
```

## 4. Commands

### 4.1. Add Settings

Add or update settings for multiple devices.

**Usage:**

```sh
python bulk_changes.py add-settings <file_path>
```

- `<file_path>`: Path to a CSV or Excel file containing IMEI numbers and their corresponding settings.

**Process:**

1. Read IMEI numbers and settings from the specified file.
2. Generate commands to update device settings.
3. Execute commands via the OneEdge API.

### 4.2. Apply Device Profile

Apply a specified device profile to multiple devices.

**Usage:**

```sh
python bulk_changes.py apply-profile <file_path> <profile_id>
```

- `<file_path>`: Path to a CSV or Excel file containing IMEI numbers.
- `<profile_id>`: ID of the profile to apply.

**Process:**

1. Read IMEI numbers from the file.
2. Generate commands to apply the profile to each device.
3. Execute commands via the OneEdge API.

### 4.3. Add Tags

Add specified tags to multiple devices.

**Usage:**

```sh
python bulk_changes.py add-tags <file_path> <tag1> <tag2> ...
```

- `<file_path>`: Path to a CSV or Excel file containing IMEI numbers.
- `<tag1> <tag2> ...`: Tags to be added to the devices.

**Process:**

1. Read IMEI numbers from the file.
2. Generate commands to add the specified tags.
3. Execute commands via the OneEdge API.

### 4.4. Change Thing Definition

Change the thing definition for multiple devices.

**Usage:**

```sh
python bulk_changes.py change-def <file_path> <thing_key>
```

- `<file_path>`: Path to a CSV or Excel file containing IMEI numbers.
- `<thing_key>`: New thing definition key to apply.

**Process:**

1. Read IMEI numbers from the file.
2. Generate commands to change the thing definition.
3. Execute commands via the OneEdge API.

### 4.5. Undeploy Devices

Undeploy multiple devices.

**Usage:**

```sh
python bulk_changes.py undeploy <file_path>
```

- `<file_path>`: Path to a CSV or Excel file containing IMEI numbers.

**Process:**

1. Read IMEI numbers from the file.
2. Verify VPN connection status.
3. Establish SSH connection to the server.
4. Execute SQL queries to remove devices from the database.
5. Generate commands to undeploy devices in OneEdge.
6. Execute commands via the OneEdge API.

### 4.6. Delete Tags

Remove specified tags from multiple devices.

**Usage:**

```sh
python bulk_changes.py delete-tags <file_path> <tag1> <tag2> ...
```

- `<file_path>`: Path to a CSV or Excel file containing IMEI numbers.
- `<tag1> <tag2> ...`: Tags to be removed.

**Process:**

1. Read IMEI numbers from the file.
2. Generate commands to remove the specified tags.
3. Execute commands via the OneEdge API.

### 4.7. Delete Things by Tags

Delete things (devices) based on specified tags.

**Usage:**

```sh
python bulk_changes.py delete-things-tags <tag1> <tag2> ...
```

- `<tag1> <tag2> ...`: Tags identifying the things to delete.

**Process:**

1. Generate command to delete things based on the tags.
2. Execute command via the OneEdge API.

### 4.8. Delete Things by Keys

Delete things (devices) based on their keys (IMEI numbers).

**Usage:**

```sh
python bulk_changes.py delete-things-keys <file_path>
```

- `<file_path>`: Path to a CSV or Excel file containing IMEI numbers.

**Process:**

1. Read IMEI numbers from the file.
2. Generate commands to delete things based on the keys.
3. Execute commands via the OneEdge API.

## 5. Configuration

The tool requires certain environment variables, which should be set in a `.env` file located in the `config/` directory. These variables include:

- `API_URL`: URL of the OneEdge API.
- `TELIT_USERNAME`: Username for OneEdge API authentication.
- `TELIT_PASSWORD`: Password for OneEdge API authentication.
- `DNS_SUFFIX`: DNS suffix for VPN connection verification.
- `SSH_HOSTNAME`: Hostname for SSH connections.
- `SSH_USERNAME`: Username for SSH connections.
- `SQLITE3_DBPATH`: Path to the SQLite database on the remote server.
- `SQLITE3_TABLE`: Name of the table in the SQLite database.

Note: Just Update the `.env` file with the telit credentials.
