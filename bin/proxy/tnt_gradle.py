import os
import os.path

def config(HOME, proxy_host_port, cacert_file):
   gradledir = os.path.join(HOME, ".gradle")
   os.makedirs(gradledir, exist_ok=True)

   f = open(os.path.join(gradledir, "gradle.properties"), "w+")
   proxy_parts = proxy_host_port.split(':')
   f.write("""
systemProp.http.proxyHost={1}
systemProp.http.proxyPort={2}
systemProp.https.proxyHost={1}
systemProp.https.proxyPort={2}
systemProp.javax.net.ssl.trustStore={0}
systemProp.javax.net.ssl.trustStorePassword=changeit
""".format(
      cacert_file, proxy_parts[0], proxy_parts[1]
   ))
   f.close()
