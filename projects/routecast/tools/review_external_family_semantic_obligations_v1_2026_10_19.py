"""Fresh source-proof scope review; inherits solver results without rerunning jobs."""
import json,re
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prospective_external_family_semantic_review_v1_2026-10-19';out.mkdir(exist_ok=False);base=R/'experiments/prospective_external_family_reset_defined_v1_2026-10-18';ind=R/'experiments/prospective_external_family_defined_induction_v1_2026-10-18';coverage=R/'experiments/prospective_external_family_defined_property_coverage_v1_2026-10-18/verification.json';composition=ind/'terminal_composition_review_v1.json';docs=[base/'receipt.json',ind/'receipt.json',coverage,composition];bindings={str(Path(__file__).resolve()):sha(__file__)}
 for p in docs:
  x=read(p)
  for f,h in x.get('bindings',{}).items():assert sha(f)==h
  bindings[str(p)]=sha(p)
 br,ir,cv,co=map(read,docs);assert br['passed'] and ir['passed'] and co['conditional_unbounded_defined_equality'];assert not co['original_unrestricted_equivalence_satisfied'] and not co['strict_unseen_admitted'];mp=base/'strict_miter.json';m=read(mp)['modules']['base_miter'];cells=m['cells'];drivers={b:c for c in cells.values() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};pairs=[]
 for c in cells.values():
  if c['type']!='$assert':continue
  assert c['connections']['EN']==['1'];gate=drivers[c['connections']['A'][0]];assert gate['type']=='$logic_and';both=drivers[gate['connections']['A'][0]];eq=drivers[gate['connections']['B'][0]];assert both['type']=='$logic_and' and eq['type']=='$eqx';a,b=eq['connections']['A'],eq['connections']['B'];assert len(a)==len(b)==1
  for port,operand in [('A',a),('B',b)]:
   neg=drivers[both['connections'][port][0]];assert neg['type']=='$logic_not';probe=drivers[neg['connections']['A'][0]];assert probe['type']=='$eqx' and probe['connections']['A']==operand and probe['connections']['B']==['x']
  pairs.append((a[0],b[0]))
 assert len(set(pairs))==len(pairs)==1970 and not any(c['type']=='$assume' for c in cells.values());qs={b for c in cells.values() if 'dff' in c['type'] for b in c['connections']['Q']};counts=Counter(b for pair in pairs for b in pair);assert len(qs)==3876 and all(counts[q]==1 for q in qs);assert sum(a in qs and b in qs for a,b in pairs)==1938
 bp=read(base/'protocol.json');ip=read(ind/'protocol.json');assert bp['bindings'][str(mp)]==ip['bindings'][str(mp)]==sha(mp);assert bp['commands'][0]==ip['commands'][0]==f'read_json "{mp}"';assert '-set-init-def' in bp['commands'][-1] and '-prove-skip 1' in bp['commands'][-1];assert '-set-at 1 reset_n 0 -set-at 2 reset_n 0 -set-at 3 reset_n 1' in bp['commands'][-1];assert '-tempinduct-inductonly' in ip['commands'][-1] and '-set-def-inputs' in ip['commands'][-1] and '-set-init' not in ip['commands'][-1] and '-set-at' not in ip['commands'][-1]
 blog=(base/'prove.log').read_text();ilog=(ind/'prove.log').read_text();assert 'SAT proof finished - no model found: SUCCESS!' in blog and '[induction step 1]' in ilog and 'Induction step proven: SUCCESS!' in ilog;assert sha(ind/'prove.log')==ir['log_sha256']
 pid=990092;proc=Path('/proc')/str(pid);live=None
 if proc.exists():
  cmd=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode();assert 'prospective_external_family_source_equivalence_v1_2026-10-18/commands.ys' in cmd;stat=(proc/'stat').read_text().rsplit(') ',1)[1].split();log=R/'experiments/prospective_external_family_source_equivalence_v1_2026-10-18/check.log';text=log.read_text();live=dict(pid=pid,start_ticks=stat[19],state=stat[0],verified_utc=datetime.now(timezone.utc).isoformat(),completed_success_lines=text.count(': success!'),log_tail_snapshot=text[-600:],terminal_certificate_present=(log.parent/'receipt.json').exists())
 for p in [mp,base/'protocol.json',ind/'protocol.json',base/'prove.log',ind/'prove.log']:bindings[str(p)]=sha(p)
 result=dict(status='CONDITIONAL_UNBOUNDED_DEFINED_EQUALITY_REVALIDATED_FULL_HDLSCOPE_STILL_OPEN',created_utc=datetime.now(timezone.utc).isoformat(),properties=1970,state_pairs=1938,output_pairs=32,conditional_proof_composed=True,scope=co['scope'],assumptions=co['assumptions'],full_HDL_four_state_equivalence=False,strict_unseen_admitted=False,source_equivalence_live_observation=live,bindings=bindings,next_action='Preserve live unrestricted proof; treat conditional-reset model as a separately stated development contract. Review family-history/exposure certificates and source-to-packed LUT proof coverage before any strict unseen assignment; user external-history answer remains evidence only, not automatic admission.')
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print('Fresh1970-property coverage, same-miter/base/induction/log hashes verified; live proof preserved.')
if __name__=='__main__':main()
