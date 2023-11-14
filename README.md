# OneEdge Bulk Changes CLI

## Description

This Command-Line Interface (CLI) application facilitates bulk changes for OneEdge devices. It provides options for various operations such as adding tags to IMEIs, changing device profiles, updating Thing_defs, adjusting attribute settings, and undeploying or changing data destinations for loggers.

## Installation

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

## Usage

To use the application, follow these steps:

1. **Running the Application**

   Run the main script from the command line:

   ```bash
   python builk_changes.py [path-to-your-file]
   ```

   Replace `[path-to-your-file]` with the path to the CSV or Excel file containing the IMEIs and other relevant data.

2. **Interactive Menu**

   After running the script, you'll be presented with an interactive menu:

   ```
   Welcome to OneEdge Bulk Changes!
   1. Adding tags to a list of IMEIs
   2. Change device profile to IMEIs
   3. Change Thing_def to IMEIs
   4. Add attributes settings to all IMEIs
   5. Undeploy or change data destination for removed loggers
   q. Quit
   ```

   Enter the number corresponding to the task you want to perform.

3. **Follow Prompts**

   Each option will prompt you for additional information. Enter the required details as requested.

4. **View Results**

   After executing an option, the results or status of the operation will be displayed on the terminal.
  
# **Undeploy**

## **Description**

This project is composed of Python scripts designed to interact with the OneEdge API. It reads a file containing IMEI numbers, generates commands from those numbers, and sends the commands to the OneEdge API.

## Connecting to the Remote Server

  
**SSH Connection**: Open a terminal and connect to the remote server using SSH by executing the following command:

   ```
   ssh user@192.168.52.233
   ```

  

**Change Directory**: Once connected, navigate to the appropriate directory using the following command:

   ```
   cd workspace/diditwork/testdata
   ```

## Interacting with the SQL Database


**Connect to SQLite Database**: Connect to the SQLite database by executing the following command:

   ```

   sqlite3 database.db

   ```

  

**Test IMEI**: Test the IMEI numbers from the extracted list using a SELECT statement. Replace `[imei_list]` with the actual list of IMEI numbers:

   ```

   SELECT * FROM deployment_queue WHERE imei IN ([imei_list]);

   ```

  

Run the jupyter notebook file to get the full command

  

**Delete Data**: If necessary, delete the data associated with the IMEI numbers from the database using the following command:

   ```

   DELETE FROM deployment_queue WHERE imei IN ([imei_list]);

   ```

Run the jupyter notebook file to get the full command

  

Please note that this document assumes familiarity with SSH, SQL. It's important to carefully execute each step and replace placeholders such as `[imei_list]` with actual data.

  

*Disclaimer: Ensure you have the necessary permissions and backups before making any modifications to the data or database.*