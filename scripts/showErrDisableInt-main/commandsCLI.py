from netmiko import ConnectHandler
from functions import createPDF, checkYNInput
from log import authLog

import traceback
import re

shErroDisable = "show interfaces status err-disabled"
shHostname = "show run | i hostname"
interface = ''
writeMem = 'do write'

errDisableIntPatt = r'[a-zA-Z]+\d+\/(?:\d+\/)*\d+'

recovInt = [
    f'int {interface}',
    'shut',
    'no shut'
]

intErrDisableList = []
devicesErrList = []

def errDisable(validIPs, username, netDevice):
    # This function is to find and fix errDisable Intrfaces
    
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
                'session_log': 'netmikoLog.txt',
                'verbose': True,
                'session_log_file_mode': 'append'
            }

            print(f"INFO: Connecting to device {validDeviceIP}...")
            with ConnectHandler(**currentNetDevice) as sshAccess:
                authLog.info(f"User {username} is now running commands at: {validDeviceIP}")
                sshAccess.enable()
                authLog.info(f"Generating hostname for {validDeviceIP}")
                shHostnameOut = re.sub(".mgmt.internal.das|.cm.mgmt.internal.das|.mgmt.wellpoint.com","#", validDeviceIP)
                hostname = re.sub(".mgmt.internal.das|.cm.mgmt.internal.das|.mgmt.wellpoint.com","", validDeviceIP)
                authLog.info(f"Hostname for {validDeviceIP}: {shHostnameOut}")
                print(f"INFO: This is the hostname: {shHostnameOut}")

                print(f"INFO: Searching and fixing errDisabled interfaces for device: {validDeviceIP}")
                authLog.info(f"Searching and fixing errDisabled interfaces for device: {validDeviceIP}")
                shErroDisableOut = sshAccess.send_command_timing(shErroDisable)
                print(f"{shHostnameOut}{shErroDisable}\n{shErroDisableOut}")
                authLog.info(f"{shHostnameOut}{shErroDisable}\n{shErroDisableOut}")
                shErroDisableOut = re.findall(errDisableIntPatt, shErroDisableOut)
                authLog.info(f"Found the following interfaces in error disable for device {validDeviceIP}: {shErroDisableOut}")

                if shErroDisableOut:
                    devicesErrList.append((hostname, shErroDisableOut))
                    

                    recoverInt = input(f"Do you want to recover the interfaces?(y/n):")
                    while not checkYNInput(recoverInt):
                        print("ERROR: Invalid input. Please enter 'y' or 'n'.\n")
                        authLog.error(f"User tried to choose the option to recover the err-disabled interfaces but failed. Wrong option chosen: {recoverInt}")
                        recoverInt = input("\nDo you want to choose a CSV file?(y/n):")

                    if recoverInt.lower() == "y":
                        for interface in shErroDisableOut:
                            interface = interface.strip()
                            recovInt[0] = f'int {interface}'
                            print(f"INFO: Recovering interface {interface} from errDisabled state on device {validDeviceIP}")
                            authLog.info(f"Recovering interface {interface} on device {validDeviceIP}")
                            recovIntOut = sshAccess.send_config_set(recovInt)
                            print(recovIntOut)
                            authLog.info(f"{recovIntOut}")
                            print(f"INFO: Successfully recovered interface {interface} for device: {validDeviceIP}")
                            authLog.info(f"Successfully recovered interface {interface} for device: {validDeviceIP}")
                            with open(f"Outputs/generalOutputs.txt", "a") as file:
                                file.write(f"INFO: Fixing errDisabled interfaces for device: {validDeviceIP}\n")
                                file.write(f"{shHostnameOut}:\n{recovIntOut}\n")
                        print(f"INFO: Saving configuration for device: {validDeviceIP}")
                        sshAccess.send_config_set(writeMem)
                        authLog.info(f"Saved configuration for device: {validDeviceIP}")
                    else:
                        print(f"INFO: No interfaces will be recovered from device: {validDeviceIP}")
                        authLog.info(f"No interfaces will be recovered from device: {validDeviceIP}")
                else:
                    print(f"INFO: No interfaces were found in errDisable state. Skipping device: {validDeviceIP}")
                    authLog.info(f"No interfaces were found in errDisable state. Skipping device: {validDeviceIP}")

        except Exception as error:
            print(f"ERROR: An error occurred: {error}\n{traceback.format_exc()}")
            authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}\n{traceback.format_exc()}")
            with open(f"failedDevices.csv","a") as failedDevices:
                failedDevices.write(f"{validDeviceIP}\n")
    
    createPDF(devicesErrList, username)
