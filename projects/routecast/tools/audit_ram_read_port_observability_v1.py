"""Exact direct-use audit on all16 preserved real-source DP interfaces."""
import json,hashlib
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'preserved_source_ram_mapping_v1_2026-10-21';D=E/'ram_read_port_observability_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);paths=[P/n/'preserved_boundary.json' for n in ['mcml','mkDelayWorker32B']];(D/'protocol.json').write_text(json.dumps({'scope':'All16 DP instances in original preserved source-boundary snapshots. Direct cell-input fanout and top-output aliases audited at each RAM output bit. No liveness pruning or reset/source modifications. Zero consumers establishes disconnected output in this frozen graph, not that collision cannot occur.','bindings':{str(p):sha(p) for p in [Path(__file__),*paths]}},indent=2)+'\n');rows=[]
 for path in paths:
  n=path.parent.name;m=json.loads(path.read_text())['modules'][n];users=defaultdict(set)
  for cn,c in m['cells'].items():
   for port,bits in c['connections'].items():
    if c['port_directions'][port]=='input':
     for bit in bits:
      if isinstance(bit,int):users[bit].add((cn,port))
  external={b for p in m['ports'].values() if p['direction']=='output' for b in p['bits']}
  for cn,c in m['cells'].items():
   if not c['type'].endswith('dual_port_ram'):continue
   z=c['connections'];assert z['we2']==['0'];out={}
   for port in ['out1','out2']:
    bits=z[port];used=[b for b in bits if users[b] or b in external];out[port]={'width':len(bits),'used_bits':len(used),'direct_input_consumer_count':len(set(pair for b in bits for pair in users[b])),'top_output_bits':sum(b in external for b in bits),'unused_output_proven':not used}
   rows.append({'source':n,'instance':cn,'write2_constant_zero':True,'read_ports':out,'cross_port_read_is_unused':out['out2']['unused_output_proven']})
 assert len(rows)==16 and sum(r['cross_port_read_is_unused'] for r in rows)==7
 (D/'results.json').write_text(json.dumps({'status':'7_UNUSED_SECOND_READ_PORTS_9_USED_SECOND_READ_PORTS','rows':rows,'unused_second_read_count':7,'used_second_read_count':9,'scope':'No equivalence/source reset reachability claim. For the7disconnected outputs, port2 read-result race cannot directly enter top graph; port2 write is also literal0.9used-port2 cases retain collision/ordering obligations.'},indent=2)+'\n');print('RAM_PORT_USE_16_INTERFACES_VERIFIED')
if __name__=='__main__':main()
