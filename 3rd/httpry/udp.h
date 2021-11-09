#ifndef _HAVE_UDP_H
#define _HAVE_UDP_H

struct udp_header {
   u_short source;
   u_short desc;
   u_short len;
   u_short checksum;
};

#endif
