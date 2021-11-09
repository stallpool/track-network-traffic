import sys
import os
import os.path

sys.path.append(
   os.path.join(
      os.path.dirname(__file__),
      "proxy"
   )
)

HOME = os.getenv("HOME")
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

def act():
   for x in BACKUPLIST:
      patched = os.path.join(HOME, x)
      backup = patched + ".tnt"
      if os.path.isfile(patched):
         os.remove(patched)
      if os.path.isfile(backup):
         os.rename(backup, patched)

   import tnt_golang
   tnt_golang.revert(HOME)

def main():
   if not HOME:
      print("ERROR: env HOME is not set")
      exit(1)
   act()

if __name__ == "__main__":
   main()
