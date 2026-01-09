from log import authLog
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException

import socket
import getpass
import csv
import traceback

def checkIsDigit(input_str):
    try:
        authLog.info(f"String successfully validated selection number {input_str}, from checkIsDigit function.")
        return input_str.strip().isdigit()
    
    except Exception as error:
        authLog.error(f"Invalid option chosen: {input_str}, error: {error}")
        authLog.error(traceback.format_exc())
                
def validateIP(deviceIP):
    hostnamesResolution = [
        f'{deviceIP}.mgmt.internal.das',
        f'{deviceIP}.cm.mgmt.internal.das',
        f'{deviceIP}.mgmt.wellpoint.com'
    ]
        
    def checkConnect22(ipAddress, port=22, timeout=3):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connectTest:
                connectTest.settimeout(timeout)
                connectTestOut = connectTest.connect_ex((ipAddress, port))
                return connectTestOut == 0
        except socket.error as error:
            authLog.error(f"Device {ipAddress} is not reachable on port TCP 22.")
            authLog.error(f"Error:{error}\n{traceback.format_exc()}")
            return False

    def validIP(ip):
        try:
            socket.inet_aton(ip)
            authLog.info(f"IP successfully validated: {deviceIP}")
            return True
        except socket.error:
            authLog.error(f"IP: {ip} is not an IP Address, will attempt to resolve hostname.")
            return False

    def resolveHostname(hostname):
        try:
            hostnameOut = socket.gethostbyname(hostname)
            authLog.info(f"Hostname successfully validated: {hostname}")
            return hostnameOut
        except socket.gaierror:
            authLog.error(f"Was not posible to resolve hostname: {hostname}")
            return None

    if validIP(deviceIP):
        if checkConnect22(deviceIP):
            authLog.info(f"Device IP {deviceIP} is reachable on Port TCP 22.")
            print(f"INFO: Device IP {deviceIP} is reachable on Port TCP 22.")
            return deviceIP

    for hostname in hostnamesResolution:
        resolvedIP = resolveHostname(hostname)
        if resolvedIP and checkConnect22(resolvedIP):
            authLog.info(f"Device IP {hostname} is reachable on Port TCP 22.")
            print(f"INFO: Device IP {hostname} is reachable on Port TCP 22.")
            return hostname    

    hostnameStr = ', '.join(hostnamesResolution)  
    
    authLog.error(f"Not a valid IP address or hostname: {hostnameStr}")
    authLog.error(traceback.format_exc())
    print(f"ERROR: Invalid IP address or hostname: {hostnameStr}")

    with open('invalidDestinations.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([hostnameStr])
    
    return None

def requestLogin(validIPs):
    while True:
            username = input("Please enter your username: ")
            password = getpass.getpass("Please enter your password: ")
            #execPrivPassword = getpass.getpass("Please input your enable password: ")

            for deviceIP in validIPs:
                netDevice = {
                    'device_type': 'cisco_xe',
                    'ip': deviceIP,
                    'username': username,
                    'password': password,
                    'secret': password
                }

                authLog.info(f"Successful saved credentials for username: {username}")

            return validIPs, username, netDevice

def checkYNInput(stringInput):
    return stringInput.strip().lower() in ['y', 'n']

def logInCSV(validDeviceIP, filename="", *args):
    # print(f"INFO: File created: {filename}")
    with open(f'Outputs/{filename}.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([validDeviceIP, *args])
        authLog.info(f"Appended device: {validDeviceIP} to file {filename}")

def genTxtFile(validDeviceIP, username, filename="", *args):
    with open(f"Outputs/{validDeviceIP} {filename}.txt","a") as failedDevices:
        failedDevices.write(f"User {username} connected to {validDeviceIP}\n\n")
        for arg in args:
            if isinstance(arg, dict):
                for key,values in arg.items():
                    failedDevices.write(f"{key}: ")
                    failedDevices.write(", ".join(str(v) for v in values))
                    failedDevices.write("\n")
            
            elif isinstance(arg, list):
                for item in arg:
                    failedDevices.write(item)
                    failedDevices.write("\n")

            elif isinstance(arg, str):
                failedDevices.write(arg + "\n")

from fpdf import FPDF
from datetime import datetime
import logging


authLog = logging.getLogger("authLog")
logging.basicConfig(level=logging.INFO)

def createPDF(devicesErrList, user):
    dateHour = datetime.now()
    dateHourOut = dateHour.strftime("%Y-%m-%d %H:%M:%S")

    authLog.info(f"Automation is creating the PDF file for error disabled interfaces, requested by user: {user}")
    pdf = FPDF()
    pdf.add_page()

    
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 12, "Error Disabled Interfaces", ln=True, align='C')

   
    pdf.image("elevance.png", x=10, y=12, w=34)
    pdf.image("Kyndryl.png", x=165, y=12, w=34)

    pdf.ln(6)

  
    pdf.set_font("Arial", '', 14)
    pdf.set_text_color(0, 0, 0)
    authLog.info(f"Results from {dateHourOut} - User: {user}")
    pdf.cell(0, 10, f"Results from {dateHourOut} - User: {user}", ln=True)

   
    pdf.set_draw_color(0, 102, 204)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    pdf.ln(5)

    
    def print_table_header():
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(60, 10, "Device", border=1, fill=True)
        pdf.cell(0, 10, "Interface", border=1, ln=True, fill=True)
        pdf.set_font("Arial", '', 12)

   
    print_table_header()

   
    pdf.set_fill_color(245, 245, 245)

    line_height = 6
    col_width_device = 60
    col_width_interface = 130

    for deviceIP, interfaces in devicesErrList:
        interface_text = ', '.join(interfaces)
        authLog.info(f"Appending Device IP: {deviceIP}, interfaces: {interface_text}")

        device_lines = pdf.multi_cell(col_width_device, line_height, deviceIP, split_only=True)
        interface_lines = pdf.multi_cell(col_width_interface, line_height, interface_text, split_only=True)
        max_lines = max(len(device_lines), len(interface_lines))
        row_height = max_lines * line_height

      
        if pdf.get_y() + row_height > pdf.page_break_trigger:
            pdf.add_page()
            print_table_header()

        x = pdf.get_x()
        y = pdf.get_y()

      
        pdf.set_xy(x, y)
        pdf.multi_cell(col_width_device, line_height, deviceIP, border=0, fill=False)

        
        pdf.set_xy(x + col_width_device, y)
        pdf.multi_cell(col_width_interface, line_height, interface_text, border=0, fill=False)

       
        pdf.rect(x, y, col_width_device + col_width_interface, row_height)
        pdf.line(x + col_width_device, y, x + col_width_device, y + row_height)

        pdf.set_y(y + row_height)

    pdf.ln(10)

    authLog.info(f"PDF file created: Error Disable Interfaces Report.pdf, requested by user: {user}")
    pdf.output("Error Disable Interfaces Report.pdf")
