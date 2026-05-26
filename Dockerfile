# Imagen base con soporte CUDA para aceleración por GPU
FROM nvidia/cuda:12.2.0-base-ubuntu22.04

# Evitar prompts interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# 1. Cambiar los espejos de Ubuntu a un mirror HTTPS seguro (Kernel.org)
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|https://mirrors.kernel.org/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com/ubuntu/|https://mirrors.kernel.org/ubuntu/|g' /etc/apt/sources.list

# 2. Agregar el flag para ignorar la verificación de pares en el handshake inicial (por si la imagen base de Nvidia no tiene los certificados SSL instalados todavía). 
# Nota: Esto es 100% seguro porque los paquetes de Ubuntu se siguen validando por sus claves GPG internas.
RUN apt-get -o Acquire::https::Verify-Peer=false update && apt-get -o Acquire::https::Verify-Peer=false install -y \
     python3.11 \
     python3-pip \
     ocrmypdf \
     tesseract-ocr-spa \
     ghostscript \
     unpaper \
     poppler-utils \
     libgl1-mesa-glx \
     libglib2.0-0 \
     libsm6 \
     libxext6 \
     libxrender1 \
     libqt5gui5 \
     && rm -rf /var/lib/apt/lists/*
     
# Instalación de 'uv'
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copia del código fuente (necesario antes de instalar en modo editable)
COPY . .

# Instalamos a nivel sistema dentro del contenedor usando uv
RUN uv pip install --python python3.11 --system -e .

# Variables de entorno por defecto
ENV DEBUG_MODE=0
ENV OLLAMA_HOST=http://host.docker.internal:11434

# Usamos python3 global en lugar del entorno virtual
CMD ["python3.11", "main.py"]