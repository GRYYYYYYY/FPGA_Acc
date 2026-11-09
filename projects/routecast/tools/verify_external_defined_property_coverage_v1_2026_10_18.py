"""Exact strict property structure and all-register coverage, independent of SAT."""
import pathlib,json,hashlib
from collections import Counter
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 out=R/'experiments/prospective_external_family_defined_property_coverage_v1_2026-10-18';out.mkdir();base=R/'experiments/prospective_external_family_reset_defined_v1_2026-10-18';ind=R/'experiments/prospective_external_family_defined_induction_v1_2026-10-18';mp=base/'strict_miter.json';m=json.loads(mp.read_text())['modules']['base_miter'];cells=m['cells'];drivers={b:c for c in cells.values() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};pairs=[]
 for c in cells.values():
  if c['type']!='$assert':continue
  assert c['connections']['EN']==['1'];final=drivers[c['connections']['A'][0]];assert final['type']=='$logic_and';both=drivers[final['connections']['A'][0]];eq=drivers[final['connections']['B'][0]];assert both['type']=='$logic_and' and eq['type']=='$eqx';a,b=eq['connections']['A'],eq['connections']['B'];assert len(a)==len(b)==1
  for port,operand in [('A',a),('B',b)]:
   neg=drivers[both['connections'][port][0]];assert neg['type']=='$logic_not';probe=drivers[neg['connections']['A'][0]];assert probe['type']=='$eqx' and probe['connections']['A']==operand and probe['connections']['B']==['x']
  pairs.append((a[0],b[0]))
 assert len(pairs)==len(set(pairs))==1970;assert not any(c['type']=='$assume' for c in cells.values());qs={b for c in cells.values() if 'dff' in c['type'] for b in c['connections']['Q']};counts=Counter(b for pair in pairs for b in pair);assert len(qs)==3876;assert all(counts[q]==1 for q in qs);assert sum(a in qs and b in qs for a,b in pairs)==1938;assert sum(a not in qs and b not in qs for a,b in pairs)==32
 bp=json.loads((base/'protocol.json').read_text());ip=json.loads((ind/'protocol.json').read_text());h=sha(mp);assert bp['bindings'][str(mp)]==ip['bindings'][str(mp)]==h;assert bp['commands'][0]==ip['commands'][0]==f'read_json "{mp}"';assert '-set-def-inputs' in ip['commands'][-1] and '-set-at' not in ip['commands'][-1] and '-set-init' not in ip['commands'][-1]
 bindings={str(p):sha(p) for p in [pathlib.Path(__file__).resolve(),mp,base/'protocol.json',ind/'protocol.json']};v=dict(status='all1970_strict_properties_and_all3876_register_bits_covered_once',bindings=bindings,properties=1970,state_pairs=1938,nonstate_pairs=32,assume_cells=0,same_base_and_induction_miter_bytes=True,induction_solver_passed=False,scope='Structural certificate only. Every assertion requires both definedness and exact case equality, all register Q bits covered exactly once. No SAT induction result, startup equivalence, family admission or physical timing claim.')
 (out/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'])
if __name__=='__main__':main()
