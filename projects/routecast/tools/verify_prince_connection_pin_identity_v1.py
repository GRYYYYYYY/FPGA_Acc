"""Exact native NET/local-pin/sink join to independently audited physical pin export."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from load_prince_current_initial_timing_v1 import load
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_connection_query_trial_v1_2026-10-20'
def main():
 p=D/'verification.json';v=json.loads(p.read_text());bindings={str(p):sha(p),str(__file__):sha(__file__)};rows=[]
 for case in sorted(x['case'].rsplit('/',1)[0] for x in v['rows'] if x['case'].endswith('/capture')):
  td=R/'experiments/prince_frame_timings_v1_2026-10-20'/case;ep=R/'experiments/prince_native_cohort_v1_2026-10-20'/case/'pre_route_endpoints.json';timing=load(td,ep);pins={(x['native_net_id'],x['local_sink_pin']):x['target_rr'] for x in timing.values()};assert len(pins)==4802
  cp=D/case/'capture/queries.tsv.connections.tsv';count=multi=0
  for line in cp.open():
   iteration,ident,net,pin,sink,nodes=map(int,line.split());assert pins[net,pin]==sink;count+=1;multi+=nodes>1
  for q in [td/'verification.json',td/'initial_connection_criticalities.json',ep,cp]:bindings[str(q)]=sha(q)
  rows.append(dict(case=case,exact_NET_pin_sink_joins=count,entries_with_more_than_root_node=multi))
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());out=D/'connection_pin_identity_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL_CONNECTION_NET_PIN_SINK_IDENTITIES_EXACT',rows=rows,bindings=bindings,scope='Matches native local sink-pin index and sink RR node to separately XML/physical-pin audited initial timing export for same graph/netlist/placement. Does not independently reconstruct per-connection route-tree membership.'),indent=2)+'\n');print('EXACT_CONNECTION_PIN_IDENTITY_PASS',sum(x['exact_NET_pin_sink_joins'] for x in rows))
if __name__=='__main__':main()
