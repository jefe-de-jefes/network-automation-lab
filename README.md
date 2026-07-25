# Network Automation Lab — AIOps

Laboratorio de automatización de redes con capa de inteligencia artificial conversacional. Combina infraestructura de red virtual (FRRouting, OSPF, GNS3), automatización vía SSH/SFTP con Python, persistencia en PostgreSQL, y un agente de IA que permite consultar y diagnosticar la red en lenguaje natural.

Construido en dos fases: primero la infraestructura de automatización base, después la capa de agente conversacional sobre esa misma infraestructura.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Kali Linux (host)                    │
│                                                         │
│  automation/          ai_agent/          config.py      │
│  ├── backup.py        ├── agent.py       (centralizado) │
│  ├── restore.py       └── tools.py                      │
│  └── check_changes.py                                   │
│                                                         │
│  PostgreSQL 16 (Docker)    tap0 (192.168.99.5/28)       │
│  Gemini API (google-genai) SSH/SFTP (Paramiko)          │
└──────────────┬──────────────────────────────────────────┘
               │ Red de gestión Out-of-Band (192.168.99.0/28)
    ┌──────────▼──────────────────────────────────────┐
    │             GNS3 — Topología virtual            │
    │                                                 │
    │   [R1]────────[R2]────────[R3]  ← OSPF área 0  │
    │    │╲          │          /│                    │
    │    │  ╲        │        /  │                    │
    │   SW1   └──────────────┘  SW3                  │
    │    │          SW2          │                    │
    │  PC4,5,6    PC1,2,3     PC7,8,9                │
    │                                                 │
    │   Switch-MGMT (red de gestión separada)         │
    └─────────────────────────────────────────────────┘
```

### Flujo del agente de IA

```
Usuario escribe → detect_intent() identifica herramienta →
tools.py consulta SSH o PostgreSQL → datos reales →
Gemini razona sobre esos datos → respuesta en español
```

---

## Stack tecnológico

| Componente | Tecnología | Razón |
|---|---|---|
| Routing | FRRouting 9.1.2 (Docker) | Independiente de fabricante; usado en producción en datacenters modernos |
| Orquestador de red | GNS3 | Topología virtual con soporte nativo de contenedores Docker |
| Automatización | Python 3 + Paramiko | SSH/SFTP programático, mismo patrón que herramientas de producción |
| Persistencia | PostgreSQL 16 (Docker) | Historial consultable de configuraciones con timestamp |
| Agente de IA | Gemini API (google-genai) | Razonamiento en lenguaje natural sobre datos reales de la red |
| Autenticación SSH | Ed25519 (llave pública/privada) | Sin contraseñas; llave privada nunca sale del host |
| Entorno | Kali Linux | Plataforma de desarrollo y control |

---

## Estructura del repositorio

```
network-automation-lab/
├── ai_agent/
│   ├── agent.py           # Loop conversacional e integración con Gemini
│   └── tools.py           # Herramientas de consulta SSH y PostgreSQL
├── automation/
│   ├── backup.py          # Respaldo de configuraciones vía SSH → PostgreSQL
│   ├── restore.py         # Restauración de configuraciones vía SFTP
│   └── check_changes.py   # Auditoría de cambios entre backups
├── configs/
│   ├── r1.conf            # Configuración base de R1 (IPs + OSPF)
│   ├── r2.conf            # Configuración base de R2 (IPs + OSPF)
│   └── r3.conf            # Configuración base de R3 (IPs + OSPF)
├── docker/
│   └── frr-router/
│       ├── Dockerfile         # Imagen personalizada: ulimit fix + ospfd + SSH
│       ├── entrypoint.sh      # Script de arranque con ulimit corregido
│       └── frr_automation.pub # Llave pública SSH
├── config.py              # Configuración centralizada importada por todos los módulos
├── requirements.txt       # Dependencias del proyecto
├── setup.sql              # Script para crear la base de datos desde cero
└── .gitignore             # Protege .env, credenciales SSH y archivos temporales
```

---

## Topología de red

### Red de datos — OSPF área 0

3 routers FRR en topología de triángulo (full mesh). OSPF converge automáticamente con redundancia real: si un enlace cae, el tráfico continúa por el camino alternativo sin intervención manual.

| Enlace | Subred | IP Router A | IP Router B |
|---|---|---|---|
| R1 ↔ R2 | 10.0.0.4/30 | 10.0.0.5 (R1-eth1) | 10.0.0.6 (R2-eth0) |
| R1 ↔ R3 | 10.0.0.0/30 | 10.0.0.1 (R1-eth0) | 10.0.0.2 (R3-eth1) |
| R2 ↔ R3 | 10.0.0.8/30 | 10.0.0.9 (R2-eth1) | 10.0.0.10 (R3-eth0) |

### LANs de departamento

| Departamento | Subred | Gateway | PCs |
|---|---|---|---|
| Depto 1 (R1) | 10.1.0.0/28 | 10.1.0.1 | PC4, PC5, PC6 |
| Depto 2 (R2) | 10.2.0.0/28 | 10.2.0.1 | PC1, PC2, PC3 |
| Depto 3 (R3) | 10.3.0.0/28 | 10.3.0.1 | PC7, PC8, PC9 |

### Red de gestión Out-of-Band (OOB)

La administración de los routers corre en una red completamente separada del tráfico de datos (`192.168.99.0/28`), conectada al host vía interfaz TAP virtual. Si la red de datos falla, el acceso administrativo sigue disponible — práctica estándar en redes empresariales.

| Dispositivo | Interfaz | IP de gestión |
|---|---|---|
| R1 | eth3 | 192.168.99.1 |
| R2 | eth3 | 192.168.99.2 |
| R3 | eth3 | 192.168.99.3 |
| Host (Kali) | tap0 | 192.168.99.5 |

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/jefe-de-jefes/network-automation-lab.git
cd network-automation-lab
```

### 2. Instalar dependencias de Python

```bash
pip3 install -r requirements.txt --break-system-packages
```

### 3. Construir la imagen Docker de FRR

```bash
docker build -t frr-gns3:local docker/frr-router/
```

### 4. Generar par de llaves SSH

```bash
ssh-keygen -t ed25519 -f ~/.ssh/frr_automation -N ""
cp ~/.ssh/frr_automation.pub docker/frr-router/frr_automation.pub
docker build -t frr-gns3:local docker/frr-router/
```

### 5. Levantar PostgreSQL y crear la base de datos

```bash
docker run -d \
  --name postgres-lab \
  -e POSTGRES_USER=tu-usuario \
  -e POSTGRES_PASSWORD=tu-password \
  -e POSTGRES_DB=network_lab \
  -p 5432:5432 \
  postgres:16

docker exec -i postgres-lab psql -U tu-usuario -d network_lab < setup.sql
```

---

## Configuración

Crea el archivo `.env` en la raíz del proyecto:

```
GEMINI_API_KEY=tu-api-key-aqui
DB_USER=tu-usuario
DB_PASSWORD=tu-password
```

Obtén tu API key de Gemini en [aistudio.google.com](https://aistudio.google.com). El tier gratuito es suficiente para uso normal.

Ajusta `config.py` si tus IPs de routers o nombre de base de datos son distintos a los valores por defecto.

---

## Cómo usar el proyecto

### Arranque del laboratorio

Cada vez que abras GNS3 los contenedores arrancan vacíos. El flujo de arranque es:

```bash
# 1. Abrir GNS3 y dar Start a la topología

# 2. Copiar configuraciones a los contenedores recién creados
docker cp configs/r1.conf GNS3.FRR-Router-1.<id>:/etc/frr/frr.conf
docker cp configs/r2.conf GNS3.FRR-Router-2.<id>:/etc/frr/frr.conf
docker cp configs/r3.conf GNS3.FRR-Router-3.<id>:/etc/frr/frr.conf
# Hacer Stop/Start de los routers en GNS3 para que apliquen la config

# 3. Levantar la red de gestión
sudo ip addr add 192.168.99.5/28 dev tap0
sudo ip link set dev tap0 up

# 4. Levantar PostgreSQL
docker start postgres-lab
```

### Scripts de automatización

```bash
# Respaldar configuraciones actuales → PostgreSQL
python3 automation/backup.py

# Restaurar configuraciones guardadas → routers vía SFTP
python3 automation/restore.py

# Detectar cambios entre los dos backups más recientes
python3 automation/check_changes.py
```

### Agente de IA conversacional

```bash
python3 ai_agent/agent.py
```

El agente detecta la intención de la pregunta y consulta la herramienta correspondiente:

| Palabras clave | Acción |
|---|---|
| "estado", "interfaces", "ospf", "cómo está" | Consulta SSH en tiempo real |
| "cambio", "cambió", "diferencia" | Compara backups en PostgreSQL |
| "backup", "historial", "respaldo" | Trae historial de PostgreSQL |
| "red", "resumen", "todo", "todos" | Estado completo de los 3 routers |

**Ejemplo de conversación:**

```
NetOps Agent iniciado
Red: R1 (192.168.99.1), R2 (192.168.99.2), R3 (192.168.99.3)

Tú: ¿cómo está r1?
Agente: R1 está operativo. 4 interfaces activas: eth0 (10.0.0.1/30),
eth1 (10.0.0.5/30), eth2 (10.1.0.1/28), eth3 (192.168.99.1/28).
OSPF activo con 2 vecinos: R2 y R3.

Tú: ¿hubo cambios en la configuración?
Agente: No se detectaron cambios en R1 entre el último backup
(2026-06-22 01:00:49) y el anterior (2026-06-22 00:53:09).

Tú: salir
Cerrando NetOps Agent.
```

---

## Problema técnico resuelto: bug de ulimit en FRR

Los contenedores de FRR morían al arrancar con este error:

```
WATCHFRR: out of memory: failed to allocate 17179868672 bytes
```

**Causa:** Docker heredaba al contenedor un `ulimit -n` de 2,147,483,584. `watchfrr` reserva memoria proporcional a ese límite al arrancar: 2,147,483,584 × 8 bytes = 16 GB — más RAM de la disponible en el sistema.

**Diagnóstico:** se descartaron sucesivamente hipótesis de memoria del host, versión de imagen, cgroups v2 y cgroupns hasta confirmar el ulimit como causa raíz mediante la fórmula exacta que producía el número del error.

**Solución:** `entrypoint.sh` personalizado que fija el límite antes de lanzar FRR:

```bash
#!/bin/bash
ulimit -n 1024
exec /sbin/tini -- /usr/lib/frr/docker-start
```

---

## Limitación conocida del agente

La detección de intención usa `if/elif` — toma la primera coincidencia y no combina múltiples herramientas en una sola consulta. Si la pregunta mezcla dos temas, solo se obtienen datos del primero que coincida.

**Mejora futura:** implementar *function calling* nativo de Gemini para que el modelo decida qué herramientas usar y pueda llamar varias en paralelo.

---

## Posibles extensiones

- Ejecutar backups desde el agente conversacional
- Function calling nativo de Gemini para detección de intención más precisa
- Alertas automáticas vía Telegram o WhatsApp
- Monitoreo periódico con detección proactiva de anomalías
- Soporte para routers Cisco IOS vía Netmiko
