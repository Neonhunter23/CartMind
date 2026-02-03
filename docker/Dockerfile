FROM python:3.11-slim


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app

# Instalar dependencias del SISTEMA (Linux)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de PYTHON
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el CÓDIGO fuente del proyecto
# Copiamos lo que hay en la carpeta actual al contenedor
COPY .. .

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando de inicio: Lanzar la App
# --server.address=0.0.0.0 es obligatorio para que sea visible desde fuera del contenedor
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]