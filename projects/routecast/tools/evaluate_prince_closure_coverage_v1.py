"""Join frozen input-only closures to already exposed development native changes."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from diagnose_prince_native_route_churn_v2 import native
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_closure_coverage_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);bindings={str(Path(__file__)):sha(__file__)};selections={};rows=[]
 for mode,root in [('CHANNEL','prince_congestion_closures_v1_2026-10-20'),('spatial','prince_spatial_closures_v1_2026-10-20')]:
  p=E/root/'verification.json';v=json.loads(p.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings[str(p)]=sha(p)
  for row in v['rows']:
   s=Path(row['selection']);assert sha(s)==row['sha256'];d=json.loads(s.read_text());assert not d['label_inputs'];assert all(sha(f)==h for f,h in d['bindings'].items());selections[mode,row['case']]=d;bindings[str(s)]=sha(s)
 for width in [128,160]:
  base=E/'prince_native_cohort_v1_2026-10-20'/f'w{width}';src=base/'source';rp=E/'prince_quality_domains_v1_2026-10-20'/f'w{width}'/'resources.jsonl';resources={x['id'] for x in map(json.loads,rp.open())};source=native(src/'output.route',src/'physical_audit.json',resources)
  for f in [rp,src/'output.route',src/'physical_audit.json']:bindings[str(f)]=sha(f)
  for i in [1,2,3]:
   case=f'w{width}/episode_{i:02d}';target=base/f'episode_{i:02d}';ep=target/'pre_route_endpoints.json';meta=json.loads(ep.read_text());names={int(n):name for n,name in meta['net_names'].items()};final=native(target/'output.route',target/'physical_audit.json',resources);s=selections['CHANNEL',case];nets=set(s['NETs']);dirty=set(s['dirty_NETs']);clean=nets-dirty;changed={n for n in clean if source.get(names[n],set())!=final.get(names[n],set())};result={}
   for mode in ['CHANNEL','spatial']:
    d=selections[mode,case];assert set(d['NETs'])==nets and set(d['dirty_NETs'])==dirty;result[mode]={}
    for policy,ids in d['policies'].items():
     selected=set(ids);chosen=selected&clean;hit=len(chosen&changed);result[mode][policy]=dict(selected_NETs=len(selected),all_NETs=len(nets),selected_clean_NETs=len(chosen),native_changed_clean_NETs=len(changed),covered_changed_clean_NETs=hit,missed_changed_clean_NETs=len(changed)-hit,clean_change_recall=hit/len(changed),clean_change_precision=hit/len(chosen) if chosen else None)
   rows.append(dict(case=case,coverage=result))
   for f in [ep,target/'output.route',target/'physical_audit.json']:bindings[str(f)]=sha(f)
   print('COVERAGE',case,'channel_full',result['CHANNEL']['dirty_fixedpoint'],'spatial_1',result['spatial']['dirty_1'],flush=True)
 assert all(sha(f)==h for f,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Coverage of exact native source-to-cold-target clean NET CHANNEL set changes only. Input closures frozen before this join but development labels already exposed historically; no unseen/blind validation. High coverage may select nearly allNETs; no forecast accuracy, native benefit or speedup claim.'),indent=2)+'\n')
if __name__=='__main__':main()
