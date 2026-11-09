"""Every saved tree arc/terminal/capacity ledger, reusable exact XML index."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
from stream_native_route_audit_expat_v3 import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_native_trajectory_v1_2026-10-20'
def fast(path,nodes,edges,expected):
 groups={};connections=[];current=None;switch=None;name=None;seen=set();root=None
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:name=m[2];assert name not in groups;groups[name]=set();seen=set();current=None;switch=None;root=None
  m=NODE.match(line)
  if not m:
   assert not line.lstrip().startswith('Node:');continue
  n,kind,s=int(m[1]),m[2],int(m[3]);assert name is not None and nodes[n][0]==kind and nodes[n][1]>0;groups[name].add(n)
  if n in seen and kind!='SINK':pass
  elif kind=='SOURCE':assert not seen;root=n;seen.add(n)
  else:
   assert current is not None and nodes[current][0]!='SINK';assert (current,n,switch) in edges
   if kind=='SINK':connections.append((name,root,n))
   else:seen.add(n)
  current=n;switch=s
 assert Counter(connections)==expected
 ledger=Counter(n for group in groups.values() for n in group);overflow=sum(max(0,count-nodes[n][1]) for n,count in ledger.items());return ledger,overflow,connections

def main():
 vp=D/'verification.json';v=json.loads(vp.read_text());assert all(x['all_iteration_snapshots_complete'] and x['all_iteration_summary_fields_match_except_clocks'] and x['final_physical_sequences_identical'] for x in v['rows']);pp=E/'prince_native_trajectory_design_v1_2026-10-20/protocol.json';p=json.loads(pp.read_text());jobs={x['case']:x for x in p['jobs']};allrows=[];bindings={str(q):sha(q) for q in [vp,pp,Path(__file__)]}
 for row in v['rows']:
  case=row['case'];d=D/case;j=jobs[case];graph=Path(j['command'][j['command'].index('--read_rr_graph')+1]);ep=E/'prince_native_cohort_v1_2026-10-20'/case/'pre_route_endpoints.json';meta=json.loads(ep.read_text());assert sha(graph)==meta['graph_sha256'];nodes={};edges=set()
  for event,x in ET.iterparse(graph):
   if x.tag=='node':n=int(x.get('id'));assert n not in nodes;nodes[n]=(x.get('type'),int(x.get('capacity')))
   if x.tag=='edge':edges.add(tuple(int(x.get(k)) for k in ['src_node','sink_node','switch_id']))
   x.clear()
  expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in meta['connections']);shots=sorted(d.glob('iteration_*.route'));audits=[]
  for i,shot in enumerate(shots):
   assert row['files'][str(shot)]==sha(shot);ledger,overflow,connections=fast(shot,nodes,edges,expected)
   if i in [0,len(shots)-1]:
    independent=audit(graph,shot);assert ledger==Counter({int(n):v for n,v in independent['node_occupancy'].items()}) and overflow==independent['overflow_units']
   output=d/(shot.stem+'_occupancy.json');output.write_text(json.dumps(dict(node_occupancy=dict(ledger),overflow_units=overflow,graph_sha256=meta['graph_sha256'],connections=len(connections)))+'\n');audits.append(dict(iteration=i+1,snapshot=str(shot),snapshot_sha256=sha(shot),occupancy=str(output),occupancy_sha256=sha(output),overflow_units=overflow))
  paths=[graph,ep,d/'receipt.json'];bindings.update({str(q):sha(q) for q in paths});result=dict(case=case,rows=audits,all_tree_arcs_endpoints_and_NET_union_counts_verified=True);proof=d/'trajectory_audit_v1.json';proof.write_text(json.dumps(result,indent=2)+'\n');allrows.append(dict(case=case,proof=str(proof),sha256=sha(proof),snapshots=len(shots)));print('TRAJECTORY_AUDIT',case,len(shots),flush=True)
 assert all(sha(q)==h for q,h in bindings.items());(D/'trajectory_audit_verification_v1.json').write_text(json.dumps(dict(rows=allrows,snapshots=sum(x['snapshots'] for x in allrows),bindings=bindings,scope='Every printed snapshot branch arc and endpoint multiset and uniqueNET occupancy checked against exact current XML index; first/last ledgers crosschecked by original Expat full-graph audit. Congestion retained. No generic pin legality/canonical acceptance for partial states, no label quality or gain claim.'),indent=2)+'\n')
if __name__=='__main__':main()
