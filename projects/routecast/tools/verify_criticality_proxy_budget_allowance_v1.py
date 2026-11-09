"""Independent rational budget contract and full development-input accounting, no route labels."""
import hashlib,json,math,resource,struct
from collections import Counter
from fractions import Fraction
from pathlib import Path
from criticality_proxy_budget_allowance_v1 import budget,POLICY
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 resource.setrlimit(resource.RLIMIT_AS,(768*2**20,768*2**20))
 out=R/'experiments/neuron_criticality_proxy_budget_prereg_v1_2026-10-17';assert not (out/'verification.json').exists()
 protocol=json.loads((out/'protocol.json').read_text())
 for p,h in protocol['bindings'].items():assert sha(Path(p))==h
 cases=0
 for floor in range(101):
  for original in sorted({max(1,floor),max(1,2*floor),max(1,floor+17)}):
   previous=None
   for n in range(65):
    c=Fraction(n,64);got=budget(floor,original,c);reference=original+math.ceil(Fraction(floor)*(1-c))
    assert got==reference and original<=got<=original+floor
    assert previous is None or got<=previous;previous=got;cases+=1
   assert budget(floor,original,Fraction(1))==original and budget(floor,original,Fraction(0))==original+floor
 for floor,original,c in [(True,1,Fraction(0)),(-1,1,Fraction(0)),(2,1,Fraction(0)),(0,0,Fraction(0)),(0,1,Fraction(-1)),(0,1,Fraction(2)),(0,1,0.5)]:
  try:budget(floor,original,c)
  except ValueError:pass
  else:raise AssertionError('invalid inputs accepted')
 for floor in [2**127-1,2**240-1]:
  c=Fraction(16777215,16777216);assert budget(floor,floor,c)==floor+math.ceil(Fraction(floor)*(1-c));cases+=1
 initial=R/'experiments/neuron_continue_primary_trial_v1_2026-10-17/model/initial.json'
 manifest=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json'
 atom=R/'experiments/neuron_initial_timing_snapshot_v1_2026-10-17/per_cluster_atom_identity_bits.json'
 records=json.loads(initial.read_text())['records'];old={x['connection_id']:x for x in records};pins=json.loads(manifest.read_text());atoms=json.loads(atom.read_text());seen=set();counts=Counter();rows=[];maxbits=0
 for m in pins:
  cid=m['connection_id'];assert cid not in seen;seen.add(cid);o=old[cid]
  assert (m['net'],m['source_rr'],m['target_rr'])==(o['net_id'],o['source'],o['sink'])
  packed=struct.pack('<f',float(m['criticality_float32_text']));c=Fraction(struct.unpack('<f',packed)[0]);a=atoms[f"{m['net']}:{m['local_sink_pin']}"]
  assert a['global_pin']==m['global_pin'] and a['transformed_criticality_bits']==f'{int.from_bytes(packed,"little"):08x}' and not a['ignored']
  floor,original=o['floor_integer'],o['budget_integer'];assert original==max(10**20,(3*floor+1)//2)
  value=budget(floor,original,c);reference=Fraction(original)+Fraction(floor)*(1-c)
  assert value>=reference and value-reference<1 and original<=value<=original+floor
  counts['connections']+=1;counts['changed_budgets']+=value!=original;counts['zero_floor']+=floor==0;counts['zero_criticality']+=c==0
  maxbits=max(maxbits,value.bit_length());rows.append(dict(connection_id=cid,net=m['net'],local_sink_pin=m['local_sink_pin'],global_pin=m['global_pin'],floor_integer=floor,original_budget_integer=original,new_budget_integer=value,criticality_numerator=c.numerator,criticality_denominator=c.denominator))
 assert seen==set(old)==set(range(77106)) and counts['zero_floor']==6669
 output=out/'candidate_budgets.jsonl'
 with output.open('x') as f:
  for row in sorted(rows,key=lambda r:r['connection_id']):f.write(json.dumps(row,separators=(',',':'))+'\n')
 files=[Path(__file__).resolve(),R/'tools/criticality_proxy_budget_allowance_v1.py',out/'protocol.json',initial,manifest,atom,output]
 result=dict(all_pass=True,policy=POLICY,arithmetic_contract_cases=cases,invalid_cases_rejected=7,counts=dict(counts),maximum_candidate_budget_bits=maxbits,all_full_CID_and_pin_identity_and_original_budget_formula_checked=True,independent_rational_ceiling_reconstruction=True,bindings={str(p):sha(p) for p in files},scope='No model launched, native route labels read, budgets applied, quality change or timing feasibility established. Formula is frozen proxy hypothesis only.',promoted=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
if __name__=='__main__':main()
