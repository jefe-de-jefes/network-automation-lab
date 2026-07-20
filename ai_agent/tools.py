import paramiko
import psycopg2
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import SSH_USERNAME, SSH_KEY_PATH, ROUTERS, DB_CONFIG

def _ssh_connect(host):
    private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=SSH_USERNAME, pkey=private_key, timeout=5)
    return client
def get_router_status(router_name):
    """
    Conecta al router por SSH y obtiene:
    - Estado de interfaces (show interface brief)
    - Vecinos OSPF activos (show ip ospf neighbor)
    Devuelve un diccionario con esa informacion.
    """
    router = next((r for r in ROUTERS if r["name"] == router_name), None)
    if not router:
        return {"error": f"Router {router_name} no encontrado"}

    try:
        client = _ssh_connect(router["host"])

        _, stdout, _ = client.exec_command(
            "ulimit -n 1024 && vtysh -c 'show interface brief'"
        )
        interfaces = stdout.read().decode()

        _, stdout, _ = client.exec_command(
            "ulimit -n 1024 && vtysh -c 'show ip ospf neighbor'"
        )
        ospf_neighbors = stdout.read().decode()

        client.close()

        return {
            "router": router_name,
            "interfaces": interfaces,
            "ospf_neighbors": ospf_neighbors,
        }

    except Exception as e:
        return {"error": str(e)}


def get_recent_backups(router_name, limit=3):
    """
    Consulta PostgreSQL y devuelve los ultimos N backups
    de un router especifico, con fecha y primeras lineas del config.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT router_name, created_at, config_text
            FROM config_backups
            WHERE router_name = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (router_name, limit),
        )

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return {"router": router_name, "backups": [], "mensaje": "Sin backups guardados"}

        backups = []
        for row in rows:
            backups.append({
                "router": row[0],
                "fecha": str(row[1]),
                "config_preview": row[2][:200],
            })

        return {"router": router_name, "backups": backups}

    except Exception as e:
        return {"error": str(e)}


def check_config_changes(router_name):
    """
    Compara los dos backups mas recientes de un router.
    Devuelve si hubo cambio o no, y entre que fechas.
    """
    try:
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
            (router_name,),
        )

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if len(rows) < 2:
            return {
                "router": router_name,
                "resultado": "insuficiente",
                "mensaje": "Se necesitan al menos 2 backups para comparar",
            }

        config_actual, fecha_actual = rows[0]
        config_anterior, fecha_anterior = rows[1]

        hubo_cambio = config_actual != config_anterior

        return {
            "router": router_name,
            "hubo_cambio": hubo_cambio,
            "fecha_anterior": str(fecha_anterior),
            "fecha_actual": str(fecha_actual),
            "mensaje": "Cambio detectado" if hubo_cambio else "Sin cambios",
        }

    except Exception as e:
        return {"error": str(e)}


def get_network_summary():
    """
    Obtiene el estado completo de la red:
    - Estado en vivo de los 3 routers
    - Si hubo cambios recientes en cada uno
    Devuelve todo en un diccionario para que Claude razone sobre el.
    """
    summary = []

    for router in ROUTERS:
        status = get_router_status(router["name"])
        changes = check_config_changes(router["name"])

        summary.append({
            "router": router["name"],
            "status": status,
            "cambios_recientes": changes,
        })

    return summary
