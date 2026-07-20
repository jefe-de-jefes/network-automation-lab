import paramiko
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import ROUTERS, SSH_USERNAME, SSH_KEY_PATH

REMOTE_PATH = "/etc/frr/frr.conf"

def push_config(host, username, key_path, local_config):
    private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, pkey=private_key, timeout=5)
    sftp = client.open_sftp()
    sftp.put(local_config, REMOTE_PATH)
    sftp.close()
    client.close()

def main():
    fallos = []
    print("=== Restaurando configuraciones ===")
    for router in ROUTERS:
        print(f"\n[+] {router['name']} ({router['host']})...")
        try:
            push_config(router["host"], SSH_USERNAME, SSH_KEY_PATH, router["config_file"])
            print(f"    OK: subido correctamente.")
        except Exception as e:
            print(f"    ERROR: {e}")
            fallos.append((router["name"], str(e)))

    print("\n--- Resumen ---")
    if fallos:
        print("Fallos:")
        for nombre, error in fallos:
            print(f"  {nombre}: {error}")
    else:
        print("Todas las configuraciones restauradas correctamente.")

if __name__ == "__main__":
    main()
