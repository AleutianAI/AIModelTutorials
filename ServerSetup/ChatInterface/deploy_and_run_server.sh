#!/bin/bash

VERSION=v3

# build the image
podman build --runtime=runc -t go_chatbot_httpserver:$VERSION .

# run the image
podman run \
  --runtime=runc \
  -p 12321:12321 \
  --network=gemma-test-network \
  --replace \
  --name=gemma_golang_webserver \
  go_chatbot_httpserver:$VERSION