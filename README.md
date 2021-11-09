# Track Network Traffic (TNT)

Track network traffic: make exploring your software supply chain possible

## Setup

```
python3 -m virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## How to use

### one line example

```
bash ./bin/tnt.bash -o . -- npm install uuid
```

### docker example

```
docker run --name build --rm -d \
   -v /tmp/output:/opt/output \
   tnt:latest \
   bash /opt/tnt/bin/tnt.bash -o /opt/output -- go get github.com/gogs/gogs"
```

### docker build example

```
export OUTPUT_DIR=.
export TNT_DOCKER_GATEWAY=`ifconfig docker0 | grep -o -E 'inet 172[0-9.]+' | cut -d ' ' -f 2`
export TNT_DOCKER=`which docker`
alias docker=`pwd`/bin/docker

cat > /tmp/Dockerfile <<EOF
FROM ubuntu:20.04
RUN curl -L https://www.google.com
EOF

docker build --no-cache -t test:test -f /tmp/Dockerfile .
```

### report.json sample

```
{
   "items": [
      {
         "content": "binary",
         "host": "www.google.com",
         "path": [
            "/ HTTP/2.0"
         ],
         "protocol": "https"
      }
   ]
}
```


## Build `tnt` package

```
# all on a Linux machine

# tnt-lin.tar.gz
echo tnt for Linux version lin-`cat ./bin/version/lin`
bash ./build_lin.sh

# tnt-mac.tar.gz
echo tnt for MacOS version mac-`cat ./bin/version/mac`
bash ./build_mac.sh

# tnt-win.zip
echo tnt for Windows version win-`cat ./bin/version/win`
bash ./build_win.sh
```


## Build Template (template.tar.gz)

### httpry

> original: https://github.com/jbittel/httpry

> dependency:
>
> ref: http://www.tcpdump.org/release/libpcap-1.7.4.tar.gz
>
> we recommend libpcap 1.7.4 since it works even on centos 5.8

> httpry replacement on Windows
>
> nmcap, ref: https://www.microsoft.com/en-us/download/4865

```
export PCAP=/path/to/compiled/libpcap-1.7.4
# static will help to run httpry on more similar OSes
# tested build a static linked one on CentOS 5.8; and it works also on Debian 10, Centos 6, 7, Photon3, ...
gcc -static -Wall -O3 -funroll-loops -I/usr/include/pcap -I/usr/local/include/pcap \
   -I ${PCAP}/include \
   -o httpry httpry.c format.c methods.c utility.c rate.c ${PCAP}/lib/libpcap.a \
   -lm -pthread

# if meet problem on libpcap_usb_linux, just slient sscanf
# save as _fake.c and add after rate.c in above gcc command line
// in libpcap_usb_linux
// but we do not need the module
// fake the sscanf
int __isoc99_sscanf(const char *str, const char *format, ...) {
   return -1;
}
```

### mitmproxy for manylinux

- use docker to build python3.6 with mitmproxy (low GLIBC support to run on manylinux)

```
FROM centos:centos5

RUN mkdir /var/cache/yum/base/ \
    && mkdir /var/cache/yum/extras/ \
    && mkdir /var/cache/yum/updates/ \
    && mkdir /var/cache/yum/libselinux/ \
    && echo "http://vault.centos.org/5.11/os/x86_64/" > /var/cache/yum/base/mirrorlist.txt \
    && echo "http://vault.centos.org/5.11/extras/x86_64/" > /var/cache/yum/extras/mirrorlist.txt \
    && echo "http://vault.centos.org/5.11/updates/x86_64/" > /var/cache/yum/updates/mirrorlist.txt \
    && echo "http://vault.centos.org/5.11/centosplus/x86_64/" > /var/cache/yum/libselinux/mirrorlist.txt

RUN yum install -y gcc gcc44 zlib-devel python-setuptools readline-devel wget make perl
RUN yum install -y bzip2-devel sqlite-devel expat-devel

RUN wget https://www.openssl.org/source/old/1.0.2/openssl-1.0.2u.tar.gz
RUN tar zxf openssl-1.0.2u
RUN cd openssl-1.0.2u \
    &&./config --prefix=`pwd`/dist -fPIC \
    && make && make install

RUN wget https://www.python.org/ftp/python/3.6.13/Python-3.6.13.tgz
RUN tar zxf Python-3.6.13.tgz
# point SSL to the right location in Setup.dist file
ADD Setup.dist Python-3.6.13/Modules/
RUN cd Python-3.6.13 \
    && ./configure --prefix=`pwd`/dist \
    && make && make install \
    && cd dist/bin \
    && ./python3 -m pip install mitmproxy
    && cd ../../..
    && ./Python-3.6.13/dist/bin/mitmdump --help
```

- expose `./Python-3.6.13/dist` as a base folder on host machine
- copy `httpry` binary into the base folder
- make a tarball `template.tar.gz` to contain `bin` `lib` folder in the base folder
- for Windows, it should be template.zip; for MacOS, it should be template-mac.tar.gz
