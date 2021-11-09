import os.path

def config(HOME, proxy_host_port, cacert_file):
   f = open(os.path.join(HOME, ".curlrc"), "w+")
   f.write("cacert={0}\nproxy={1}\n".format(
      cacert_file, proxy_host_port
   ))
   f.close()
