# usage mitmproxy-report.py mitmproxy-access.log /path/to/output

import sys
import json
import os
import os.path

"""
# log sample
Proxy server listening at http://*:3128
127.0.0.1:46978: clientconnect
127.0.0.1:46978: Cannot connect to server, no server address given.
127.0.0.1:46978: clientdisconnect
127.0.0.1:46980: clientconnect
127.0.0.1:46980: GET https://internal.npm.com/api/npm/npm/n
              << 200 OK 23.37k
127.0.0.1:46980: clientdisconnect
127.0.0.1:46982: clientconnect
127.0.0.1:46982: GET https://internal.npm.com/api/npm/npm/n/-/n-7.1.0.tgz
              << 200 OK 21.01k
127.0.0.1:46982: clientdisconnect
127.0.0.1:46998: clientconnect
127.0.0.1:46996: clientconnect
"""

filename = sys.argv[1]
outdir = sys.argv[2]

urlmap = {}

try:
   # oops, python2.6 do not support with!
   f = open(filename, 'r')
   for line in f:
      if not f: continue
      line = line.strip('\n')
      if not f: continue
      parts = line.split(' ')
      # skip `ip:port: clientconnect`
      # skip `ip:port: clientdisconnect`
      if len(parts) < 3: continue
      # TODO: parse CONNECT host:port
      if parts[1] not in ['GET', 'PUT', 'POST', 'OPTIONS', 'PATCH']: continue
      # skip `              << CODE STATUS SIZE`
      if line.startswith(' '): continue
      # skip `Proxy server listening ...`
      url = ' '.join(parts[2:])
      urlmap[url] = (urlmap.get(url) or 0) + 1
   f.close()

   items = []
   itemmap = {}
   for k in urlmap.keys():
      formatedURL = k.replace('"', '%22')
      parts = formatedURL.split('/')
      host = parts[2]
      protocol = parts[0][:-1]
      path = '/' + '/'.join(parts[3:])
      protocolHost = protocol + '://' + host
      if protocolHost in itemmap:
         obj = itemmap[protocolHost]
      else:
         obj = {
            "host": host,
            "protocol": protocol,
            "path": []
         }
         items.append(obj)
         itemmap[protocolHost] = obj
      if path not in obj["path"]:
         obj["path"].append(path)

   report_json_path = os.path.join(outdir, 'report.json')
   obj = { "items": items }
   if os.path.isfile(report_json_path):
      with open(report_json_path, 'r') as f0:
         obj0 = json.loads(f0.read())
      ar0 = obj0.get("items", [])
      ar0map = {}
      for item in ar0:
         ar0map[item["protocol"] + "://" + item["host"]] = item
      for item in items:
         arkey = item["protocol"] + "://" + item["host"]
         if arkey in ar0map:
            item0 = ar0map[arkey]
            paths0 = item0["path"]
            for path in item.get("path", []):
               if path not in paths0:
                  paths0.append(path)
         else:
            ar0.append(item)
            ar0map[arkey] = item
      obj = obj0
   f = open(report_json_path, 'w+')
   f.write(json.dumps(obj, indent=3, sort_keys=True))
   f.close()
except Exception as e:
   print('Error!', e)
