import sys
import os
import os.path
import subprocess
import re
import tempfile

# docker build ...
# docker_build ...

"""
           TNT_DOCKER  real docker command path, e.g. /usr/bin/docker
   TNT_DOCKER_GATEWAY  docker bridge IP, e.g. 172.18.0.1
TNT_DOCKER_PROXY_PORT  tnt proxy listen port, e.g. 20210
       TNT_OUTPUT_DIR  output dir for supply chain report, e.g. /tmp/out
"""

SELF_DIR = os.path.abspath(os.path.dirname(__file__))
IS_WINDOWS = sys.platform == 'win32'
DOCKER = os.getenv('TNT_DOCKER')
DOCKER_GATEWAY = os.getenv('TNT_DOCKER_GATEWAY')
DOCKER_PROXY_PORT = os.getenv('TNT_DOCKER_PROXY_PORT', '20210')
OUTPUT_DIR = os.getenv('TNT_OUTPUT_DIR', '.')
DOCKER_FILE_INJECTED = []

def parse_args():
   argv = sys.argv[1:]
   n = len(argv)
   if n <= 0:
      cmdp = subprocess.Popen('{0} build'.format(DOCKER), shell=True)
      cmdp.wait()
      os.exit(1)
      return
   injected_argv = []
   obj = {}
   obj["context"] = argv.pop()
   skip_next = False
   for i in range(0, n-1):
      one = sys.argv[i]
      if one == '-f':
         obj["dockerfile"] = sys.argv[i+1]
         skip_next = True
      elif skip_next:
         skip_next = False
      else:
         injected_argv.append(one)
   return argv, obj


def get_docker_bridge_gateway_ip():
   if DOCKER_GATEWAY:
      return DOCKER_GATEWAY
   cmd = [DOCKER, 'network', 'inspect', 'bridge']
   stdout = subprocess.check_output(cmd).decode('utf8')
   m = None
   for line in stdout.split('\n'):
      m = re.match(r'^\s*"Gateway": "(.*)".*$', line)
      if m is not None: break
   if m is None:
      raise Exception('cannot find docker bridge gateway IP address.')
   return m[1]


def prepare_pre_config(docker_context):
   base_dir = os.path.join(SELF_DIR, 'runtime', 'tnt')
   target_tar = os.path.join(SELF_DIR, '..', 'publish', 'tnt-lin.tar.gz')
   # TODO: use pure python code to support multiple platforms
   if not os.path.isfile(target_tar):
      target_dir = os.path.join(base_dir, 'lin')
      cmdp = subprocess.Popen(['mkdir', '-p', target_dir])
      cmdp.wait()
      # TODO: use shutil.unpack_archive, (3rd)tarfile, etc
      cmdp = subprocess.Popen(['tar', 'zxf', target_tar, '-C', target_dir])
      cmdp.wait()
   # TODO: deal with context path is a package instead of a folder
   context_dir = os.path.abspath(docker_context)
   buildtime_dir = os.path.join(context_dir, '.tnt')
   # TODO: use os.mkdir
   cmdp = subprocess.Popen(['mkdir', '-p', buildtime_dir])
   cmdp.wait()
   cmdp = subprocess.Popen([
      'bash',
      os.path.join(SELF_DIR, 'tnt.bash'), '-n',
      '--', 'echo', 'generating certificate ...'
   ])
   cmdp.wait()
   cmdp = subprocess.Popen([
      'cp',
      os.path.join(base_dir, '.mitmproxy/mitmproxy-ca.pem'),
      os.path.join(buildtime_dir, 'ca.pem')
   ])
   cmdp.wait()
   if not os.path.isdir(os.path.join(buildtime_dir, 'lin')):
      cmdp = subprocess.Popen([
         'cp', '-r',
         os.path.join(base_dir, 'lin'),
         os.path.join(buildtime_dir, 'lin')
      ])
      cmdp.wait()


def inject_ca_cert(dockerfile, proxy_host, proxy_port):
   dockerfile = os.path.abspath(dockerfile)
   print('injecting CA cert into {0} for docker build ...'.format(dockerfile))
   # CA cert is available at ${SELF_DIR}/runtime/tnt/.mitmproxy/mitmproxy-ca.pem
   base_dir = os.path.join(SELF_DIR, 'runtime/tnt')
   with open(dockerfile, 'r') as f:
      dockerfile_text = f.read()
   newlines = []
   lines = dockerfile_text.split('\n')
   regex_from = r'^\s*FROM .*$'
   for line in lines:
      if re.match(regex_from, line) is None:
         newlines.append(line)
         continue
      # inject cert for all FROM
      newlines.append(line)
      newlines.append('ADD .tnt/ca.pem /tmp/ca.pem')
      newlines.append('ADD .tnt/lin /tmp/lin')
      newlines.append('RUN {0} {1} {2} {3} {4}'.format(
         '/tmp/lin/bin/python3',
         '/tmp/lin/bin/pre_config.py',
         proxy_host, proxy_port,
         '/tmp/ca.pem'
      ))
   # TODO: add RUN python3 revert_config.py for cleanup
   # currently after this build wrapper, the final image cannot be used for a release
   # TODO: we add 2ADDs+1RUN in Dockerfile, should remove related layers
   #       to make sure one build for both supply chain report generation and release
   fd, tf_path = tempfile.mkstemp(prefix=os.path.join(base_dir, 'tnt-docker-'))
   os.close(fd)
   DOCKER_FILE_INJECTED.append(tf_path)
   with open(tf_path, 'w+') as tf:
      tf.write('\n'.join(newlines))
   return tf_path


def main():
   if not DOCKER:
      raise Exception('TNT_DOCKER not set; should refer to real docker command like /usr/bin/docker')
   docker_build_gateway = get_docker_bridge_gateway_ip()
   docker_proxy = '{0}:{1}'.format(docker_build_gateway, DOCKER_PROXY_PORT)

   argv, extra = parse_args()
   prepare_pre_config(extra["context"])
   if "dockerfile" not in extra:
      extra["dockerfile"] = "Dockerfile"
   docker_file = inject_ca_cert(
      extra["dockerfile"],
      docker_build_gateway,
      DOCKER_PROXY_PORT,
   )
   argv += [
      '-f', docker_file,
      '--build-arg', 'http_proxy=http://{0}'.format(docker_proxy),
      '--build-arg', 'https_proxy=http://{0}'.format(docker_proxy),
      '--build-arg', 'HTTP_PROXY=http://{0}'.format(docker_proxy),
      '--build-arg', 'HTTPS_PROXY=http://{0}'.format(docker_proxy),
      extra["context"]
   ]

   if IS_WINDOWS:
      tnt_cmd = [os.path.join(SELF_DIR, 'tnt.cmd')]
   else:
      tnt_cmd = ['bash', os.path.join(SELF_DIR, 'tnt.bash')]
   # TODO: how to guarantee docker gateway is available for docker build
   #       e.g. in some OS, by default, it is blocked by firewall. need to run
   #            `iptables -A INPUT -p tcp --dport ${DOCKER_PROXY_PORT} -j ACCEPT` before run docker build
   cmd = tnt_cmd + [
      '-a', '-o', OUTPUT_DIR,
      '-H', docker_build_gateway, '-p', DOCKER_PROXY_PORT,
      '--', DOCKER, 'build'
   ] + argv
   print('running: {0}'.format(cmd))
   cmdp = subprocess.Popen(cmd)
   cmdp.wait()
   for tf_path in DOCKER_FILE_INJECTED:
      os.remove(tf_path)
   # TODO: cleanup build time dir (${context}/.tnt)

if __name__ == "__main__":
   main()
