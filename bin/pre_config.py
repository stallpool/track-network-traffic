import sys
import os
import os.path

sys.path.append(
   os.path.join(
      os.path.dirname(__file__),
      "proxy"
   )
)

USAGEDOC = """Usage: python {0} <proxy_host> <proxy_port> <cacert_path>
python {0} 127.0.0.1 8080 ~/.mitmproxy/mitmproxy-ca-cert.pem""".format(sys.argv[0])

HOME = os.getenv('HOME')
if sys.platform == 'win32':
   HOME = os.getenv('USERPROFILE')

BACKUPLIST = [
   ".curlrc", ".wgetrc", ".npmrc",
   os.path.join(".config", "pip", "pip.conf"),
   os.path.join(".pip", "pip.conf"),
   os.path.join(".gradle", "gradle.properties"),
   os.path.join(".m2", "settings.xml"),
   os.path.join(".mvn", "jvm.config"),
]

def usage():
   print(USAGEDOC)
   exit(1)

def act(cacert_file, proxy_host_port):
   for x in BACKUPLIST:
      origin = os.path.join(HOME, x)
      target = origin + '.tnt'
      if not os.path.isfile(origin):
         continue
      os.rename(origin, target)

   import tnt_curl
   tnt_curl.config(HOME, proxy_host_port, cacert_file)
   import tnt_wget
   tnt_wget.config(HOME, proxy_host_port, cacert_file)
   import tnt_pip
   tnt_pip.config(HOME, proxy_host_port, cacert_file)
   import tnt_npm
   tnt_npm.config(HOME, proxy_host_port, cacert_file)
   import tnt_java_base
   javacert = tnt_java_base.config(HOME, proxy_host_port, cacert_file)
   if javacert:
      import tnt_maven
      tnt_maven.config(HOME, proxy_host_port, javacert)
      import tnt_gradle
      tnt_gradle.config(HOME, proxy_host_port, javacert)
   import tnt_golang
   tnt_golang.config(HOME, proxy_host_port, cacert_file)

def main():
   argc = len(sys.argv)
   if not HOME:
      print("ERROR: env HOME is not set")
      exit(1)
   if argc <= 3: return usage()

   proxy_host = sys.argv[1]
   proxy_port = sys.argv[2]
   cacert_file = os.path.abspath(sys.argv[3])
   proxy_host_port = "{0}:{1}".format(proxy_host, proxy_port)
   act(cacert_file, proxy_host_port)

if __name__ == '__main__':
   main()
