import os
import os.path
import tempfile
import subprocess

JAVA_HOME = os.getenv("JAVA_HOME")

def config(HOME, proxy_host_port, cacert_file):
   if not JAVA_HOME:
      print("JAVA_HOME is not found, skip to configure java")
      return None

   fid, name = tempfile.mkstemp()
   os.close(fid)
   os.remove(name)
   p = subprocess.Popen(
      "{0} -importcert -noprompt -alias tnt_proxy -storepass changeit -keystore {1} -trustcacerts -file {2}".format(
         os.path.join(JAVA_HOME, "bin", "keytool"),
         name, cacert_file
      ),
      shell=True
   )
   p.wait()
   return name
