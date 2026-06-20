FROM quay.io/frrouting/frr:9.1.2

# Crear config base de FRR
RUN mkdir -p /etc/frr && \
    echo "frr version 9.1.2" > /etc/frr/frr.conf && \
    echo "frr defaults traditional" >> /etc/frr/frr.conf && \
    echo "!" >> /etc/frr/frr.conf && \
    chown -R frr:frr /etc/frr

# Activar el daemon de OSPF (viene desactivado por defecto en la imagen base)
RUN sed -i 's/^ospfd=no/ospfd=yes/' /etc/frr/daemons

# Instalar SSH y configurar autenticación por llave (sin contraseña)
RUN apk add --no-cache openssh && \
    ssh-keygen -A && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Copiar la llave pública para autenticación
COPY frr_automation.pub /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys

# Script de arranque que fija el ulimit antes de iniciar FRR
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
