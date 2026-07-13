import psycopg2

ROUTERS = ["R1", "R2", "R3"]

DB_CONFIG = {
    "host": "localhost",
    "dbname": "network_lab",
    "user": "netadmin",
    "password": "labpassword123",
    "port": "5432",
}

def get_two_last_rows(router_name):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM config_backups WHERE router_name = %s ORDER BY created_at DESC LIMIT 2", (router_name,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def main():
    for router_name in ROUTERS:
        rows = get_two_last_rows(router_name)
        if len(rows) < 2:
            print(f"El router {router_name} no tiene suficientes registros")
            continue
        if rows[0][2] == rows[1][2]:
            print(f"El router {router_name} no ha realizado cambios")
        else:
            print(f"El router {router_name} ha realizado cambios")

if __name__ == "__main__":
    main()
