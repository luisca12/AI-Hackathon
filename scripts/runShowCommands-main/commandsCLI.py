from netmiko import ConnectHandler
from log import authLog
from functions import failedDevices, logInCSV, filterFilename

import traceback
import re
import os

shCommand = ""
shHostname = "show run | i hostname"

def showCommands(validIPs, username, netDevice, shCommand):
    # This function is to take a show run
    results = []
    
    for validDeviceIP in validIPs:
        try:
            validDeviceIP = validDeviceIP.strip()
            currentNetDevice = {
                'device_type': 'cisco_xe',
                'ip': validDeviceIP,
                'username': username,
                'password': netDevice['password'],
                'secret': netDevice['secret'],
                'global_delay_factor': 2.0,
                'timeout': 120,
                'session_log': 'Outputs/netmikoLog.txt',
                'verbose': False,
                'session_log_file_mode': 'append'
            }

            # print(f"INFO: Connecting to device {validDeviceIP}...")
            authLog.info(f"Connecting to device {validDeviceIP}")
            with ConnectHandler(**currentNetDevice) as sshAccess:
                try:
                    authLog.info(f"Connected to device: {validDeviceIP}")
                    sshAccess.enable()
                    authLog.info(f"Generating hostname for {validDeviceIP}")
                    shHostnameOut = re.sub(".mgmt.internal.das|.cm.mgmt.internal.das|.mgmt.wellpoint.com|.caremore.com|.healthcore.local","", validDeviceIP)
                    shHostnameOut = shHostnameOut + '#'
                    authLog.info(f"Hostname for {validDeviceIP}: {shHostnameOut}")

                    authLog.info(f"Command input by the user:{username}, command:{shCommand}")
                    # print(f"INFO: Running command:{shCommand}, on device {validDeviceIP}")
                    shCommandOut = sshAccess.send_command(shCommand)
                    authLog.info(f"Automation successfully run the command: {shCommand} on device: {validDeviceIP}")
                    authLog.info(f"{shHostnameOut}{shCommand}\n{shCommandOut}")
                    # print(f"INFO: Command successfully executed")

                    filename = filterFilename(shCommand)
                    authLog.info(f"This is the filename:{filename}")

                    with open(f"Outputs/{filename} for device {validDeviceIP}.txt", "a") as file:
                        file.write(f"User {username} connected to device IP {validDeviceIP}\n\n")
                        file.write(f"{shHostnameOut}{shCommand}\n{shCommandOut}")
                        authLog.info(f"File:{file} successfully created")

                    if shCommandOut: 
                        with open(f"Outputs/General Outputs.txt", "a") as file:
                            file.write(f"{shHostnameOut}{shCommand}\n{shCommandOut}\n")
                            authLog.info(f"File:General Outputs.txt successfully created andinfo added")
                    
                    outText = f"{shHostnameOut}{shCommand}\n{shCommandOut}"
                    results.append(outText)

                except Exception as error:
                    # print(f"ERROR: An error occurred: {error}\n", traceback.format_exc())
                    authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}")
                    authLog.error(traceback.format_exc(),"\n")
                    failedDevices(username,validDeviceIP,error)
                    results.append(f"Error on {validDeviceIP}, error: {error}")
         
        except Exception as error:
            # print(f"ERROR: An error occurred: {error}\n", traceback.format_exc())
            authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}")
            authLog.error(traceback.format_exc(),"\n")
            failedDevices(username,validDeviceIP,error)   
    return "\n\n".join(results)  