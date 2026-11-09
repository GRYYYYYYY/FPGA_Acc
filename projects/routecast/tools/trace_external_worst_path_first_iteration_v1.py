"""All seeded worst-path external points: initial seed/first iteration/final paths."""
import json,sys,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from native_route_ledger_import_compact import physical_paths
A=R/'experiments/prospective_external_family_final_critical_path_attribution_v1_2026-10-19';P=R/'experiments/prospective_external_family_native_seed_delay_handoff_v1_2026-10-19';S=R/'experiments/prospective_external_family_native_utility_seed_inputs_v1_2026-10-19';D=R/'experiments/prospective_external_family_worst_path_first_iteration_v1_2026-10-19';G=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 v=json.loads((A/'attribution.json').read_text());assert all(sha(p)==h for p,h in v['bindings'].items());D.mkdir(exist_ok=False);weights={}
 for event,e in ET.iterparse(G,events=('start','end')):
  if event=='start' and e.tag=='rr_nodes':break
  if event=='end' and e.tag=='switch':
   t=e.find('timing');q=Fraction(t.get('Tdel','0'))*10**18;assert q.denominator==1;weights[int(e.get('id'))]=q.numerator
 bindings={str(G):sha(G),str(A/'attribution.json'):sha(A/'attribution.json'),str(Path(__file__).resolve()):sha(__file__)};results=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';p=A/case/'seed/worst_path_points.json';points=json.loads(p.read_text());bindings[str(p)]=sha(p);maps={}
  for name,path in [('input_seed',S/case/'seed.route'),('cold_first',P/case/'cold/native/first_iteration.route'),('seed_first',P/case/'seed/native/first_iteration.route')]:
   bindings[str(path)]=sha(path);out={}
   for net,ps in physical_paths(path).items():
    for q in ps:
     k=(net,q[0][0],q[-1][0]);assert k not in out or out[k]==q;out[k]=q
   maps[name]=out
  rows=[]
  for r in points:
   if r['classification']!='EXTERNAL_NATIVE_CID':continue
   k=(r['native_net_name'],r['source_rr'],r['sink_rr']);delays={}
   for name,mp in maps.items():
    q=mp.get(k);delays[name+'_as']=sum(weights[s] for n,s in q[1:]) if q else None
   rows.append(dict(CID_candidates=r['CID_candidates'],net=k[0],source_rr=k[1],sink_rr=k[2],cold_final_as=r['cold_delay_as'],seed_final_as=r['final_delay_as'],final_delta_as=r['delta_as'],**delays))
  summary=dict(case=case,external_points=len(rows),rows=rows);results.append(summary)
 assert all(sha(p)==h for p,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(status='ALL_SEEDED_WORST_PATH_EXTERNAL_POINTS_FIRST_ITERATION_TRACED',rows=results,bindings=bindings,scope='Posthoc trace, not policy fitting or causal proof. First iteration routes not separately complete canonical-admitted states. Original full graph audit zeroRC prerequisite inherited; switch sum only for these observation files.'),indent=2)+'\n')
 for r in results:
  print(r['case'],json.dumps(max(r['rows'],key=lambda q:q['final_delta_as'])))
if __name__=='__main__':main()
