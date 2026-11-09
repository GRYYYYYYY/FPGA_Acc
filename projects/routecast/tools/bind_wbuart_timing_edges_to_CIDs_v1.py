"""Source-driver + native-local-pin + CID binding of current interconnect edge candidates."""
import json,csv,hashlib,struct
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_nominal_contexts_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def exact(s):return F(struct.unpack('f',struct.pack('f',float(s)))[0])
def main():
 proof=read(D/'verification.json');assert all(sha(k)==h for k,h in proof['bindings'].items());bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)};summaries=[]
 for case_row in proof['rows']:
  case=case_row['case'];folder=D/case;atoms=list(csv.DictReader((folder/'timing_atoms.tsv').open(),delimiter='\t'));roots=defaultdict(list);sinks=defaultdict(list)
  for a in atoms:
   if a['native_net'] and a['local_pin']=='0' and a['external_node']:roots[int(a['external_node'])].append(a)
   if a['raw_criticality']:sinks[int(a['external_node'])].append(a)
  payload=E/'wbuart_frame_timings_v1_2026-10-20'/case/'initial_connection_criticalities.json';queries=read(payload);by_key={(q['native_net_id'],q['local_sink_pin']):q for q in queries};assert len(by_key)==2493
  initial={(int(q['net']),int(q['pin'])):q for q in csv.DictReader((folder/'initial_connections.tsv').open(),delimiter='\t')};mapped=[];covered=set();edge_ids=set()
  for e in csv.DictReader((folder/'timing_edges.tsv').open(),delimiter='\t'):
   if e['type']!='3' or e['disabled']!='0' or int(e['sink']) not in sinks:continue
   data=sinks[int(e['sink'])];keys={(int(a['native_net']),int(a['local_pin'])) for a in data};assert len(keys)==1;key=keys.pop();q=by_key[key];drivers=[a for a in roots[int(e['source'])] if int(a['native_net'])==key[0]];assert len(drivers)==1
   rr=exact(initial[key]['delay_s']);whole=exact(e['value_max_or_setup_s']);offset=whole-rr;assert offset>=0 and offset+rr==whole;edge=int(e['edge']);assert edge not in edge_ids;edge_ids.add(edge);covered.add(q['connection_id']);mapped.append(dict(edge=edge,source_node=int(e['source']),sink_node=int(e['sink']),source_atom_pin=int(drivers[0]['atom_pin']),source_atom=drivers[0]['atom'],destination_atom_pins=[int(a['atom_pin']) for a in data],connection_id=q['connection_id'],full_connection_id=q['full_connection_id'],native_net_id=key[0],local_sink_pin=key[1],net_name=q['net_name'],source_rr=q['source_rr'],target_rr=q['target_rr'],initial_native_rr_delay_s=str(rr),initial_native_edge_delay_s=str(whole),nominal_offset_s=str(offset)))
  assert covered=={q['connection_id'] for q in queries};path=folder/'external_edge_CID_bindings_v1.json';path.write_text(json.dumps(mapped)+'\n');bindings[str(path)]=sha(path);bindings[str(payload)]=sha(payload);summaries.append(dict(case=case,mapped_external_timing_edges=len(mapped),covered_CIDs=len(covered),source_driver_NET_and_local_sink_pin_verified=True,ambiguous_edge_to_CID=0,all_nominal_offsets_nonnegative=True));print(json.dumps(summaries[-1]),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'edge_CID_verification_v1.json').write_text(json.dumps(dict(status='ALL12_WBUART_TIMING_EDGES_SOURCE_SINK_AND2493_CIDS_BOUND',rows=summaries,bindings=bindings,scope='Current nominal packed mapping; every mapped external edge source native NET matches sink and endpoint CID identity. Rational offset is baseline edge-minus-net-delay decomposition including float rounding, not independent intracluster delay or invariance after speculative IPIN changes. Clock required-time import, independent STA recurrence and dynamic criticality still unproven.'),indent=2)+'\n')
if __name__=='__main__':main()
