import psycopg2
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DB_CONFIG, ROUTERS

def get_last_two_backups(router_name):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT config_text, created_at
        FROM config_backups
        WHERE router_name = %s
        ORDER BY created_at DESC
        LIMIT 2
        """,
        (router_name,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def main():
    for r in ROUTERS:
        name = r["name"]
        print(f"=== {name} ===")
        rows = get_last_two_backups(name)

        if len(rows) < 2:
            print("    No hay suficientes backups para comparar (se necesitan al menos 2).")
            continue

        config_actual, fecha_actual = rows[0]
        config_anterior, fecha_anterior = rows[1]

        if config_actual == config_anterior:
            print(f"    Sin cambios entre {fecha_anterior} y {fecha_actual}.")
        else:
            print(f"    CAMBIO DETECTADO entre {fecha_anterior} y {fecha_actual}.")

if __name__ == "__main__":
    main()
