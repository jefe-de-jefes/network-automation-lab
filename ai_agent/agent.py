from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL
import tools

# Inicializar cliente de Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Historial de conversacion — se acumula durante la sesion
conversation_history = []

# Instrucciones base que definen el comportamiento del agente
SYSTEM_PROMPT = """Eres NetOps Agent, un asistente experto en redes que ayuda a administrar 
una red de 3 routers FRR con OSPF. Tienes acceso a datos en tiempo real de los routers 
y a un historial de configuraciones en PostgreSQL.

Cuando te den datos de la red, analízalos y responde en español de forma clara y concisa.
Si detectas algo anormal (interfaces caídas, vecinos OSPF perdidos, cambios no esperados),
menciónalo explícitamente y sugiere qué revisar."""


def detect_intent(user_input):
    """
    Detecta qué herramienta usar según lo que el usuario preguntó.
    Devuelve los datos relevantes para pasarle a Gemini.
    """
    text = user_input.lower()

    # Detectar si menciona un router específico
    router_name = None
    for r in ["r1", "r2", "r3"]:
        if r in text:
            router_name = r.upper()
            break

    # Decidir qué herramienta usar
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
    """
    Procesa la pregunta del usuario:
    1. Detecta si necesita datos de la red
    2. Construye el contexto para Gemini
    3. Llama a Gemini con el historial completo
    4. Devuelve la respuesta
    """
    # Obtener datos de la red si son necesarios
    network_data = detect_intent(user_input)

    # Construir el mensaje con contexto de red si lo hay
    if network_data:
        full_message = f"{user_input}\n\nDatos de la red:\n{network_data}"
    else:
        full_message = user_input

    # Agregar mensaje del usuario al historial
    conversation_history.append({
        "role": "user",
        "parts": [{"text": full_message}]
    })

    # Llamar a Gemini con el historial completo
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
        ] + conversation_history
    )

    answer = response.text

    # Agregar respuesta al historial
    conversation_history.append({
        "role": "model",
        "parts": [{"text": answer}]
    })

    return answer


def main():
    print("=" * 50)
    print("NetOps Agent iniciado")
    print("Red: R1 (192.168.99.1), R2 (192.168.99.2), R3 (192.168.99.3)")
    print("Escribe 'salir' para terminar")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nTú: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["salir", "exit", "quit"]:
                print("Cerrando NetOps Agent.")
                break

            print("\nAgente: ", end="", flush=True)
            response = ask_agent(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\nCerrando NetOps Agent.")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
