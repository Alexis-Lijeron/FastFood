# Dockerfile para PostgreSQL
FROM postgres:16-alpine

# Variables de entorno para configuración inicial
ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
ENV POSTGRES_DB=${POSTGRES_DB}

# Puerto por defecto de PostgreSQL
EXPOSE 5432

# Volumen para persistencia de datos
VOLUME ["/var/lib/postgresql/data"]
