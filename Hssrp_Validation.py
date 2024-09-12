"""
HSRP Validation Library

This script is designed to automate the validation of HSRP (Hot Standby Router Protocol) status on network devices 
using SSH. It connects to specified devices (e.g., routers or switches), executes the 'show standby brief' command, 
parses the output, and validates the HSRP state against expected conditions. The validation results are then 
formatted and output in JSON format.

Key Features:
- Establishes SSH connections to network devices using Paramiko.
- Parses HSRP status from the 'show standby brief' command.
- Validates the active and standby states of specified HSRP groups.
- Outputs the validation results in a JSON format for easy integration with other systems.

Usage:
- Customize the SSH credentials, hostnames, and expected HSRP conditions in the `main()` function.
- Run the script to automatically validate HSRP status on the specified devices.
"""

import paramiko
import re
import json

class SSHClient:
    """
    A class to handle SSH connections and command execution on a remote host.
    """

    def __init__(self, host, username, password):
        """
        Initializes the SSHClient with connection details.
        """
        self.host = host
        self.username = username
        self.password = password

    def run_command(self, command):
        """
        Executes a command on the remote host via SSH.
        Returns the output of the command.
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.host, username=self.username, password=self.password)

            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode().strip()
            client.close()
            return output
        except Exception as e:
            return None

class HSRPValidator:
    """
    A class to validate HSRP status on a remote device using SSHClient.
    """

    @staticmethod
    def parse_show_standby_brief(output):
        """
        Parses the output of the 'show standby brief' command.
        Returns a dictionary of HSRP states keyed by group.
        """
        pattern = r"(\S+)\s+(\S+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)"
        standby_data = {}
        for line in output.splitlines():
            match = re.match(pattern, line)
            if match:
                group, state = match.group(2), match.group(4).lower()
                standby_data[group] = state
        return standby_data

    @staticmethod
    def validate_hsrp(standby_data, expected_conditions, device_name):
        """
        Validates HSRP states against expected conditions.
        Returns a dictionary of validation results.
        """
        results = {}
        for condition in expected_conditions:
            group = condition['Group']
            expected_active = condition.get('ExpectedActiveState', '').lower()
            expected_standby = condition.get('ExpectedStandbyState', '').lower()

            actual_state = standby_data.get(group, '')

            if expected_active:
                results[f"grp{group}"] = {
                    "Active": 'pass' if actual_state == 'active' else f"Failed : {device_name} No longer Active"
                }
            if expected_standby:
                results[f"grp{group}"] = {
                    **results.get(f"grp{group}", {}),
                    "Standby": 'pass' if actual_state == 'standby' else f"Failed : {device_name} No longer Standby"
                }
        return results

def main():
    # Define expected conditions for CPE1 and CPE2
    expected_conditions_cpe1 = [
        {'Group': '1', 'ExpectedActiveState': 'Active'},
        {'Group': '2', 'ExpectedStandbyState': 'Standby'}
    ]

    expected_conditions_cpe2 = [
        {'Group': '1', 'ExpectedActiveState': 'Active'},
        {'Group': '2', 'ExpectedStandbyState': 'Standby'}
    ]

    # SSH credentials and command
    ssh_details = [
        {"device_name": "CPE1", "host": "CPE1_IP_or_Hostname", "username": "your_username", "password": "your_password", "conditions": expected_conditions_cpe1},
        {"device_name": "CPE2", "host": "CPE2_IP_or_Hostname", "username": "your_username", "password": "your_password", "conditions": expected_conditions_cpe2}
    ]
    command = "show standby brief"

    # Initialize the final results dictionary
    final_results = {}

    # Validate each device
    for device in ssh_details:
        ssh_client = SSHClient(device["host"], device["username"], device["password"])
        output = ssh_client.run_command(command)

        if output:
            standby_data = HSRPValidator.parse_show_standby_brief(output)
            final_results[device["device_name"]] = HSRPValidator.validate_hsrp(standby_data, device["conditions"], device["device_name"])

    # Output results as JSON
    print(json.dumps(final_results, indent=4))

if __name__ == "__main__":
    main()
