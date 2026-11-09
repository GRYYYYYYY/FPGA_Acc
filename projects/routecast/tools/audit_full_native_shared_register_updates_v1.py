"""Exact same-net update signatures for native-merged register groups."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
P=E/'full_structural_native_register_mapping_v1_2026-10-09/mapping_audit.json';F=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json'
a=json.loads(P.read_text());m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})))
groups=collections.defaultdict(list)
for r in a['rows']:
 if r['status']=='unique_native_state':groups[r['native_candidates'][0]].append(r)
records=[]
for target,rs in groups.items():
 if len(rs)<2:continue
 members=[]
 for r in rs:
  c=m['cells'][r['cell']];lane=r['lane'];params={k:v for k,v in c['parameters'].items() if k not in ['WIDTH','ARST_VALUE','SRST_VALUE']}
  for k in ['ARST_VALUE','SRST_VALUE']:
   if k in c['parameters']:params[k]=c['parameters'][k][-1-lane]
  signature={'type':c['type'],'parameters':params,'inputs':{p:([bs[lane]] if p=='D' else bs) for p,bs in c['connections'].items() if c['port_directions'][p]=='input'}}
  members.append({'cell':r['cell'],'lane':lane,'q':r['bit'],'signature':signature,'init_attributes':r['init_attributes']})
 equal=all(x['signature']==members[0]['signature'] for x in members)
 records.append({'native_q':target,'members':members,'exact_same_update_inputs':equal,'initial_equality_proven':False})
report={'groups':len(records),'exact_same_update_groups':sum(r['exact_same_update_inputs'] for r in records),'nonidentical_groups':sum(not r['exact_same_update_inputs'] for r in records),'input_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,F]},'records':records,'scope':'Equal signatures prove same register update function on identical actual input nets, conditional on equal held Q when enable is inactive. No initial equality or native transition equivalence is proved. Nonidentical signatures require expression or formal proof.'}
D=E/'full_native_shared_register_updates_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'update_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
