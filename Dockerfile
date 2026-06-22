# 1. Image de base officielle avec support GPU
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# 2. Installation de Python 3.11 et des bibliothèques système (OpenCV + MediaPipe)
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    git \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    libgles2 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

# 3. Forcer l'utilisation de Python 3.11
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

WORKDIR /app

COPY requirements.txt .

# 4. Installation de l'écosystème PyTorch Linux stable (CUDA 12.1)
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Pré-installation des outils et dépendances critiques requises par les métadonnées de torchreid
RUN pip3 install --no-cache-dir numpy cython scipy gdown

# Étape A : On installe le reste de vos dépendances depuis le requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Étape B : Compilation et installation finale de torchreid sans isolation
RUN pip3 install --no-cache-dir --no-build-isolation git+https://github.com/KaiyangZhou/deep-person-reid.git

# 5. On copie le reste du code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "siteWeb.main:app", "--host", "0.0.0.0", "--port", "8000"]