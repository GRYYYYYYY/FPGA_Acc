"""Verify serialized graph potentials/witnesses without rerunning shortest-path search."""
import csv,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_ex5p_capacity_delay_bound_20261015';INF=(1<<64)-1

def main():
 refs={}
 def bind(p):
  key=str(p)
  if key not in refs:refs[key]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
  return refs[key]
 f=P/'independent_audit.json';report=json.loads(f.read_text());bind(f)
 for p,h in report['source_sha256'].items():assert bind(p)==h,p
 protocol_path=R/'work/sb3_fixed_feedback_pair_20261015/protocol.json';protocol=json.loads(protocol_path.read_text());bind(protocol_path);case=next(x for x in protocol['cases'] if x['label']=='ex5p');prefix=case['input_prefix'];nodes=list(struct.iter_unpack('<IHH',Path(prefix+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(prefix+'.edges').read_bytes()));assert len(nodes)==336312
 baseline_path=R/'work/sb_ex5p_critical_arc_RR_binding_v5_20261015/independent_audit.json';baseline=json.loads(baseline_path.read_text());bind(baseline_path);baseline_delay=next(x['packed_edge_delay_sum_ps'] for x in baseline['outcomes'] if x['case']=='baseline');assert baseline_delay==567
 rows=[]
 for row in report['outcomes']:
  d=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+row['arm']+'_0');members={}
  for item in csv.DictReader((d/'route.route_trees.csv').open()):members.setdefault(int(item['net_id']),set()).update(int(item[k]) for k in ['parent','child'] if item[k]!=item['source'])
  assert len(members)==613
  resources=list(struct.iter_unpack('<HHHHII',(d/'route.resources').read_bytes()));owners=[0]*len(nodes)
  for net,ns in members.items():
   if net!=138:
    for node in ns:owners[node]+=1
  allowed=[owners[i]<r[1] for i,r in enumerate(resources)];assert allowed[43804]
  dist=[v[0] for v in struct.iter_unpack('<Q',Path(row['distance_certificate']).read_bytes())];assert len(dist)==len(nodes) and dist[43804]==0;checked=0
  for u,(begin,count,_) in enumerate(nodes):
   if dist[u]==INF:continue
   assert allowed[u]
   for v,_,w in edges[begin:begin+count]:
    if allowed[v]:assert dist[v]<=dist[u]+w;checked+=1
  path=row['witness_path'];assert (path[0],path[-1])==(43804,14256) and len(set(path))==len(path) and all(allowed[n] for n in path);cost=0
  for u,v in zip(path,path[1:]):
   begin,count,_=nodes[u];weights=[w for n,_,w in edges[begin:begin+count] if n==v];assert weights;cost+=min(weights)
  assert cost==dist[14256]==row['minimum_packed_delay_ps'] and checked==row['edge_inequalities_checked']
  assert cost>baseline_delay
  rows.append(dict(arm=row['arm'],certified_relaxed_optimum_ps=cost,baseline_connection_ps=baseline_delay,minimum_gap_ps=cost-baseline_delay,baseline_packed_delay_unattainable_with_other612nets_fixed=True))
 bind(Path(__file__).resolve());result=dict(status='serialized_capacity_delay_potentials_and_witnesses_independently_verified',outcomes=rows,source_sha256=refs,adopted=False,research_complete=False,scope='Independent certificate verifier uses all eligible edge inequalities and path attainment, no shortest-path implementation. Proves inability to attain baseline567ps for this connection in the relaxed fixed-other-nets packed graph. Does not prove full-net feasibility, primitive arc delay, globalCPD impossibility or performance; graph/capacity model only.')
 with (P/'certificate_audit.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
 print(json.dumps(rows))
if __name__=='__main__':main()
