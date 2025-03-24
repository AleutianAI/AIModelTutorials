#!/bin/sh
VERSION=v1

# build the container image
podman build --runtime=runc -t local_gemma3_4b_interactive_chatbot:$VERSION .

# run the container
podman run --runtime=runc \
  -p 12322:12322 \
  --gpus=all \
  --secret huggingface_token \
  --network=gemma-test-network \
  --name=gemma_python_llm_server \
  local_gemma3_4b_interactive_chatbot:$VERSION