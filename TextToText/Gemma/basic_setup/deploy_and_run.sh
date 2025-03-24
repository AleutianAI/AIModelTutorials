#!/bin/sh
VERSION=v1

# build the container image
podman build --runtime=runc -t local_gemma3_4b:$VERSION .

# run the container
podman run --runtime=runc \
  --gpus=all \
  --secret huggingface_token \
  local_gemma3_4b:$VERSION