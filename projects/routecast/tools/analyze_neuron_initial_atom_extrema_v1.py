"""Read-only initialized atom-extrema identity accounting; no budget calibration."""
import hashlib,json,math,struct
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def val(bits):return struct.unpack('<f',bytes.fromhex(bits)[::-1])[0]
def main():
 root=R/'experiments/neuron_initial_timing_snapshot_v1_2026-10-17'
 verification=json.loads((root/'verification.json').read_text())
 assert verification['all_pass'] and json.loads((root/'terminal.json').read_text())['exit_status']==0
 for p,h in verification['bindings'].items():assert sha(Path(p))==h
 rows=json.loads((root/'per_cluster_atom_identity_bits.json').read_text())
 counts={k:Counter() for k in ['all','nonignored','ignored']};examples=[]
 for key,row in rows.items():
  atoms=row['atoms'];slack=val(row['slack_bits']);crit=val(row['raw_criticality_bits'])
  s={a['atom_pin'] for a in atoms if val(a['slack_bits'])==slack}
  c={a['atom_pin'] for a in atoms if val(a['criticality_bits'])==crit}
  assert s and c
  different=not bool(s&c)
  for group in ['all','ignored' if row['ignored'] else 'nonignored']:
   z=counts[group];z['pins']+=1;z['multiple_atom_pins']+=len(atoms)>1
   z['disjoint_extrema_atom_sets']+=different;z['overlapping_extrema_atom_sets']+=not different
   z['finite_slack']+=math.isfinite(slack);z['negative_slack']+=slack<0
   z['slack_extremum_tied']+=len(s)>1;z['criticality_extremum_tied']+=len(c)>1
  if different and len(examples)<12:examples.append(dict(cluster_key=key,ignored=row['ignored'],atom_count=len(atoms),min_slack_atom_ids=sorted(s),max_criticality_atom_ids=sorted(c),slack_bits=row['slack_bits'],criticality_bits=row['raw_criticality_bits']))
 assert counts['all']['pins']==92608 and counts['nonignored']['pins']==77106
 out=root/'atom_extrema_identity_analysis_v1.json';assert not out.exists()
 result=dict(all_pass=True,counts={k:dict(v) for k,v in counts.items()},examples=examples,bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(root/'verification.json'):sha(root/'verification.json'),str(root/'per_cluster_atom_identity_bits.json'):sha(root/'per_cluster_atom_identity_bits.json')},scope='Initialized worst-path atom slack and criticality extrema identity only. Shared atom identity does not establish shared timing path/domain or connection additive delay allowance. No budget/model/native route change.',promoted=False)
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['counts'],indent=2))
if __name__=='__main__':main()
