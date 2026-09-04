FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


RUN ln -s /usr/bin/python3.10 /usr/local/bin/python || true
RUN ln -s /usr/bin/pip3 /usr/local/bin/pip || true

RUN python -m pip install --upgrade pip setuptools wheel

RUN python -m pip install \
    torch==2.1.2 \
    torchvision==0.16.2 \
    torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu121

RUN python -m pip install -U openmim

RUN mim install "mmcv==2.1.0"

COPY requirements.txt /app/requirements.txt

RUN python -m pip install -r /app/requirements.txt

COPY app /app/app
COPY configs /app/configs
COPY checkpoints /app/checkpoints

RUN mkdir -p /app/data/input /app/data/output


EXPOSE 8000