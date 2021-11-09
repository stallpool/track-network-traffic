import os
import os.path

def config(HOME, proxy_host_port, cacert_file):
   mvndir = os.path.join(HOME, ".mvn")
   m2dir = os.path.join(HOME, ".m2")
   os.makedirs(mvndir, 0o755, exist_ok=True)
   os.makedirs(m2dir, 0o755, exist_ok=True)

   f = open(os.path.join(mvndir, "jvm.config"), "w+")
   f.write("-Djavax.net.ssl.trustStore={0}".format(
      cacert_file
   ))
   f.close()

   proxy_parts = proxy_host_port.split(':')
   f = open(os.path.join(m2dir, "settings.xml"), "w+")
   f.write("""
<settings>
 <proxies>
  <proxy>
   <id>https_proxy</id>
   <active>true</active>
   <protocol>https</protocol>
   <host>{1}</host>
   <port>{2}</port>
  </proxy>
  <proxy>
   <id>http_proxy</id>
   <active>true</active>
   <protocol>http</protocol>
   <host>{1}</host>
   <port>{2}</port>
  </proxy>
 </proxies>
</settings>
""".format(
      cacert_file, proxy_parts[0], proxy_parts[1]
   ))
   f.close()
