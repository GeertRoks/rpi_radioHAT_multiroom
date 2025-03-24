FROM alpine:latest
RUN echo "https://dl-cdn.alpinelinux.org/alpine/edge/testing/" >> /etc/apk/repositories
RUN apk add --no-cache snapcast-server librespot
ADD ["snapserver.conf", "/etc/snapserver.conf"]

EXPOSE 1704 1705 1780
ENTRYPOINT "snapserver"
