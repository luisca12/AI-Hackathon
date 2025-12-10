from netmiko import ConnectHandler
# from functions import logInCSV
from log import authLog

from threading import Lock
import concurrent.futures
from tqdm import tqdm
import traceback
import getpass
import os
import re

aclCommnd = "snmp-server group grpallRO v3 priv read fullview write noview notify fullview"
aclCommndNX = "no snmp-server user anthemnmsa use-ipv4acl SNMP-RO"
writeMem = "copy run start"
verifyCommd = "show run | inc grpallRO"
verifyCommndNX = "show snmp user anthemnmsa"
removeNXSNMP = "no snmp-server user anthemnmsa"
userNx = "username anthemnmsa role vdc-admin"
NXcred = "snmp-server user anthemnmsa vdc-admin auth sha PASSWORD priv aes-128 PASSWORD"

def aclRemoval(validIPs, username, password):
    # This function is to remove the ACL from a SNMP group 
    results = []
    
    for validDeviceIP in validIPs:
        try:
            validDeviceIP = validDeviceIP.strip()
            currentNetDevice = {
                'device_type': 'cisco_xe', #'cisco_xe' 'cisco_nxos'
                'ip': validDeviceIP,
                'username': username,
                'password': password,
                'secret': password,
                'global_delay_factor': 2.0,
                'timeout': 120,
                'session_log': 'Outputs/netmikoLog.txt',
                'verbose': False,
                'session_log_file_mode': 'append'
            }

            # tqdm.write(f"INFO: Connecting to device {validDeviceIP}...")
            with ConnectHandler(**currentNetDevice) as sshAccess:
                authLog.info(f"User {username} is now running commands at: {validDeviceIP}")
                authLog.info(f"Generating hostname for {validDeviceIP}")
                shHostnameOut = re.sub(".mgmt.internal.das|.cm.mgmt.internal.das|.mgmt.wellpoint.com","#", validDeviceIP)
                authLog.info(f"Hostname for {validDeviceIP}: {shHostnameOut}")
                # tqdm.write(f"INFO: This is the hostname: {shHostnameOut}")
                sshAccess.enable()
                
                # tqdm.write(f"Configuring: {aclCommnd}, on device: {validDeviceIP}")
                
                # userNxOUT = sshAccess.send_config_set(userNx) # For Nexus only
                # tqdm.write(f"{shHostnameOut}{userNx}\n{userNxOUT}")
                # authLog.info(f"{shHostnameOut}{userNx}\n{userNxOUT}")
                
                
                # NXcredOut = sshAccess.send_config_set(NXcred) # For Nexus only
                # tqdm.write(f"{shHostnameOut}{NXcred}\n{NXcredOut}")
                # authLog.info(f"{shHostnameOut}{NXcred}\n{NXcredOut}")
                
                
                aclCommndOut = sshAccess.send_config_set(aclCommnd) # For Nexus aclCommndNX, for IOS-XE aclCommnd
                authLog.info(f"{shHostnameOut}{aclCommnd}\n{aclCommndOut}")
                print(f"Removing ACL from SNMP Group on device {validDeviceIP}:\n{aclCommndOut}") #\n{shHostnameOut}{aclCommnd}

                # tqdm.write(f"Verifying config with: {verifyCommd}, on device: {validDeviceIP}")
                verifyCommdOut = sshAccess.send_command_timing(verifyCommd) # For Nexus verifyCommndNX, for IOS-XE verifyCommd
                # tqdm.write(f"{shHostnameOut}{verifyCommd}\n{verifyCommdOut}")
                authLog.info(f"{shHostnameOut}{verifyCommd}\n{verifyCommdOut}")

                if "access 61" in verifyCommdOut: # For Nexus "ipv4:SNMP-RO", for IOS-XE "access 61"
                    # tqdm.write(f"INFO: Device:{validDeviceIP}, not configured properly")
                    authLog.info(f"Device:{validDeviceIP}, not configured properly")
                    # logInCSV(validDeviceIP, "Failed to configure devices")

                else:
                    print(f"INFO: Device:{validDeviceIP}, configured properly\n")
                    authLog.info(f"Device:{validDeviceIP}, configured properly")
                    # logInCSV(validDeviceIP, "Successfully configured devices", verifyCommdOut)
                    outText1 = f"ACL from SNMP Group on device {validDeviceIP} removed successfully"
                
                writeMemOut = sshAccess.send_command_timing(writeMem)
                # tqdm.write(f"INFO: Running configuration saved for device {validDeviceIP}")
                authLog.info(f"Running configuration saved for device {validDeviceIP}\n{shHostnameOut}{writeMem}\n{writeMemOut}")
            
                # results.append(outText)
                # results.append(outText1)

        except Exception as error:
            # tqdm.write(f"ERROR: An error occurred: {error}\n{traceback.format_exc()}")
            authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}\n{traceback.format_exc()}")
            results.append(f"Error on {validDeviceIP}, error: {error}")
            # logInCSV(validDeviceIP, "Failed Devices", error)

def aclRemovalThread(validIPs, username, password, maxThreads=100):
    with concurrent.futures.ThreadPoolExecutor(max_workers=maxThreads) as executor:
        futureToIP = {
            executor.submit(aclRemoval, validDeviceIP, username, password): validDeviceIP
            for validDeviceIP in validIPs
        }
        
        for future in tqdm(concurrent.futures.as_completed(futureToIP), total=len(futureToIP), desc="Testing devices") :
            ipAddress = futureToIP[future]
            try:
                future.result()
            except Exception as error:
                authLog.error(f"IP Address: {ipAddress} with thread failed with exception/error: {error}\n{traceback.format_exc()}")
                # logInCSV(ipAddress, "Devices Threads with errors", "Error:", error)

    os.system("PAUSE")
