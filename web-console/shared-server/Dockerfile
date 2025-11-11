FROM ubuntu:24.04

ARG USER_PASSWORD

RUN apt-get update && \
    apt-get install -y curl wget openssh-server openssh-client && \
    apt-get install -y nmap telnet mtr traceroute net-tools snmp iputils-ping netcat && \
    apt-get install -y htop less nano mc jq figlet && \
    apt-get autoremove && \
    apt-get autoclean && \
    mkdir /var/run/sshd && \
    adduser --gecos "" --uid 1002 --shell /bin/bash --home /home/default default;

RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN echo "default:$USER_PASSWORD" | chpasswd

COPY sc.sh tc.sh /usr/share/connections/
RUN chmod 755 -R /usr/share/connections;

COPY .ssh/config /home/default/.ssh/config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
