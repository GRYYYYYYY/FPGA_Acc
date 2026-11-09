"""Check state/output coverage and clock assumptions of the proved equiv model."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=R/'experiments/prospective_external_family_inductive_step_v1_2026-10-18';jp=d/'before.json';rp=d/'receipt.json';receipt=json.loads(rp.read_text());assert receipt['step_pass'] and receipt['properties']==1970
 for mapping in [receipt['bindings'],receipt['files']]:
  for p,h in mapping.items():assert sha(Path(p))==h
 m=json.loads(jp.read_text())['modules']['equiv'];clock=m['ports']['clk']['bits'];assert len(clock)==1
 states={s:set() for s in ['gold','gate']};types=collections.Counter();pairs=[];seqtypes={'$dff','$dffe','$sdff','$sdffe'}
 for name,c in m['cells'].items():
  if 'CLK' in c['connections']:
   assert c['type'] in seqtypes,(name,c['type'])
   side='gold' if name.endswith('_gold') else 'gate' if name.endswith('_gate') else None;assert side
   assert c['connections']['CLK']==clock and int(c['parameters']['CLK_POLARITY'],2)==1
   q=c['connections']['Q'];assert not states[side].intersection(q);states[side].update(q);types[side+':'+c['type']]+=len(q)
  if c['type']=='$equiv':
   assert all(len(c['connections'][p])==1 for p in ['A','B','Y']);pairs.append(tuple(c['connections'][p][0] for p in ['A','B','Y']))
 assert len(states['gold'])==len(states['gate'])==1938 and len(pairs)==1970
 for index,side in enumerate(['gold','gate']):
  observed=[p[index] for p in pairs];assert states[side].issubset(observed)
  assert all(observed.count(bit)==1 for bit in states[side])
 statepairs=[p for p in pairs if p[0] in states['gold'] or p[1] in states['gate']];assert len(statepairs)==1938 and all(a in states['gold'] and b in states['gate'] for a,b,y in statepairs)
 outputs={bit for port in m['ports'].values() if port['direction']=='output' for bit in port['bits']};assert len(outputs)==32
 outputpairs=[p for p in pairs if p[2] in outputs];assert len(outputpairs)==32 and len({p[2] for p in outputpairs})==32
 assert set(statepairs).isdisjoint(outputpairs) and len(statepairs)+len(outputpairs)==len(pairs)
 assert not any('init' in n.get('attributes',{}) for n in m['netnames'].values())
 out=R/'experiments/prospective_external_family_equiv_state_coverage_v1_2026-10-18';out.mkdir(exist_ok=False)
 result=dict(status='all_state_bits_and_outputs_bijectively_covered_single_positive_clock',bindings={str(p):sha(p) for p in [Path(__file__),jp,rp]},state_bits_per_design=1938,public_output_bits=32,total_properties=1970,sequential_bit_types=dict(types),clock='clk',positive_edge_only=True,explicit_initial_state_attributes=0,scope='All model register Q bits have exactly one paired property, all outputs have one separate property. This strengthens interpretation of the proved reset and induction lemmas; it does not add original HDL/four-state, physical clock/reset timing, undefined-input or external family-history guarantees.',strict_unseen_admitted=False)
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
