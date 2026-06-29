FROM python:3.11-slim-bookworm

ENV http_proxy=http://proxy.mtp.supportlabs.dell:80
ENV https_proxy=http://proxy.mtp.supportlabs.dell:80
ENV HTTP_PROXY=http://proxy.mtp.supportlabs.dell:80
ENV HTTPS_PROXY=http://proxy.mtp.supportlabs.dell:80
ENV no_proxy=localhost,127.0.0.1,qdrant
ENV NO_PROXY=localhost,127.0.0.1,qdrant

RUN apt-get update && apt-get install -y \
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

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

#  PyTorch cu117 = seule version qui supporte CC 7.0 (Tesla V100)
RUN pip install --no-cache-dir torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu117

#  onnxruntime-gpu compatible CUDA 11.x / CC 7.0
RUN pip install --no-cache-dir onnxruntime-gpu==1.16.3

# Dépendances critiques pour torchreid
RUN pip install --no-cache-dir numpy cython scipy gdown

# Reste des dépendances (onnxruntime CPU ne doit PAS être dedans)
RUN pip install --no-cache-dir -r requirements.txt

# Compilation torchreid
RUN pip install --no-cache-dir --no-build-isolation git+https://github.com/KaiyangZhou/deep-person-reid.git

COPY . .
EXPOSE 8000
CMD ["uvicorn", "siteWeb.main:app", "--host", "0.0.0.0", "--port", "8000"]