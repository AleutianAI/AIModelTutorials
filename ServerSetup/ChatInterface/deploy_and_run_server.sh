#!/bin/bash

VERSION=v2

# build the image
podman build --runtime=runc -t go_chatbot_httpserver:$VERSION .

# run the image
podman run --runtime=runc -p 12321:12321 go_chatbot_httpserver:$VERSION