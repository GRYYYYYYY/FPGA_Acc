"""All-ID temporal error attribution; descriptive, never a new acceptance gate."""
import json,hashlib,sys
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from zero_rc_budget_certificate_graph_v1 import load_graph
R=Path(__file__).resolve().parents[1];T=R/'experiments/prospective_external_family_temporal_prior_utilization_v1_2026-10-19';D=R/'experiments/prospective_external_family_temporal_prior_errors_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def pair(x):return [x.numerator,x.denominator]
def main():
 audit=read(T/'independent_verification_v1.json');assert all(sha(p)==h for p,h in audit['bindings'].items());protocol=read(T/'protocol.json');D.mkdir(exist_ok=False);bindings={str(T/'independent_verification_v1.json'):sha(T/'independent_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};spec=read(protocol['cases'][0]['original_comparison_spec']);ep=read(spec['endpoint']);g=load_graph(ep['inputs']['graph']['path']);dest=g['vs'];rows=[]
 (D/'protocol.json').write_text(json.dumps(dict(cases=protocol['cases'],policy='All45584 IDs per case. Endpoint edit masks clean=0/source_only=1/sink_only=2/mixed=4; resource affected mask is OR over NETs whose support changes. Disjoint masks avoid double attribution; truth used only after grouping. Squared error is diagnostic, original four gates unchanged. No coefficient fitting or NET/case selection.'),indent=2)+'\n')
 for c in protocol['cases']:
  s=read(c['original_comparison_spec']);domain=Path(s['domain_proof']).parent;resources=[json.loads(x) for x in (domain/'resources.jsonl').read_text().splitlines()];ids={r['id'] for r in resources};frames=[read(c['source_frame']),read(c['current_frame'])];groups=[]
  for frame in frames:
   nets=defaultdict(dict)
   for q in frame['records']:nets[q['net_id']][q['connection_id']]=q
   groups.append(nets)
  mask=Counter();netrows=[];unions=[set(),set()]
  for net,old in groups[0].items():
   new=groups[1][net];source_changed={q['source'] for q in old.values()}!={q['source'] for q in new.values()};sink_count=sum(q['sink']!=new[k]['sink'] for k,q in old.items());kind=4 if source_changed and sink_count else 1 if source_changed else 2 if sink_count else 0;supports=[]
   for group in [old,new]:
    nodes=set()
    for q in group.values():nodes.add(q['source']);nodes.update(dest[e] for e in q['answer']['physical_edge_ids'])
    supports.append(nodes&ids)
   for i in (0,1):unions[i]|=supports[i]
   for n in supports[0]^supports[1]:mask[n]|=kind
   netrows.append(dict(net_id=net,edit_mask=kind,fanout=len(old),source_changed=source_changed,changed_sinks=sink_count,old_only=len(supports[0]-supports[1]),new_only=len(supports[1]-supports[0]),shared=len(supports[0]&supports[1])))
  comp=read(T/c['case']/'comparison.json');scores={n:F(*v) for n,v in comp['score_vectors']['resource']};physical=read(s['label_physical_audit']);truth={int(n) for n,v in physical['node_occupancy'].items() if v};counts=Counter();errors=defaultdict(F);out=D/c['case'];out.mkdir(parents=True)
  with (out/'resources.jsonl').open('x') as f:
   for n in sorted(ids):
    old=int(n in unions[0]);new=int(n in unions[1]);y=int(n in truth);score=scores[n];key=(old,new,y,mask[n]);counts[key]+=1;delta=(score-y)**2-(old-y)**2;errors[key]+=delta
    f.write(json.dumps(dict(id=n,old=old,current=new,truth=y,edit_mask=mask[n],score=pair(score),squared_error_delta=pair(delta)))+'\n')
  (out/'NETs.json').write_text(json.dumps(netrows,indent=2)+'\n');cells=[dict(old=k[0],current=k[1],truth=k[2],edit_mask=k[3],count=v,squared_error_delta=pair(errors[k])) for k,v in sorted(counts.items())];row=dict(case=c['case'],resource_rows=sum(counts.values()),edited_NET_counts=dict(Counter(r['edit_mask'] for r in netrows)),cells=cells,total_squared_error_delta=pair(sum(errors.values(),F(0))));rows.append(row)
  for p in [out/'resources.jsonl',out/'NETs.json',T/c['case']/'comparison.json',Path(s['label_physical_audit']),Path(c['source_frame']),Path(c['current_frame'])]:bindings[str(p)]=sha(p)
  print(c['case'],row['edited_NET_counts'],'SSE_delta',float(sum(errors.values(),F(0))),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'summary.json').write_text(json.dumps(dict(status='ALL3_FULL_DOMAIN_TEMPORAL_ERROR_ATTRIBUTION_COMPLETE',rows=rows,bindings=bindings,scope='Descriptive development error diagnosis only; no acceptance or calibration claim.'),indent=2)+'\n')
if __name__=='__main__':main()
