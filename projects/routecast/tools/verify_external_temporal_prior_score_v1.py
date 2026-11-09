"""Independent XML support reconstruction, score arithmetic and rank/gate audit."""
import json,sys,math
import xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from verify_external_zero_feedback_warm_metrics_v1 import correlation
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_temporal_prior_utilization_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 summary=read(D/'quality_summary.json');assert all(sha(p)==h for p,h in summary['bindings'].items());bindings=dict(summary['bindings']);bindings[str(D/'quality_summary.json')]=sha(D/'quality_summary.json');bindings[str(Path(__file__).resolve())]=sha(__file__)
 c=read(D/'protocol.json')['cases'][0];spec=read(c['original_comparison_spec']);ep=read(spec['endpoint']);dest=[]
 stack=[]
 for event,e in ET.iterparse(ep['inputs']['graph']['path'],events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='edge' and parent=='rr_edges':dest.append(int(e.attrib['sink_node']))
  if (e.tag,parent) in [('edge','rr_edges'),('node','rr_nodes'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 rows=[]
 for case in read(D/'protocol.json')['cases']:
  sp=D/case['case']/'comparison_spec.json';s=read(sp);result=read(D/case['case']/'comparison.json');bindings.update(result['bindings'])
  folder=Path(s['domain_proof']).parent;resources=[json.loads(x) for x in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');domain=read(s['domain_proof']);ids={r['id'] for r in resources};by_node=defaultdict(list)
  old=read(case['source_frame']);new=read(case['current_frame']);nets=[]
  for frame in [old,new]:
   groups=defaultdict(dict)
   for q in frame['records']:groups[q['net_id']][q['connection_id']]=q
   nets.append(groups)
  assert nets[0].keys()==nets[1].keys()
  for net,oa in nets[0].items():
   nb=nets[1][net];assert oa.keys()==nb.keys()
   changes=int({q['source'] for q in oa.values()}!={q['source'] for q in nb.values()})+sum(q['sink']!=nb[c]['sink'] for c,q in oa.items());alpha=F(changes,len(oa)+1)
   assert result['pin_edit_weights'][str(net)]==[alpha.numerator,alpha.denominator]
   supports=[]
   for group in [oa,nb]:
    support=set()
    for q in group.values():support.add(q['source']);support.update(dest[e] for e in q['answer']['physical_edge_ids'])
    supports.append(support&ids)
   for n in supports[0]|supports[1]:by_node[n].append((1-alpha if n in supports[0] else 0)+(alpha if n in supports[1] else 0))
  score={}
  for n in ids:
   complement=F(1)
   for p in by_node[n]:complement*=1-p
   score[n]=1-complement
  def aggregate(values):
   total=Counter()
   for r in resources:
    for key in r['bins']:total[tuple(key)]+=values.get(r['id'],0)
   return dict(resource={r['id']:F(values.get(r['id'],0),r['capacity']) for r in resources},spatial={tuple(b['key']):total[tuple(b['key'])]/b['capacity'] for b in bins})
  predicted=aggregate(score)
  for scope in predicted:
   exported={tuple(k) if isinstance(k,list) else k:F(*v) for k,v in result['score_vectors'][scope]};assert exported==predicted[scope]
  truth=aggregate({int(n):v for n,v in read(s['label_physical_audit'])['node_occupancy'].items()});vectors={'native_retained_on':predicted}
  for name,path in [('previous_native',s['source_frame']),('raw_min_on',s['predictions']['raw_min_on']['frame'])]:vectors[name]=aggregate({int(n):v for n,v in read(path)['ledger'].items()})
  computed={}
  for name,vector in vectors.items():
   computed[name]={}
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    a,b=vector[scope],truth[scope];order=sorted(b);p=sorted(order,key=lambda n:(-a[n],n))[:k];t=sorted(order,key=lambda n:(-b[n],n))[:k];rho=correlation([a[n] for n in order],[b[n] for n in order]);hits=len(set(p)&set(t));m=result['metrics'][name][scope]
    assert abs(rho-m['spearman'])<1e-12 and hits==m['top_k_hits'] and len(order)==m['universe_size'] and k==m['k']
    computed[name][scope]=(rho,hits);rows.append(dict(case=case['case'],method=name,scope=scope,spearman=rho,top_k_hits=hits))
  passes=[]
  for control in ['previous_native','raw_min_on']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,h=computed['native_retained_on'][scope];b,j=computed[control][scope];nonreg.extend([a>=b-1e-12,h>=j]);strict.extend([a>b+1e-12,h>j])
   passed=all(nonreg) and any(strict);assert passed==result['checks'][control]['pass_primary_gate'];passes.append(passed)
  assert all(passes)==result['pass_case_gate']
 assert all(sha(p)==h for p,h in bindings.items())
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_XML_SUPPORT_SCORES_AND18_METRIC_VECTORS_AND_GATES_INDEPENDENTLY_VERIFIED',bindings=bindings,rows=rows),f,indent=2)
 print('ALL3_SCORES_18_METRIC_VECTORS_AND_GATES_VERIFIED')
if __name__=='__main__':main()
