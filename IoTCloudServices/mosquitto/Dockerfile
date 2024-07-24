FROM debian:buster
RUN apt update && apt upgrade -y
RUN apt install -y mosquitto mosquitto-clients
RUN touch /etc/mosquitto/passwd
RUN mosquitto_passwd -b /etc/mosquitto/passwd fic_server fic_password
CMD ["usr/sbin/mosquitto", "-c", "/etc/mosquitto/mosquitto.conf"]