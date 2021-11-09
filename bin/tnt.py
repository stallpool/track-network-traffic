import sys
import os
import os.path
import subprocess
import signal
import time

sys.path.append(os.path.dirname(__file__))


IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
PYTHON3 = os.path.join(ROOT_DIR, "python3")
if not os.path.isfile(PYTHON3):
   PYTHON3 = "python3"
LOG_DIR = os.path.join(ROOT_DIR, "runtime", "logs")
OB_DIR = os.path.join(ROOT_DIR, "runtime", "tnt")
DISABLE_CONFIG = False
ENABLE_APPEND_MODE = False
ENABLE_TCPDUMP = False
OB_HOST = "127.0.0.1"
IS_LOCALHOST = True
OB_AUTH = ""
OB_PORT = "8989"
OUTPUT_DIR = "."
COMMAND = ""

def usage():
   print("""Usage:
{0} [-o output_dir] [-a] [-n] [-t] \\
   [-h listen_host -auth user:passwd] [-p listen_port] -- <build command>

Description:
     -o  the dir path to store the result, default is '.'
     -a  append track log into existing supply chain report
     -n  disable default proxy/cacert configuration
     -t  enable tcpdump (sudo permission is required)
     -H  tnt listening host, default is 127.0.0.1
     -p  tnt listening port, default is 8989
  -auth  specify tnt proxy authentication; it is required when
         listening host is not localhost (127.0.0.1)
""".format(sys.argv[0]))
   exit(1)

def version():
   if IS_WINDOWS:
      plat = 'win'
      vname = 'win'
   elif IS_MACOS:
      plat = 'mac'
      vname = 'mac'
   else:
      plat = 'lin'
      vname = 'lin'
   vfilename = os.path.join(ROOT_DIR, 'version', vname)
   with open(vfilename, 'r') as f:
      ver = f.read().strip()
   
   print("tnt version {0}-{1}".format(plat, ver))
   exit(1)

def convert_arg(s):
   if " " in s:
      return '"'+s+'"'
   return s

def parse_args():
   global OUTPUT_DIR, DISABLE_CONFIG, ENABLE_TCPDUMP, OB_PORT, COMMAND, ENABLE_APPEND_MODE
   global OB_HOST, OB_AUTH, IS_LOCALHOST
   for i in range(1, len(sys.argv)):
      opt = sys.argv[i]
      if opt == '-o':
         OUTPUT_DIR = sys.argv[i+1]
      elif opt == '-a':
         ENABLE_APPEND_MODE = True
      elif opt == '-n':
         DISABLE_CONFIG = True
      elif opt == '-t':
         # temporary disable TCPDUMP for gobuild debugging
         # ENABLE_TCPDUMP = True
         ENABLE_TCPDUMP = False
      elif opt == '-H':
         OB_HOST = sys.argv[i+1]
      elif opt == '-p':
         OB_PORT = sys.argv[i+1]
      elif opt == '-auth':
         OB_AUTH = sys.argv[i+1]
      elif opt == '--':
         commands = [convert_arg(x) for x in sys.argv[i+1:]]
         COMMAND = ' '.join(commands)
         break
      elif opt == '-h' or opt == '-?':
         usage()
      elif opt == '-v' or opt == '--version':
         version()
   # NB: do not check localhost, since we can make localhost to point to an external IP
   #     by modifying /etc/hosts
   if OB_HOST != "127.0.0.1":
      IS_LOCALHOST = False
      if ENABLE_TCPDUMP:
         print("Warning: running tnt on {0}; disable tcpdump support ...".format(OB_HOST))
      ENABLE_TCPDUMP = False
      DISABLE_CONFIG = True
      # TODO: OB_AUTH should be set

def kill_process_tree(process):
    if not process.poll():
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

def check_sudo_without_password(sudo_cmd):
   if not sudo_cmd: return None
   test_cmd = "{0} ls /".format(sudo_cmd)
   with subprocess.Popen(
      test_cmd, stdout=subprocess.PIPE, preexec_fn=os.setsid
   ) as process:
      try:
         process.communicate(timeout=10)
         return sudo_cmd
      except:
         # subprocess.TimeoutExpired and others
         # if timeout, assume it hungs there waiting for password
         kill_process_tree(process)
         return None

def main():
   parse_args()
   if not COMMAND:
      print("no command.")
      exit(1)

   global ENABLE_TCPDUMP, ENABLE_APPEND_MODE
   os.makedirs(LOG_DIR, 0o755, exist_ok=True)
   os.makedirs(OB_DIR, 0o755, exist_ok=True)
   print("Start tnt server ...")
   access_log = open(os.path.join(LOG_DIR, "access.log"), "w+")
   mitmdump_error_log = open(os.path.join(LOG_DIR, "mitmdump_error.log"), "w+")
   mitmdump_exe = "mitmdump"
   # in linux/macos: bin/python3 bin/mitmump
   # in windows: bin/python3.exe bin/Scripts/mitmdump.exe
   mitmdump_env = dict(os.environ)
   if IS_WINDOWS:
      mitmdump_exe += ".exe"
      mitmdump_exe = os.path.join("Scripts", mitmdump_exe)
      mitmdump_env['USERPROFILE'] = OB_DIR
   else:
      mitmdump_env['HOME'] = OB_DIR
   mitmdump_exe = os.path.join(ROOT_DIR, mitmdump_exe)
   if os.path.isfile(mitmdump_exe):
      mitmdump_cmd = [ PYTHON3, mitmdump_exe, "-p", OB_PORT ]
   else:
      # run mitmdump in venv instead of release
      mitmdump_cmd = [ "mitmdump", "-p", OB_PORT ]
   if not IS_LOCALHOST:
      mitmdump_cmd += ["--listen-host", OB_HOST]
   mitmdump = subprocess.Popen(
      ' '.join(mitmdump_cmd),
      shell=True,
      env=mitmdump_env,
      stdout=access_log,
      stderr=mitmdump_error_log
   )
   if ENABLE_TCPDUMP:
      print("Start httpry ...")
      if IS_WINDOWS:
         nmcap_cmd = subprocess.check_output(
            "where nmcap", shell=True
         ).decode('utf-8').strip('\n')
         httpry = subprocess.Popen(
            [
               nmcap_cmd,
               "/network",
               "*",
               "/capture",
               "/file",
               os.path.join(LOG_DIR, "httpry_access.cap"),
            ],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
         )
      else: # linux and macosx
         try:
            sudo_cmd = (subprocess.check_output(
               "which sudo", shell=True
            )).decode("utf-8").strip("\n")
         except:
            if os.path.isfile('/bin/sudo'):
               sudo_cmd = '/bin/sudo'
            elif os.path.isfile('/usr/bin/sudo'):
               sudo_cmd = '/usr/bin/sudo'
            else:
               sudo_cmd = None
         sudo_cmd = check_sudo_without_password(sudo_cmd)
         if not sudo_cmd:
            print("Warning: cannot find sudo command, skip running `httpry`.")
            ENABLE_TCPDUMP = False
         else:
            subprocess.check_output("{0} rm -f {1}".format(
               sudo_cmd,
               os.path.join(LOG_DIR, "httpry_access.log")
            ), shell=True)
            httpry_exe = os.path.join(ROOT_DIR, "httpry")
            if not os.path.isfile(httpry_exe):
               # run in dev env
               httpry_exe = "httpry"
            httpry = subprocess.Popen(
               [
                  sudo_cmd, httpry_exe, "-d",
                  "-o", os.path.join(LOG_DIR, "httpry_access.log"),
                  "-P", os.path.join(LOG_DIR, "httpry.pid")
               ],
               stdout=subprocess.DEVNULL,
               stderr=subprocess.DEVNULL,
            )

   time.sleep(5)
   cacert_file = os.path.join(
      OB_DIR, ".mitmproxy", "mitmproxy-ca-cert.pem"
   )
   if DISABLE_CONFIG:
      os.environ["TNT_PROXY_HOST"] = OB_HOST
      os.environ["TNT_PROXY_PORT"] = OB_PORT
      os.environ["TNT_PROXY_CACERT"] = cacert_file
   else:
      print("Configure proxy and cacert ...")
      import pre_config
      pre_config.act(cacert_file, "{0}:{1}".format(OB_HOST, OB_PORT))

   print("Executing: {0}".format(COMMAND))
   cmd = subprocess.Popen(COMMAND, shell=True)
   cmd.wait()
   ret = cmd.returncode
   # TODO: cmd.wait(timeout)
   # if ret is None:
   #    raise(Exception("Timeout"))

   if not DISABLE_CONFIG:
      print("Revert proxy and cacert configuration ...")
      import revert_config
      revert_config.act()

   if ENABLE_TCPDUMP:
      print("Stop httpry ...")
      if IS_WINDOWS:
         # XXX: notice that kill() cannot kill all children processes
         # XXX: replace with kill_process_tree(httpry)
         httpry.kill()
         # TODO: convert .cap to .log
      else:
         # XXX: notice that httpry run as root and create the pid file
         httpry_pid = (subprocess.check_output(
            "cat {0}".format(
               os.path.join(LOG_DIR, "httpry.pid")
            ),
            shell=True
         )).decode("utf-8").strip("\n")
         subprocess.check_output(
            "{0} kill {1}".format(sudo_cmd, httpry_pid),
            shell=True
         )

   print("Stop tnt server ...")
   # XXX: replace with kill_process_tree(mitmdump)
   mitmdump.kill()
   access_log.close()
   mitmdump_error_log.close()

   report_json_path = os.path.join(OUTPUT_DIR, "report.json")
   if (not ENABLE_APPEND_MODE) and os.path.isfile(report_json_path):
      os.remove(report_json_path)
   p = subprocess.Popen(
      "{0} {1} {2} {3}".format(
         PYTHON3,
         os.path.join(ROOT_DIR, "mitmproxy-report.py"),
         os.path.join(LOG_DIR, "access.log"),
         OUTPUT_DIR
      ),
      shell=True
   )
   p.wait()

   if ENABLE_TCPDUMP:
      httpry_access_log_path = os.path.join(OUTPUT_DIR, "httpry.access.log")
      if (not ENABLE_APPEND_MODE) and os.path.isfile(httpry_access_log_path):
         os.remove(httpry_access_log_path)
      p = subprocess.Popen(
         "{0} {1} {2} {3}".format(
            PYTHON3,
            os.path.join(ROOT_DIR, "tcpdump-report.py"),
            os.path.join(LOG_DIR, "httpry_access.log"),
            OUTPUT_DIR
         ),
         shell=True
      )
      p.wait()

   print("Done.")
   print("The supply chain report is at {0}".format(os.path.join(OUTPUT_DIR, "report.json")))
   exit(ret)

if __name__ == "__main__":
   main()
