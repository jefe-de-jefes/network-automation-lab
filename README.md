# Network Automation Lab

Laboratorio de automatización de redes construido desde cero, con el objetivo de demostrar capacidad real de ingeniería de software aplicada a infraestructura de red — más allá de la configuración manual de dispositivos.

---

## Arquitectura general

```
┌─────────────────────────────────────────────────────────┐
│                    Kali Linux (host)                    │
│                                                         │
│  automation/           configs/         backups/        │
│  ├── backup.py         ├── r1.conf      (gitignored)    │
│  ├── restore.py        ├── r2.conf                      │
│  └── check_changes.py  └── r3.conf                      │
│                                                         │
│  PostgreSQL 16 (Docker)    tap0 (192.168.99.5/28)       │
└──────────────┬──────────────────────────────────────────┘
               │ SSH / SFTP (red de gestión OOB)
    ┌──────────▼──────────────────────────────────────┐
    │             GNS3 — Topología virtual            │
    │                                                 │
    │        [R1]────────[R2]────────[R3]             │
    │         │╲          │          /│               │
    │         │  ╲        │        /  │               │
    │        SW1   └─────[R2]────┘  SW3               │
    │         │          SW2          │               │
    │      PC4,5,6     PC1,2,3     PC7,8,9            │
    │                                                 │
    │      Switch-MGMT (red de gestión separada)      │
    └─────────────────────────────────────────────────┘
```

---

## Stack tecnológico

| Componente | Tecnología | Razón de elección |
|---|---|---|
| Routing | FRRouting 9.1.2 (Docker) | Independiente de fabricante; usado en producción en Meta, Cumulus Linux y switches blancos |
| Orquestador de red | GNS3 | Topología virtual con soporte nativo de contenedores Docker |
| Automatización | Python 3 + Paramiko | SSH programático, mismo patrón que herramientas de automatización de redes en producción |
| Persistencia | PostgreSQL 16 (Docker) | Historial consultable de configuraciones con timestamp |
| Transferencia de archivos | SFTP (sobre SSH) | Transferencia segura sin depender de acceso directo al Docker host |
| Autenticación | SSH con llaves Ed25519 | Sin contraseñas; llave privada nunca sale del host |
| Entorno | Kali Linux | Plataforma de desarrollo y control |

---

## Topología de red

### Red de datos — OSPF área 0

3 routers FRR en topología de triángulo (full mesh). OSPF converge automáticamente y provee **redundancia real de rutas**: si un enlace cae, OSPF recalcula y el tráfico continúa por el camino alternativo sin intervención manual.

**Tabla de enlaces inter-router:**

| Enlace | Subred | IP Router A | IP Router B |
|---|---|---|---|
| R1 ↔ R2 | 10.0.0.4/30 | 10.0.0.5 (R1-eth1) | 10.0.0.6 (R2-eth0) |
| R1 ↔ R3 | 10.0.0.0/30 | 10.0.0.1 (R1-eth0) | 10.0.0.2 (R3-eth1) |
| R2 ↔ R3 | 10.0.0.8/30 | 10.0.0.9 (R2-eth1) | 10.0.0.10 (R3-eth0) |

**LANs de departamento (/28 — 14 hosts usables por segmento):**

| Departamento | Subred | Gateway | PCs |
|---|---|---|---|
| Depto 1 (R1) | 10.1.0.0/28 | 10.1.0.1 | PC4, PC5, PC6 |
| Depto 2 (R2) | 10.2.0.0/28 | 10.2.0.1 | PC1, PC2, PC3 |
| Depto 3 (R3) | 10.3.0.0/28 | 10.3.0.1 | PC7, PC8, PC9 |

### Red de gestión Out-of-Band (OOB)

**Decisión de diseño deliberada:** la administración de los routers corre en una red completamente separada del tráfico de datos (`192.168.99.0/28`), conectada al host vía interfaz TAP virtual.

Esto garantiza que, aunque la red de datos tenga un problema (loop, saturación, fallo de OSPF), el acceso administrativo a los routers siga disponible — práctica estándar en redes empresariales y de datacenter conocida como **Out-of-Band Management**.

| Dispositivo | Interfaz | IP de gestión |
|---|---|---|
| R1 | eth3 | 192.168.99.1 |
| R2 | eth3 | 192.168.99.2 |
| R3 | eth3 | 192.168.99.3 |
| Host (Kali) | tap0 | 192.168.99.5 |

---

## Scripts de automatización

### `backup.py` — Respaldo automático vía SSH

Se conecta a los 3 routers vía SSH con autenticación por llave (sin contraseña), descarga `/etc/frr/frr.conf` de cada uno usando `Paramiko`, y lo inserta en PostgreSQL con timestamp automático.

Incluye **tolerancia a fallos**: si un router no responde (timeout de 5 segundos), el script reporta el error específico y continúa con los demás sin detenerse — comportamiento esperado en cualquier script de automatización de producción.

```bash
python3 automation/backup.py
```

Salida esperada:
```
=== Conectando a R1 (192.168.99.1) ===
    Guardado en base de datos.
=== Conectando a R2 (192.168.99.2) ===
    Guardado en base de datos.
=== Conectando a R3 (192.168.99.3) ===
    Guardado en base de datos.

--- Resumen ---
Todos los routers respaldados correctamente.
```

---

### `restore.py` — Restauración de configuración vía SFTP

Sube los archivos de configuración desde `configs/` hacia cada router vía SFTP (sobre la misma conexión SSH autenticada con llave). Útil después de que GNS3 recrea los contenedores al reiniciar el proyecto, ya que FRR arranca con configuración vacía por defecto.

```bash
python3 automation/restore.py
```

> **Nota:** después de correr `restore.py`, hacer Stop/Start de cada nodo desde GNS3 para que FRR relea el archivo de configuración restaurado.

---

### `check_changes.py` — Detección de cambios de configuración

Consulta PostgreSQL y compara los dos backups más recientes de cada router. Si el `config_text` difiere entre ambos, reporta que hubo un cambio — base para un sistema de auditoría de configuraciones no autorizadas.

```bash
python3 automation/check_changes.py
```

Salida esperada (sin cambios):
```
=== R1 ===
    Sin cambios entre 2026-06-22 00:44:28 y 2026-06-22 01:00:49.
=== R2 ===
    Sin cambios entre 2026-06-22 00:44:29 y 2026-06-22 01:00:49.
=== R3 ===
    Sin cambios entre 2026-06-22 00:44:29 y 2026-06-22 01:00:49.
```

---

## Problema técnico resuelto: bug de ulimit en contenedores FRR

Durante el setup inicial, todos los contenedores de FRR morían inmediatamente al arrancar con este error:

```
WATCHFRR: out of memory: failed to allocate 17179868672 bytes for Thread Poll Info object
```

### Diagnóstico por aislamiento de variables

Se descartaron hipótesis sucesivamente:

1. **Memoria/CPU del host** — el host tiene 11GB RAM, suficiente. Agregar `--memory` y `--cpus` al contenedor no cambió nada. ❌
2. **Versión/build de la imagen** — se probaron `frrouting/frr:latest` (Docker Hub) y `quay.io/frrouting/frr:9.1.2` (Quay). Mismo error exacto, al byte. ❌
3. **cgroups v2 / cgroupns** — el sistema usa cgroups v2, se probó `--cgroupns=host`. Sin efecto. ❌
4. **`ulimit -n` heredado por Docker** — dentro del contenedor, `ulimit -n` reportaba **2,147,483,584** (prácticamente ilimitado), vs. 1024 en el host normal.

**Causa raíz confirmada:** `watchfrr` reserva al arrancar una pequeña estructura de memoria por cada file descriptor que el límite del sistema *podría* llegar a usar — no los que usa realmente, sino el máximo teórico. Con un límite de 2,147,483,584:

```
2,147,483,584 descriptores × 8 bytes = 17,179,868,672 bytes ≈ 16 GB
```

El sistema no puede satisfacer esa reserva, mata el proceso.

### Solución

Se creó un `entrypoint.sh` personalizado que fija el límite a un valor razonable **antes** de que FRR arranque, sin depender de flags externos que GNS3 no permite pasar en su versión actual:

```bash
#!/bin/bash
ulimit -n 1024
exec /sbin/tini -- /usr/lib/frr/docker-start
```

Este script se incorporó en una imagen Docker propia (`frr-gns3:local`) construida sobre la imagen oficial de FRR.

---

## Imagen Docker personalizada

La imagen base oficial de FRR requirió tres modificaciones para funcionar correctamente en este entorno:

1. **Fix del ulimit** — `entrypoint.sh` con `ulimit -n 1024` antes de lanzar FRR
2. **Activar `ospfd`** — viene desactivado por defecto en `/etc/frr/daemons`; se activa con `sed` durante el build
3. **SSH con autenticación por llave** — se instala `openssh`, se deshabilita autenticación por contraseña, y se copia la llave pública a `/root/.ssh/authorized_keys`

```dockerfile
FROM quay.io/frrouting/frr:9.1.2

RUN mkdir -p /etc/frr && \
    echo "frr version 9.1.2" > /etc/frr/frr.conf && \
    echo "frr defaults traditional" >> /etc/frr/frr.conf && \
    echo "!" >> /etc/frr/frr.conf && \
    chown -R frr:frr /etc/frr

RUN sed -i 's/^ospfd=no/ospfd=yes/' /etc/frr/daemons

RUN apk add --no-cache openssh && \
    ssh-keygen -A && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

COPY frr_automation.pub /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

---

## Autenticación SSH por llave Ed25519

Los scripts de Python se autentican con los routers usando un par de llaves Ed25519 dedicado al proyecto. La llave privada nunca sale del host y está excluida del repositorio vía `.gitignore`. La llave pública está embebida en la imagen Docker.

```bash
ssh-keygen -t ed25519 -f .ssh/frr_automation -N ""
```

---

## Cómo levantar el lab

### Prerequisitos

- Kali Linux (o Debian/Ubuntu)
- GNS3 con soporte Docker habilitado
- Docker Engine
- Python 3.10+

### 1. Construir la imagen FRR

```bash
cd docker/frr-router
docker build -t frr-gns3:local .
```

### 2. Levantar PostgreSQL

```bash
docker run -d \
  --name postgres-lab \
  -e POSTGRES_USER=netadmin \
  -e POSTGRES_PASSWORD=labpassword123 \
  -e POSTGRES_DB=network_lab \
  -p 5432:5432 \
  postgres:16
```

Crear la tabla en PostgreSQL:

```sql
CREATE TABLE config_backups (
    id SERIAL PRIMARY KEY,
    router_name VARCHAR(50) NOT NULL,
    config_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Configurar la interfaz de gestión (cada reinicio)

```bash
sudo ip addr add 192.168.99.5/28 dev tap0
sudo ip link set dev tap0 up
```

### 4. Abrir GNS3 y cargar el proyecto

Una vez que GNS3 levanta los contenedores (vacíos por defecto), restaurar la configuración:

```bash
python3 automation/restore.py
```

Hacer **Stop/Start** de cada router desde GNS3 para que FRR aplique la configuración restaurada.

### 5. Verificar conectividad

```bash
ping 192.168.99.1   # R1
ping 192.168.99.2   # R2
ping 192.168.99.3   # R3
```

### 6. Correr los scripts

```bash
# Respaldar configuraciones actuales
python3 automation/backup.py

# Detectar cambios respecto al backup anterior
python3 automation/check_changes.py
```

---

## Estructura del repositorio

```
network-automation-lab/
├── automation/
│   ├── backup.py           # Backup vía SSH → PostgreSQL, tolerante a fallos
│   ├── restore.py          # Restauración vía SFTP
│   └── check_changes.py    # Detección de cambios entre backups
├── configs/
│   ├── r1.conf             # Configuración FRR de R1 (IPs + OSPF)
│   ├── r2.conf             # Configuración FRR de R2 (IPs + OSPF)
│   └── r3.conf             # Configuración FRR de R3 (IPs + OSPF)
├── docker/
│   └── frr-router/
│       ├── Dockerfile          # Imagen personalizada: ulimit fix + ospfd + SSH
│       ├── entrypoint.sh       # Script de arranque con ulimit corregido
│       └── frr_automation.pub  # Llave pública SSH (la privada va en .ssh/, gitignored)
└── .gitignore              # Excluye .ssh/ y backups/
```

---

## Posibles extensiones

- Integrar imágenes Cisco IOSv (vía licencia CML) para automatización con Netmiko sobre dispositivos Cisco reales
- Agregar autenticación MD5/SHA en OSPF para demostrar hardening de protocolos de routing
- Implementar red de gestión OOB con redundancia (VRF de gestión enrutada en vez de estrella plana)
- Dashboard web con FastAPI + historial de cambios consultable por fecha/router
- Alertas automáticas cuando `check_changes.py` detecta una diferencia inesperada
