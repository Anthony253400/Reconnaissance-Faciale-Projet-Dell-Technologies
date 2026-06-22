FROM python:3.11-slim-bookworm

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

# 4. Installation PyTorch (CUDA 12.1)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 5. Dépendances critiques pour torchreid
RUN pip install --no-cache-dir numpy cython scipy gdown

# 6. Reste des dépendances
RUN pip install --no-cache-dir -r requirements.txt

# 7. Compilation torchreid
RUN pip install --no-cache-dir --no-build-isolation git+https://github.com/KaiyangZhou/deep-person-reid.git

COPY . .
EXPOSE 8000
CMD ["uvicorn", "siteWeb.main:app", "--host", "0.0.0.0", "--port", "8000"]
