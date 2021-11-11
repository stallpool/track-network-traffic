import os
import os.path
import sys
import subprocess
import json
import re
import tempfile

SELF_DIR = os.path.abspath(os.path.dirname(__file__))
DOCKER = os.getenv("TNT_DOCKER")
INJECTED_CMD = re.compile(
   r'/tmp/lin/bin/python3 /tmp/lin/bin/pre_config.py [0-9.]+ [0-9]+ /tmp/ca.pem'
)

def main():
   image_namid = sys.argv[1]
   if not DOCKER:
      raise Exception('TNT_DOCKER not set; should refer to real docker command like /usr/bin/docker')
   base_dir = os.path.join(SELF_DIR, 'runtime', 'tnt')
   cmdp = subprocess.Popen(['mkdir', '-p', base_dir])
   cmdp.wait()
   fd, base_dir = tempfile.mkstemp(prefix=os.path.join(base_dir, 'tnt-docker-cleanup-'))
   print('processing in {0}'.format(base_dir))
   os.close(fd)
   os.remove(base_dir)
   contents_dir = os.path.join(base_dir, 'contents')
   cmdp = subprocess.Popen(['mkdir', '-p', contents_dir])
   cmdp.wait()
   print('extracting image ...')
   image_tar = os.path.join(base_dir, 'contents.tar')
   cmdp = subprocess.Popen([DOCKER, 'save', '-o', image_tar, image_namid])
   cmdp.wait()
   cmdp = subprocess.Popen(['tar', 'xf', image_tar, '-C', contents_dir])
   cmdp.wait()

   manifest_json = os.path.join(contents_dir, 'manifest.json')
   with open(manifest_json, 'r') as f:
      manifest = json.loads(f.read())
   layers = manifest[0]["Layers"]
   config_json = os.path.join(contents_dir, manifest[0]["Config"])
   with open(config_json, 'r') as f:
      config = json.loads(f.read())
   hitems = config["history"]
   lasti = -1
   for i, item in enumerate(hitems):
      created_by = item["created_by"]
      # TODO: cmd conflict, what will do the same thing with the same command:
      #       /tmp/lin/bin/python3 /tmp/lin/bin/pre_config.py <ip> <port> /tmp/ca.pem
      if INJECTED_CMD.search(created_by):
         lasti = i
         break

   if lasti == -1:
      print('No observer injection detected for "{0}"'.format(image_namid))
      cmdp = subprocess.Popen(['rm', '-r', base_dir])
      cmdp.wait()
      return False

   print('tnt injection detected!')
   lasti = len(hitems) - lasti
   itemi = len(layers) - lasti
   # remove itemi, itemi-1, itemi-2
   # itemi-2: ADD .tnt/ca.pem /tmp/ca.pem
   # itemi-1: ADD .tnt/lin /tmp/lin
   #   itemi: RUN /tmp/lin/bin/python3 /tmp/lin/bin/pre_config.py <ip> <port> /tmp/ca.pem
   cleanup_layers = list(map(
      lambda x: os.path.join(contents_dir, os.path.dirname(x)),
      layers[itemi-2:itemi+1]
   ))
   for one in cleanup_layers:
      print('removing Layer {0}'.format(os.path.basename(one)))
      cmdp = subprocess.Popen(['rm', '-r', one])
      cmdp.wait()

   # connect itemi-3 and itemi+1
   itemi_ = len(hitems) - lasti
   hitems = hitems[0:itemi_-2] + hitems[itemi_+1:]
   config["history"] = hitems
   hashitems = config["rootfs"]["diff_ids"]
   hashitems = hashitems[0:itemi-2] + hashitems[itemi+1:]
   config["rootfs"]["diff_ids"] = hashitems
   layers = layers[0:itemi-2] + layers[itemi+1:]
   manifest[0]["Layers"] = layers
   n = len(layers)
   if n == 0:
      print('It is empty image before injection')
      cmdp = subprocess.Popen(['rm', '-r', base_dir])
      cmdp.wait()
      return False

   with open(manifest_json, 'w+') as f:
      f.write(json.dumps(manifest))
   with open(config_json, 'w+') as f:
      f.write(json.dumps(config))

   Li_m3 = itemi - 3
   Li_a1 = itemi - 2
   if Li_m3 < 0:
      # shoud not: Li_a1 >= n
      # open json and remove parent for Li_a1
      Li_a1_hash = os.path.dirname(layers[Li_a1])
      print("cleaning up for Layer {0}".format(Li_a1_hash))
      Li_a1_dir = os.path.join(contents_dir, Li_a1_hash)
      Li_a1_json = os.path.join(Li_a1_dir, 'json')
      with open(Li_a1_json, 'r') as f:
         Li_a1_obj = json.loads(f.read())
      del Li_a1_obj["parent"]
      with open(Li_a1_json, 'w+') as f:
         f.write(json.dumps(Li_a1_obj))
   elif Li_a1 >= n:
      # should not: Li_m3 < 0
      # no change needed
      pass
   else:
      # open Li_a1 json and update parent to Li_m3
      Li_m3_hash = os.path.dirname(layers[Li_m3])
      Li_a1_hash = os.path.dirname(layers[Li_a1])
      print("cleaning up and connecting Layer {0} and Layer {1}".format(Li_m3_hash, Li_a1_hash))
      Li_a1_dir = os.path.join(contents_dir, Li_a1_hash)
      Li_a1_json = os.path.join(Li_a1_dir, 'json')
      with open(Li_a1_json, 'r') as f:
         Li_a1_obj = json.loads(f.read())
      Li_a1_obj["parent"] = Li_m3_hash
      with open(Li_a1_json, 'w+') as f:
         f.write(json.dumps(Li_a1_obj))

   print('building new image ...')
   image_cleanup_tar = os.path.join(base_dir, 'cleanup.tar')
   cmdp = subprocess.Popen(
      'cd {0} && tar cf {1} *'.format(contents_dir, image_cleanup_tar),
      shell=True
   )
   cmdp.wait()

   print('removing original image ...')
   # TODO: backup first: docker tag -t <image>.bak image_namid
   cmdp = subprocess.Popen([DOCKER, 'rmi', image_namid])
   cmdp.wait()
   print('applying new image ...')
   # TODO: `docker load` will combine layers together into one layer
   #       use `docker image history` to compare after and before cleanup
   cmdp = subprocess.Popen([DOCKER, 'load', '-i', image_cleanup_tar])
   cmdp.wait()
   cmdp = subprocess.Popen(['rm', '-r', base_dir])
   cmdp.wait()
   print('Done.')
   return True

if __name__ == '__main__':
   main()
