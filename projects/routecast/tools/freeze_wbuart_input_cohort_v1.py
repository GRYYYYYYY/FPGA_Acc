"""Freeze label-free widths/three independent CLB swaps; not a predictor trial."""
import datetime,hashlib,itertools,json,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'experiments/wbuart_development_place_v1_2026-10-20';O=R/'experiments/wbuart_input_cohort_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False);ap=S/'independent_verification_v1.json';a=json.loads(ap.read_text());assert a['blocks']==162 and a['CLBs']==78 and a['grid']==[12,12]
 for n,h in a['bindings'].items():assert sha(Path(n))==h
 template=R/'experiments/prospective_external_family_concrete_cohort_draft_v1_2026-10-18/draft.json';old=json.loads(template.read_text());assert old['proposed_width_cohort']==[96,128,160]
 protocol={'status':'DEVELOPMENT_INPUT_SELECTION_ONLY_NOT_EXECUTABLE_PREDICTION_UTILITY_TRIAL','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'widths':[96,128,160],'source':'One verified seed1/width128 placement reused across widths; each width has a separate native RR graph epoch.','targets':'Three independent single swaps from source, never chained.','selection':'Sort source CLBs by exact name; first three disjoint name-ordered pairs at distinct locations with identical full physical type and subtile. Current fixed-profile placement audit proves all source CLBs occupy physical clb/subtile0/layer0. RR-grid/native placement checks remain mandatory before prediction/routing.','native_iteration_limit':300,'failure_policy':'Retain every width, source failure and unavailable target; no new width/seed/pair or increased native iteration budget based on routing outcomes.','family_role':'Development candidate only; strict unseen not certified, lineage scan pending.','not_ready':['Native per-width graph/domain/terminal and all target placement checks.','New-epoch CIDs, RC floors, budgets and timing/context inputs.','Complete preregistered predictor/ablation/native-utility/full-paid-time configuration.'],'preserved':'Existing ChaCha cohort, six unavailable cases, original labels/metrics/gates/negative results unchanged. New family never substitutes for their missing results.','bindings':{str(p):sha(p) for p in [Path(__file__),ap,S/'source.place',S/'design.net',template]}}
 save('protocol.json',protocol)
 names={b.get('name'):b.get('instance').split('[')[0] for b in ET.parse(S/'design.net').getroot().findall('block')};loc={};original=(S/'source.place').read_text().splitlines(keepends=True)
 for row in original:
  t=row.split()
  if len(t)==6 and t[0] in names:loc[t[0]]=tuple(map(int,t[1:5]));assert loc[t[0]][2:]==(0,0) if names[t[0]]=='clb' else True
 eligible=sorted(n for n in names if names[n]=='clb');used=set();pairs=[]
 for x,y in itertools.combinations(eligible,2):
  if x in used or y in used or loc[x]==loc[y]:continue
  pairs.append((x,y));used.update((x,y))
  if len(pairs)==3:break
 assert len(pairs)==3;rows=[]
 for i,(x,y) in enumerate(pairs,1):
  d=O/f'episode_{i:02d}';d.mkdir();text=[]
  for row in original:
   t=row.split()
   if t and t[0] in (x,y):new=loc[y] if t[0]==x else loc[x];text.append(t[0]+'\t'+'\t'.join(map(str,new))+'\t'+t[5]+'\n')
   else:text.append(row)
  target=d/'design.place';target.write_text(''.join(text));newloc={}
  for row in target.read_text().splitlines():
   t=row.split()
   if len(t)==6 and t[0] in names:newloc[t[0]]=tuple(map(int,t[1:5]))
  assert set(newloc)==set(loc) and set(newloc.values())==set(loc.values()) and {n for n in loc if loc[n]!=newloc[n]}=={x,y}
  rows.append({'episode':i,'blocks':[x,y],'before':[loc[x],loc[y]],'place':str(target),'sha256':sha(target),'native_graph_and_terminal_check':'pending'})
 save('selection.json',{'rows':rows,'source_unchanged':sha(S/'source.place')==protocol['bindings'][str(S/'source.place')],'new_route_labels':False,'strict_unseen_admitted':False})
 print('INPUT_COHORT_FROZEN',3,len(rows),flush=True)
if __name__=='__main__':main()
