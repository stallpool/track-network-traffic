import os.path

def config(HOME, proxy_host_port, cacert_file):
   f = open(os.path.join(HOME, ".npmrc"), "w+")
   f.write("""
https-proxy=http://{1}
proxy=http://{1}
cafile={0}""".format(
      cacert_file, proxy_host_port
   ))
   f.close()
