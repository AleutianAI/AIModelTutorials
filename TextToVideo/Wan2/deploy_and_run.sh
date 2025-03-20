#!/bin/sh

PROMPT="A bird landing on one of a group of cacti at sunrise in the southern desert."
VERSION=v6

# Build the Docker image
podman build --runtime=runc -t wan2-image:$VERSION .


podman --debug run --runtime=runc --gpus all -v ~/Documents/:/app/Wan2.1-T2V-1.3B-Diffusers/outputs -e PROMPT="$PROMPT" wan2-image:$VERSION