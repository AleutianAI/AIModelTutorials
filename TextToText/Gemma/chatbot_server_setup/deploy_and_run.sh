#!/bin/sh
VERSION=v3

# build the container image
podman build --runtime=runc -t local_gemma3_4b_interactive_chatbot:$VERSION .

podman stop gemma_python_llm_server
podman rm gemma_python_llm_server

# run the container
podman run --runtime=runc \
  -p 12322:12322 \
  --gpus=all \
  --secret huggingface_token \
  --network=gemma-test-network \
  --name=gemma_python_llm_server \
  --replace \
  local_gemma3_4b_interactive_chatbot:$VERSION