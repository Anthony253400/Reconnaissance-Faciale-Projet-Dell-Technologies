# 1. Image de base officielle avec support GPU
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# 2. Ajout du PPA deadsnakes SANS passer par l'API Launchpad
RUN apt-get update && apt-get install -y gnupg curl ca-certificates software-properties-common && \
    curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xF23C5A6CF475977595C89F51BA6932366A755776" \
      | gpg --dearmor -o /etc/apt/trusted.gpg.d/deadsnakes.gpg && \
    echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" \
      > /etc/apt/sources.list.d/deadsnakes.list && \
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
    libgles2 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

# 3. Forcer Python 3.11 + installer pip (curl est déjà installé à l'étape 2)
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

WORKDIR /app

COPY requirements.txt .

# 4. PyTorch avec support CUDA 12.1
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

RUN pip3 install --no-cache-dir numpy cython scipy gdown

RUN pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install --no-cache-dir --no-build-isolation git+https://github.com/KaiyangZhou/deep-person-reid.git

COPY . .

EXPOSE 8000

CMD ["uvicorn", "siteWeb.main:app", "--host", "0.0.0.0", "--port", "8000"]