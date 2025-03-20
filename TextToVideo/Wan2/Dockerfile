FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

LABEL authors="AleutianAI"

WORKDIR /app
RUN mkdir /app/tensor_cache

# Install dependencies
RUN apt update && apt install -y python3 python3-pip python3-venv git wget ffmpeg
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN python3 -m pip install --upgrade pip
COPY requirements.txt .
COPY replacement_utils.py .
RUN python3 -m pip install huggingface_hub
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install flash-attn --no-build-isolation

# Clone Wan2.1
RUN git clone https://github.com/Wan-Video/Wan2.1.git
RUN mv replacement_utils.py Wan2.1/wan/utils/utils.py

# Set the working directory to Wan
WORKDIR /app/Wan2.1

RUN huggingface-cli download Wan-AI/Wan2.1-T2V-1.3B --local-dir ./Wan2.1-T2V-1.3B

CMD python3 generate.py --task t2v-1.3B --offload_model True --t5_cpu --size 832*480 --ckpt_dir ./Wan2.1-T2V-1.3B --prompt "$PROMPT"
