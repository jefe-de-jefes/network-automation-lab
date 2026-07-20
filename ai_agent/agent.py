import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL, ROUTERS
import tools

client = genai.Client(api_key=GEMINI_API_KEY)
conversation_history = []

SYSTEM_PROMPT = """Eres NetOps Agent, un asistente experto en redes que ayuda a administrar 
una red de routers FRR con OSPF. Tienes acceso a datos en tiempo real de los routers 
y a un historial de configuraciones en PostgreSQL.

Cuando te den datos de la red, analízalos y responde en español de forma clara y concisa.
Si detectas algo anormal (interfaces caídas, vecinos OSPF perdidos, cambios no esperados),
menciónalo explícitamente y sugiere qué revisar."""

def detect_intent(user_input):
    text = user_input.lower()

    router_names = [r["name"].lower() for r in ROUTERS]
    router_name = None
    
    for r in router_names:
        if r in text:
            router_name = r.upper()
            break

    if any(w in text for w in ["estado", "interfaz", "interfaces", "ospf", "cómo está", "como esta", "vecino"]):
        target = router_name or "R1"
        data = tools.get_router_status(target)
        return f"Estado actual de {target}:\n{data}"

    elif any(w in text for w in ["cambio", "cambió", "cambio", "diferencia", "modificó"]):
        target = router_name or "R1"
        data = tools.check_config_changes(target)
        return f"Análisis de cambios en {target}:\n{data}"

    elif any(w in text for w in ["backup", "historial", "respaldo"]):
        target = router_name or "R1"
        data = tools.get_recent_backups(target)
        return f"Historial de backups de {target}:\n{data}"

    elif any(w in text for w in ["red", "resumen", "todo", "general", "todos"]):
        data = tools.get_network_summary()
        return f"Resumen general de la red:\n{data}"

    return None

def ask_agent(user_input):
    network_data = detect_intent(user_input)

    if network_data:
        full_message = f"{user_input}\n\nDatos de la red:\n{network_data}"
    else:
        full_message = user_input

    conversation_history.append({"role": "user", "parts": [{"text": full_message}]})

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}] + conversation_history
    )

    answer = response.text
    conversation_history.append({"role": "model", "parts": [{"text": answer}]})
    return answer

def main():
    print("=" * 50)
    print("NetOps Agent iniciado")
    
    # Imprime la topología dinámicamente
    texto_red = ", ".join([f"{r['name']} ({r['host']})" for r in ROUTERS])
    print(f"Red: {texto_red}")
    
    print("Escribe 'salir' para terminar")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nTú: ").strip()
            if not user_input: continue
            if user_input.lower() in ["salir", "exit", "quit"]:
                print("Cerrando NetOps Agent.")
                break
            print("\nAgente: ", end="", flush=True)
            print(ask_agent(user_input))
        except KeyboardInterrupt:
            print("\nCerrando NetOps Agent.")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
