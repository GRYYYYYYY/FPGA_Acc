"""Conservative launcher profile identity; input bytes bound separately except architecture."""
import hashlib,json
from pathlib import Path
from pre_route_endpoints import sha
VERSION='PRINCE_ROUTER_LAUNCH_PROFILE_V1'
def profile(command,circuit_path):
 argv=list(command[1:]);assert len(argv)>=2;arch=Path(argv[0]);argv[0]='$ARCH';argv[1]='$CIRCUIT'
 for flag,token in [('--read_rr_graph','$GRAPH'),('--net_file','$NET'),('--place_file','$PLACE'),('--route_file','$OUTPUT')]:
  assert argv.count(flag)==1;argv[argv.index(flag)+1]=token
 payload=dict(schema=VERSION,architecture_sha256=sha(arch),circuit_sha256=sha(circuit_path),argv=argv,scope='Fixed native routing command, all supplied options retained; native resolved option record is a second independent identity component. Input graph/netlist/placement/binary hashes bind separately.')
 raw=json.dumps(payload,sort_keys=True,separators=(',',':')).encode();return payload,hashlib.sha256(raw).hexdigest()
