# TODO: actually it is not only a golang support, it is a generic support
#       may change this file name from tnt_golang.py to tnt_generic.py

import os
import sys
from shutil import copyfile

IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
# ref: https://github.com/golang/go/blob/master/src/crypto/x509/root_linux.go
CACERT_CHECK_LIST = [
   "/etc/ssl/certs/ca-certificates.crt",                # Debian/Ubuntu/Gentoo etc.
   "/etc/pki/tls/certs/ca-bundle.crt",                  # Fedora/RHEL 6
   "/etc/ssl/ca-bundle.pem",                            # OpenSUSE
   "/etc/pki/tls/cacert.pem",                           # OpenELEC
   "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", # CentOS/RHEL 7
   "/etc/ssl/cert.pem",                                 # Alpine Linux
]

def config(HOME, proxy_host_port, cacert_file):
   os.environ["SSL_CERT_FILE"] = cacert_file
   os.environ["https_proxy"] = "http://"+proxy_host_port
   os.environ["http_proxy"] = "http://"+proxy_host_port
   os.environ["HTTPS_PROXY"] = "http://"+proxy_host_port
   os.environ["HTTP_PROXY"] = "http://"+proxy_host_port
   # for Linux only, TODO: support Windows and MacOS
   if not IS_WIN and not IS_MAC:
      with open(cacert_file, 'r') as f:
         catext = f.read()
      for one in CACERT_CHECK_LIST:
         if not os.path.isfile(one): continue
         if os.access(one, os.W_OK):
            # do backup and inject ca-cert
            copyfile(one, one + '.tnt')
            with open(one, 'a') as f:
               f.write('\n')
               f.write(catext)
            break
         # elif:
         #   # TODO: should we try to use sudo cat to inject cert?
   

def revert(HOME):
   if not IS_WIN and not IS_MAC:
      for one in CACERT_CHECK_LIST:
         if not os.path.isfile(one + '.tnt'): continue
         os.rename(one + '.tnt', one)
