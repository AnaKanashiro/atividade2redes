FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para PostgreSQL
# CORREÇÃO: Adicionados os pacotes que faltavam
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY backend/ .

# Criar diretório para arquivos estáticos
RUN mkdir -p /app/static

# Expor porta interna
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "app.py"]