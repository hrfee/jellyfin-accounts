FROM python:3.8.2-buster

RUN apt update -y

RUN apt install unzip python3-pip python3-dev libsasl2-dev libldap2-dev libssl-dev -y

RUN cd /opt && wget https://github.com/hrfee/jellyfin-accounts/archive/master.zip

RUN cd /opt && unzip master.zip

RUN pip install pyOpenSSL

RUN pip install -r /opt/jellyfin-accounts-master/requirements.txt

RUN cd /opt/jellyfin-accounts-master && python3 setup.py install

ENTRYPOINT [ "python3", "/usr/local/bin/jf-accounts", "-d", "/data" ]
