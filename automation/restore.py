import paramiko

ROUTERS = [
    {"name": "R1", "host": "192.168.99.1", "config": "/home/jefe_de_jefes/network-automation-lab/configs/r1.conf"},
    {"name": "R2", "host": "192.168.99.2", "config": "/home/jefe_de_jefes/network-automation-lab/configs/r2.conf"},
    {"name": "R3", "host": "192.168.99.3", "config": "/home/jefe_de_jefes/network-automation-lab/configs/r3.conf"},
]

USERNAME = "root"
KEY_PATH = "/home/jefe_de_jefes/network-automation-lab/.ssh/frr_automation"
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
            push_config(router["host"], USERNAME, KEY_PATH, router["config"])
            print(f"    OK: {router['config']} subido correctamente.")
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
        print("Recuerda hacer Stop/Start de cada router desde GNS3 para que tomen efecto.")

if __name__ == "__main__":
    main()
