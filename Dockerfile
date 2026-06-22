FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV HTTP_PROXY=$HTTP_PROXY
ENV HTTPS_PROXY=$HTTPS_PROXY
ENV NO_PROXY=$NO_PROXY
ENV DEBIAN_FRONTEND=noninteractive

# 2. Installation de Python 3.11 depuis les dépôts Ubuntu (sans PPA)
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
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

# 3. Forcer Python 3.11
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

WORKDIR /app

COPY requirements.txt .

# 4. PyTorch version stable
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
    torch==2.1.0 \
    torchvision==0.16.0 \
    torchaudio==2.1.0

RUN pip3 install --no-cache-dir numpy cython scipy gdown

RUN pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install --no-cache-dir --no-build-isolation \
    git+https://github.com/KaiyangZhou/deep-person-reid.git

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]