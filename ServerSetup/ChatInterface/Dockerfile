FROM golang:1.24-alpine3.21 as builder
LABEL authors="Aleutian AI"

WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY *.go ./
RUN go build -o Server

FROM alpine:3.21
COPY --from=builder /app/Server ./
COPY index.html ./
 # if you change the port, change it in the CMD arg too
EXPOSE 12321
CMD ["./Server", "12321"]