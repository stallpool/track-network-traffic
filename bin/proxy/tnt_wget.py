import os.path

def config(HOME, proxy_host_port, cacert_file):
   f = open(os.path.join(HOME, ".wgetrc"), "w+")
   f.write("""
use_proxy=yes
ca_certificate={0}
http_proxy={1}
https_proxy={1}""".format(
      cacert_file, proxy_host_port
   ))
   f.close()
