from netmiko import ConnectHandler
from log import authLog
from functions import logInCSV

import traceback
import re

shInventory = "show inventory"
shIntStatusHalf = "show interface | tab | inc half|inc Half"
shIntStatusHalfcEdge = "show interface | inc Giga|TenGig|Duplex"
halfPatt = r"Half"

def showHalfInts(validIPs, username, netDevice):
    # This function is to take a show run
    
    for validDeviceIP in validIPs:
        try:
            validDeviceIP = str(validDeviceIP).strip()
            currentNetDevice = {
                'device_type': 'cisco_viptela', #'cisco_viptela', #cisco_xe
                'ip': validDeviceIP,
                'username': username,
                'password': netDevice['password'],
                'secret': netDevice['secret'],
                'global_delay_factor': 2.0,
                'timeout': 120,
                'session_log': 'logs/netmikoLog.txt',
                'verbose': True,
                'session_log_file_mode': 'append'
            }

            print(f"Connecting to device {validDeviceIP}...")
            with ConnectHandler(**currentNetDevice) as sshAccess:
                sshAccess.enable()
                authLog.info(f"Generating hostname for {validDeviceIP}")
                shHostnameOut = re.sub(".mgmt.internal.das|.cm.mgmt.internal.das|.mgmt.wellpoint.com","#", validDeviceIP)
                authLog.info(f"Hostname for {validDeviceIP}: {shHostnameOut}")
                print(f"INFO: This is the hostname: {shHostnameOut}")

                print(f"INFO: Taking a \"{shInventory}\" for device: {validDeviceIP}")
                shInventoryOut = sshAccess.send_command_timing(shInventory)
                authLog.info(f"Automation successfully ran the command: {shInventory}")

                if "syntax error" in shInventoryOut:
                    print(f"INFO: Taking a \"{shIntStatusHalf}\" for device: {validDeviceIP}")
                    shIntStatusHalfOut = sshAccess.send_command_timing(shIntStatusHalf)
                    authLog.info(f"Automation successfully ran the command: {shIntStatusHalf}")

                    if halfPatt in shIntStatusHalfOut:
                        print(f"INFO: The word \"half\" was found on the output for device: {validDeviceIP}")
                        authLog.info(f"The word \"half\" was found on the output for device: {validDeviceIP}")
                        authLog.info(f"{shHostnameOut}{shIntStatusHalf}\n{shIntStatusHalfOut}")
                        logInCSV(shHostnameOut, "Devices Half Duplex", shIntStatusHalf,shIntStatusHalfOut)
                    else:
                        authLog.info(f"Device {validDeviceIP} is running at full duplex/full speed")
                        logInCSV(shHostnameOut, "Devices Full Duplex", shIntStatusHalf,shIntStatusHalfOut)
                else:
                    print(f"INFO: Taking a \"{shIntStatusHalfcEdge}\" for device: {validDeviceIP}")
                    shIntStatusHalfcEdgeOut = sshAccess.send_command_timing(shIntStatusHalfcEdge)
                    authLog.info(f"Automation successfully ran the command: {shIntStatusHalfcEdge}")

                    if halfPatt in shIntStatusHalfcEdgeOut:
                        print(f"INFO: The word \"half\" was found on the output for device: {validDeviceIP}")
                        authLog.info(f"The word \"half\" was found on the output for device: {validDeviceIP}")
                        authLog.info(f"{shHostnameOut}{shIntStatusHalfcEdge}\n{shIntStatusHalfcEdgeOut}")
                        logInCSV(shHostnameOut, "Devices Half Duplex", shIntStatusHalfcEdge,shIntStatusHalfcEdgeOut)
                    else:
                        authLog.info(f"Device {validDeviceIP} is running at full duplex/full speed")
                        logInCSV(shHostnameOut, "Devices Full Duplex", shIntStatusHalfcEdge,shIntStatusHalfcEdgeOut)

        except Exception as error:
            print(f"An error occurred: {error}\n {traceback.format_exc()}")
            authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}\n {traceback.format_exc()}")

            with open(f"Outputs/Failed Devices.txt","a") as failedDevices:

                failedDevices.write(f"User {username} connected to {validDeviceIP} got an error.\n{error}")
