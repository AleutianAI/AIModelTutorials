#!/bin/bash

VERSION=v1

# build the image
podman build --runtime=runc -t go_chatbot_httpserver:$VERSION .

# run the image
podman run --runtime=runc go_chatbot_httpserver:$VERSION