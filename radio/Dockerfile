FROM alpine:latest

RUN set -xe && apk --no-cache add mpd mpc dumb-init avahi

VOLUME ["/var/lib/mpd"]
VOLUME ["/var/lib/mpd/music"]
VOLUME ["/tmp"]

ADD ["start.sh", "/start.sh"]
ADD ["mpd.conf", "/etc/mpd.conf"]

RUN chown -R mpd:audio /etc/mpd.conf
RUN chmod +x /start.sh

EXPOSE 6600

ENTRYPOINT ["/start.sh"]
CMD ["mpd", "--stdout", "--no-daemon", "-v"]
