#!/bin/sh
VERSION=v5

# build the container image
podman build --runtime=runc -t local_gemma3_4b:$VERSION .

# run the container
podman run --runtime=runc \
  --gpus=all \
  --secret huggingface_token \
  -e PROMPT="Tell me the about the different styles of painting in art history." \
  local_gemma3_4b:$VERSION