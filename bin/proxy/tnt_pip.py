import os
import os.path

def config(HOME, proxy_host_port, cacert_file):
   pipdir = os.path.join(HOME, ".config", "pip")
   pip1_5dir = os.path.join(HOME, ".pip")
   os.makedirs(pipdir, 0o755, exist_ok=True)
   os.makedirs(pip1_5dir, 0o755, exist_ok=True)

   f = open(os.path.join(pipdir, "pip.conf"), "w+")
   f.write("""
[global]
proxy=http://{1}
cert={0}
""".format(
      cacert_file, proxy_host_port
   ))
   f.close()

   # support older pip, like pip 1.5
   f = open(os.path.join(pip1_5dir, "pip.conf"), "w+")
   f.write("""
[global]
proxy=http://{1}
cert={0}
""".format(
      cacert_file, proxy_host_port
   ))
   f.close()
