"""Compare same-placement repeat complete route trees, edges and occupancy."""
import json,re,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_same_place_cold_control_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def parse(path):
 result={};net=None
 for line in path.read_text().splitlines():
  if line.startswith('Net '):
   m=re.fullmatch(r'Net (\d+) \((.*)\)',line.strip());net=int(m[1]) if m else None
   if net is not None:assert net not in result;result[net]=[]
  elif line.startswith('Node:'):
   assert net is not None;result[net].append(line.strip())
 return result

def main():
 p=read(D/'protocol.json');old=Path(p['source_verification']);new=D/'native/verification.json';bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)}
 for f in [old,new]:
  d=read(f);assert d['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and d['exit_status']==0 and d['canonical']['semantic_consistency_gate_pass'];assert all(sha(q)==h for q,h in d['bindings'].items());bindings[str(f)]=sha(f)
 source=old.parent/'output.route';repeat=new.parent/'output.route';a,b=parse(source),parse(repeat);assert a.keys()==b.keys();changed=[n for n in a if a[n]!=b[n]];supports_changed=[n for n in a if {int(x.split()[1]) for x in a[n]}!={int(x.split()[1]) for x in b[n]}];ap=read(old.parent/'physical_audit.json');bp=read(new.parent/'physical_audit.json');same_occupancy=ap['node_occupancy']==bp['node_occupancy'];assert read(old.parent/'protocol.json')['command']==read(new.parent/'protocol.json')['command'];inputs={k:sha(old.parent/k)==sha(new.parent/k) for k in ['design.blif','design.net','design.place']};assert all(inputs.values())
 for f in [source,repeat]:bindings[str(f)]=sha(f)
 result=dict(status='SAME_PLACEMENT_COLD_REPEAT_PHYSICAL_AND_CANONICAL_AUDITED',same_inputs=inputs,same_explicit_command=True,NETs=len(a),changed_printed_tree_NETs=changed,changed_support_NETs=supports_changed,same_full_occupancy=same_occupancy,source_iterations=read(old)['iterations'],repeat_iterations=read(new)['iterations'],source_wirelength=read(old)['wirelength'],repeat_wirelength=read(new)['wirelength'],bindings=bindings,scope='One same-placement same-seed repeat. Tree comparison includes ordered printed nodes/types/switches, ignores route header paths; not proof across hosts/runs/configurations. Original label cohort unchanged.')
 with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
if __name__=='__main__':main()
