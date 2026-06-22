import paramiko
from datetime import datetime
import os

ROUTERS = [
    {"name": "R1", "host": "192.168.99.1"},
    {"name": "R2", "host": "192.168.99.2"},
    {"name": "R3", "host": "192.168.99.3"},
]

USERNAME = "root"
KEY_PATH = "/home/jefe_de_jefes/network-automation-lab/.ssh/frr_automation"
BACKUP_DIR = "/home/jefe_de_jefes/network-automation-lab/backups"

def get_config(host, username, key_path):
    private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(hostname=host, username=username, pkey=private_key, timeout=5)
    stdin, stdout, stderr = client.exec_command("cat /etc/frr/frr.conf")
    output = stdout.read().decode()
    client.close()

    return output

def save_backup(name, config_text):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{BACKUP_DIR}/{name}_{timestamp}.conf"

    with open(filename, "w") as f:
        f.write(config_text)

    print(f"Guardado: {filename}")

def main():
    fallos = []
    for router in ROUTERS:
        print(f"=== Conectando a {router['name']} ({router['host']}) ===")
        try:
            config_text = get_config(router["host"], USERNAME, KEY_PATH)
            save_backup(router["name"], config_text)
        except Exception as e:
            print(f"ERROR al conectar con {router['name']}: {e}")
            fallos.append((router["name"], str(e)))

    print("\n---Resumen---")
    if fallos:
        print("=== Fallos ===")
        for nombre, error in fallos:
            print(f"{nombre}: {error}")
    else:
        print("Routers respaldados correctamente")

if __name__ == "__main__":
    main()
