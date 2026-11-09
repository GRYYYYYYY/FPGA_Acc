#!/usr/bin/python3
"""Local serial fixed-source pilot; immutable RR reuse, no occupancy reuse."""
import socket,json,sys,traceback
from pathlib import Path
from live_search_worker_v2 import produce
path=Path(sys.argv[1]);assert not path.exists();server=socket.socket(socket.AF_UNIX);server.bind(str(path));path.chmod(0o600);server.listen(1);ctx=inventory=None
try:
 for index in range(int(sys.argv[2])):
  with server.accept()[0] as client:
   data=client.makefile('r').readline();request=json.loads(data)
   try:
    ctx,inventory=produce(request['stem'],request['config'],ctx,inventory);result={'ok':True,'index':index}
   except Exception:
    result={'ok':False,'error':traceback.format_exc()};ctx=inventory=None
   client.sendall((json.dumps(result)+'\n').encode())
finally:
 server.close();path.unlink()
