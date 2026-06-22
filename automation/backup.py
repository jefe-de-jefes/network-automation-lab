import paramiko
import psycopg2

ROUTERS = [
    {"name": "R1", "host": "192.168.99.1"},
    {"name": "R2", "host": "192.168.99.2"},
    {"name": "R3", "host": "192.168.99.3"},
]

USERNAME = "root"
KEY_PATH = "/home/jefe_de_jefes/network-automation-lab/.ssh/frr_automation"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "network_lab",
    "user": "netadmin",
    "password": "labpassword123",
}

def get_config(host, username, key_path):
    private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(hostname=host, username=username, pkey=private_key, timeout=5)
    stdin, stdout, stderr = client.exec_command("cat /etc/frr/frr.conf")
    output = stdout.read().decode()
    client.close()

    return output

def save_to_db(router_name, config_text):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO config_backups (router_name, config_text) VALUES (%s, %s)",
        (router_name, config_text)
    )

    conn.commit()
    cursor.close()
    conn.close()

def main():
    fallos = []

    for router in ROUTERS:
        print(f"=== Conectando a {router['name']} ({router['host']}) ===")
        try:
            config_text = get_config(router["host"], USERNAME, KEY_PATH)
            save_to_db(router["name"], config_text)
            print(f"    Guardado en base de datos.")
        except Exception as e:
            print(f"    ERROR: {e}")
            fallos.append((router["name"], str(e)))

    print("\n--- Resumen ---")
    if fallos:
        print("Fallos:")
        for nombre, error in fallos:
            print(f"  {nombre}: {error}")
    else:
        print("Todos los routers respaldados correctamente.")

if __name__ == "__main__":
    main()
