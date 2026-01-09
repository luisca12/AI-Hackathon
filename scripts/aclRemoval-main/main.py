import argparse
import os

def main():
    from utils import mkdir
    # Crear carpetas logs/Outputs si no existen
    mkdir()

    from functions import validateIP
    from commandsCLI import aclRemoval
    from log import authLog

    """
    Modo NO interactivo, pensado para ser llamado desde FastAPI / backend.

    Ejemplo de uso:
      python main.py \
        --devices "10.1.1.1,10.1.1.2" \
        --username luis \
        --password cisco \
    """

    parser = argparse.ArgumentParser(
        description="Automated ACL removal"
    )
    parser.add_argument(
        "--devices",
        required=True,
        help="Comma-separated list of device IPs/hostnames. Example: '10.1.1.1,10.1.1.2'",
    )
    parser.add_argument(
        "--username",
        required=True,
        help="Username to use for device login.",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Password to use for device login (also used as enable password).",
    )

    args = parser.parse_args()

    def validateIPs(devices: str):
        """
        Recibe un string tipo '10.1.1.1,10.1.1.2'
        Valida cada IP/hostname con validateIP y devuelve la lista de válidas.
        """
        validIPs = []
        raw_list = devices.split(",")
        for ip in raw_list:
            ip = ip.strip()
            if not ip:
                continue
            ipOut = validateIP(ip)
            if ipOut is not None:
                validIPs.append(ipOut)
            else:
                authLog.info(f"IP address {ip} is invalid or unreachable.")

        if not validIPs:
            raise ValueError("No valid IP addresses found after validation.")

        return validIPs

    # Validar IPs/hostnames igual que antes
    validIPs = validateIPs(args.devices)

    # netDevice solo necesita password/secret,
    # la IP la pone showCommands por cada device.

    authLog.info(
        f"[aclRemoval-main] Non-interactive run. "
        f"Devices={validIPs}, username={args.username}"
    )

    # Reusar tu función existente
    aclRemoval(validIPs, args.username, args.password)

    print("INFO: Non-interactive run completed successfully.")
    print(f"INFO: Devices: {validIPs}")


    # return showCommandOut


if __name__ == "__main__":
    main()
