"""Authenticate full replay and compare every semantic output to frozen originals."""
import json,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/resident_unique_rc_lattice_replay_v1_2026-10-09';P=R/'experiments/resident_hybrid_complete_v5_2026-10-08/xtea/resident'
bindings={str(Path(__file__)):sha(Path(__file__)),str(D/'stages.json'):sha(D/'stages.json')};rows=[]
stages=json.loads((D/'stages.json').read_text());assert [x['stage'] for x in stages]==['initial','sketch','events'] and all(x['exit_code']==0 for x in stages)
for label,original in [('initial','initial_physical_verification.json'),('sketch','sketch_physical_verification.json'),('events','verification.json')]:
 new=D/(label+'_verification.json');old=P/original;a,b=[json.loads(p.read_text()) for p in [new,old]]
 for data in [a,b]:
  for p,h in data['bindings'].items():assert sha(p)==h
 assert {k:v for k,v in a.items() if k!='bindings'}=={k:v for k,v in b.items() if k!='bindings'}
 assert a['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 bindings.update({str(p):sha(p) for p in [new,old,D/(label+'.log')]})
 rows.append(dict(stage=label,all_semantic_fields_equal=True,completed=a['completed'],overflow_units=a['overflow_units'],events=a.get('events')))
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,full_initial_final_and_events_semantically_equal=True,rows=rows,scope='Complete original XTEA development case replay. Historical results preserved. Different-time stages do not prove speedup, MMC complete gain, unseen-family behavior or hardware performance.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
