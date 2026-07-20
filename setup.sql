CREATE USER "tu-user" WITH PASSWORD 'tu-password-aqui';
CREATE DATABASE network_lab OWNER "tu-user";

\c network_lab

CREATE TABLE config_backups (
    id SERIAL PRIMARY KEY,
    router_name VARCHAR(50) NOT NULL,
    config_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

GRANT ALL PRIVILEGES ON TABLE config_backups TO "tu-user";
GRANT USAGE, SELECT ON SEQUENCE config_backups_id_seq TO "tu-user";
