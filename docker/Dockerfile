# Usamos Python 3.11 para máxima compatibilidad con librerías de Data Science
FROM python:3.11-slim

# Evitar archivos .pyc y logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Instalar dependencias del sistema (Linux)
# Necesario para compilar psycopg2 (Base de datos) y numpy/pandas
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar dependencias de Python
# Copiamos primero solo el txt para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiar el código fuente
COPY . .

# 4. Exponer puerto de Streamlit
EXPOSE 8501

# 5. Healthcheck (Opcional, para saber si está vivo)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 6. Comando de arranque
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]