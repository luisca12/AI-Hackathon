from utils import mkdir
import os

def main():    
    mkdir()
    os.system("CLS")
    
    from functions import checkIsDigit
    from auth import Auth
    from commandsCLI import errDisable
    from log import authLog
    from strings import menuString, greetingString, inputErrorString

    greetingString()
    validIPs, username, netDevice = Auth()

    while True:
        menuString(validIPs, username), print("\n")
        selection = input("Please choose the option that yyou want: ")
        if checkIsDigit(selection):
            if selection == "1":
                # This option will fix errDisable interfaces
                errDisable(validIPs, username, netDevice)
            if selection == "2":
                authLog.info(f"User {username} disconnected from the devices {validIPs}")
                authLog.info(f"User {username} logged out from the program.")
                break
        else:
            authLog.error(f"Wrong option chosen {selection}")
            inputErrorString()
            os.system("PAUSE")

if __name__ == "__main__":
    main()