FROM ubuntu:20.04

WORKDIR /opt/tnt
RUN apt-get update && \
    apt-get install -y sudo 
RUN apt-get install -y python2 python3 python-pip python3-pip nodejs npm curl wget
RUN apt-get install -y openjdk-11-jdk gradle maven
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

RUN cd /opt && \
    curl -L -O https://golang.org/dl/go1.16.4.linux-amd64.tar.gz && \
    tar zxf go1.16.4.linux-amd64.tar.gz && \
    rm go1.16.4.linux-amd64.tar.gz && \
    ln -s /opt/go/bin/go /bin/go
ENV GOROOT=/opt/go
COPY ./bin/. /opt/tnt/bin/
ADD template.tar.gz /opt/tnt/bin/template.tar.gz
RUN cd /opt/tnt && \
    tar zxf ./bin/template.tar.gz && \
    rm ./bin/template.tar.gz && \
    echo 'export PATH=$PATH:/opt/go/bin:/opt/tnt/bin' >> ~/.profile
