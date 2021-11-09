# usage: tcpdump-report.py httpry-access.log /path/to/outdir

import sys
import re
import os
import os.path

IP_REGEX = re.compile(r'^[0-9]+[.][0-9]+[.][0-9]+[.][0-9]+$')
PROXYPORT="3128"

filename = sys.argv[1]
outdir = sys.argv[2]

iphostmap = {}
ipallhostmap = {}
visit = {} # {a:p : { b:p : { uri } }}
self = None

def mergeSelf(visit, self):
   # visit = { a:p : { b:p : { uri : n} } }
   for a in visit.keys():
      m = visit[a]
      for b in list(m.keys()):
         p = b.split(':')
         if self != p[0]:
         #   if p[0] in iphostmap:
         #      b0 = iphostmap[p[0]] + ':' + p[1]
         #      m[b0] = m[b]
         #      del m[b]
            continue
         # self:port -> self
         d = m[b]
         del m[b]
         if p[1] == PROXYPORT:
            b0 = 'selfProxy'
         else:
            b0 = 'self'
         m[b0] = m.get(b0) or {}
         for x in d.keys():
            m[b0][x] = (m[b0].get(x) or 0) + d[x]

   for a in list(visit.keys()):
      m = visit[a]
      p = a.split(':')
      if self != p[0]:
      #   if p[0] in iphostmap:
      #      a0 = iphostmap[p[0]] + ':' + p[1]
      #      visit[a0] = m
      #      del visit[a]
         continue
      del visit[a]
      if p[1] == PROXYPORT:
         a0 = 'selfProxy'
      else:
         a0 = 'self'
      visit[a0] = visit.get(a0) or {}
      for b in m.keys():
         if b in visit[a0]:
            for x in m[b].keys():
               visit[a0][b][x] = (visit[a0][b].get(x) or 0) + m[b][x]
         else:
            visit[a0][b] = m[b]

try:
   f = open(filename, 'r', errors='replace')
   last = ''
   first3 = 0
   for line in f:
      if not f: continue
      line = line.strip('\n')
      if not f: continue
      if last:
         last += line
         line = last
      # read every line and process
      parts = line.split('\t')
      n = len(parts)

      # XXX: some DNS record contains '\n'
      #      need concat multiple lines to one line
      if n < 11:
         # skip first 3 lines which are httpry startup info
         first3 += 1
         if first3 < 3:
            last = ''
            continue
         last = line
         continue
      last = ''

      tm = parts[0]
      src = parts[1]
      sport = parts[2]
      dst = parts[3]
      dport = parts[4]

      # XXX: recognize local IP, not 100% accurate
      #      sometimes, a packet is not related to self
      #      maybe some data center packet goes through self NIC
      #      not sure it is related to vsock traffic or not
      if self is None:
         self = [ src, dst ]
      else:
         self0 = []
         if src in self: self0.append(src)
         if dst in self: self0.append(dst)
         if len(self0) > 0:
            self = self0

      rtype = parts[5]
      hostname = parts[6]
      uri = parts[7]
      rcode = parts[8]
      rstatus = parts[9]
      # parts[10]: error reason

      # do not care about source and destination
      # just track 2 terminals communicate with each other
      if src > dst:
         t = src
         src = dst
         dst = t
         t = sport
         sport = dport
         dport = t

      # process DNS record
      if rtype == 'DNS':
         items = list(filter(
            lambda x: IP_REGEX.match(x) is not None,
            rstatus.split(';')
         ))
         #print(hostname, items)
         if len(items) == 0: continue
         for ip in items:
            iphostmap[ip] = hostname
            ipallhostmap[ip] = ipallhostmap.get(ip) or set()
            ipallhostmap[ip].add(hostname)

      #if hostname != '-' and uri != '-' and rtype != '-': record hostname
      # record communication as a <--> b, uri and count
      a = '{0}:{1}'.format(src, sport)
      b = '{0}:{1}'.format(dst, dport)
      if a not in visit:
         visit[a] = {}
      if b not in visit[a]:
         visit[a][b] = {}
      visit[a][b][uri] = (visit[a][b].get(uri) or 0) + 1
   f.close()

   #print('map:', self)
   if self and len(self) == 1:
      self = self[0]
   else:
      self = None
   # transform self IP as hostname 'self' / 'selfProxy'
   # transform IP to one of known hostnames
   if self:
      mergeSelf(visit, self)

   httpry_access_log_path = os.path.join(outdir, 'httpry.access.log')
   if os.path.isfile(httpry_access_log_path):
      fout = open(httpry_access_log_path, "a")
      fout.write('\n')
   else:
      fout = open(httpry_access_log_path, 'w+')
   fout.write('DNS Information\n')
   for ip in ipallhostmap.keys():
      fout.write('IP: {0}\n'.format(ip))
      for hostname in list(ipallhostmap[ip]):
         fout.write('  - {0}\n'.format(hostname))
   fout.write('\n')

   fout.write('Visit Information\n')
   for a in visit.keys():
      for b in visit[a].keys():
         count = sum(visit[a][b].values())
         if a == 'self' or b == 'self':
            fout.write('{0}: Count={1}\n'.format(a if a != 'self' else b, count))
         else:
            #fout.write('{0} <--> {1}: Count={2}\n'.format(a, b, count))
            continue
         #for x in visit[a][b].keys():
         #   fout.write('  - {0}: {1}\n'.format(x, visit[a][b][x]))
   fout.close()
except Exception as e:
   print('Error!', e)
