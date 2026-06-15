# 1. Utilisation d'une image stable haut de gamme CUDA 12.4, totalement compatible avec ton driver 13.0
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# 2. Désactiver les invites interactives pendant l'installation
ENV DEBIAN_FRONTEND=noninteractive

# 3. Installer Python, Pip, CMake et les paquets requis par OpenCV / InsightFace
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Dossier de travail dans le conteneur
WORKDIR /app

# 5. Copier la liste des paquets Python
COPY requirements.txt .

# 6. Mettre à jour pip et installer tes librairies (PyTorch, OpenCV, InsightFace, etc.)
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 7. Copier tout ton code source dans le conteneur
COPY . .

# 8. Exposer le port de FastAPI
EXPOSE 8000

# 9. Commande de lancement de l'API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]