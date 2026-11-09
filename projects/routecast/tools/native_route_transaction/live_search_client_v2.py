#!/usr/bin/python3
"""Native producer structured argv client to an isolated serial local worker."""
import os,sys,socket,json
keys=['ROUTECAST_SEARCH_ENDPOINT','ROUTECAST_SEARCH_REPORT','ROUTECAST_TX_CANDIDATE','ROUTECAST_TX_REQUEST'];config={k:os.environ[k] for k in keys};config['place']=os.path.abspath('design.place')
with socket.socket(socket.AF_UNIX) as client:
 client.settimeout(110);client.connect(os.environ['ROUTECAST_SEARCH_SOCKET']);client.sendall((json.dumps(dict(stem=sys.argv[1],config=config))+'\n').encode());result=json.loads(client.makefile('r').readline())
if not result['ok']:raise RuntimeError(result['error'])
