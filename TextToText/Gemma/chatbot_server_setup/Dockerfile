FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

LABEL authors="AleutianAI"

COPY . /app
WORKDIR /app

# Install dependencies
RUN apt update && apt install -y python3 python3-pip python3-venv git
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN python3 -m pip install --upgrade pip
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install git+https://github.com/huggingface/transformers@v4.49.0-Gemma-3
EXPOSE 12322

CMD ["python3", "demo_with_chatbot_server.py", "--prompt", "Compare taking a vacation in Florida with taking a vacation in California. Give me the pros and cons and a table comparing the two."]