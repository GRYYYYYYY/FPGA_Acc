"""Audit actual equivalence properties, state omissions and initialization scope."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/wbuart_source_equivalence_v1_2026-10-20';S=R/'experiments/wbuart_equiv_structure_v1_2026-10-20';O=R/'experiments/wbuart_equivalence_coverage_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);proof=json.loads((P/'verification.json').read_text());protocol=json.loads((P/'protocol.json').read_text());assert proof['equivalence_proven'] and not proof['timeout']
 for n,h in proof['bindings'].items():assert sha(P/n)==h
 for n,h in protocol['bindings'].items():assert sha(Path(n))==h
 prefix=protocol['commands'][:protocol['commands'].index('equiv_simple -undef -seq 2')];assert (S/'commands.ys').read_text().splitlines()==prefix+['write_json '+str(S/'before.json')]
 m=json.loads((S/'before.json').read_text())['modules']['equiv'];clock=m['ports']['i_clk']['bits'];states={s:set() for s in ['gold','gate']};pairs=[];init={};seqtypes=collections.Counter()
 for n,c in m['cells'].items():
  if 'dff' in c['type'].lower():
   side='gold' if n.endswith('_gold') else 'gate' if n.endswith('_gate') else None;assert side
   con=c['connections'];assert con['CLK']==clock and int(c['parameters']['CLK_POLARITY'],2)==1
   assert not states[side]&set(con['Q']);states[side].update(con['Q']);seqtypes[side+':'+c['type']]+=len(con['Q'])
  if c['type']=='$equiv':
   con=c['connections'];assert all(len(con[p])==1 for p in ['A','B','Y']);pairs.append(tuple(con[p][0] for p in ['A','B','Y']))
 for n,v in m['netnames'].items():
  if 'init' not in v.get('attributes',{}):continue
  for b,x in zip(v['bits'],reversed(v['attributes']['init'])):
   if x!='x':assert b not in init or init[b]==x;init[b]=x
 assert len(states['gold'])==601 and len(states['gate'])==598 and len(pairs)==602
 gatepairs=[p for p in pairs if p[1] in states['gate']];assert len(gatepairs)==598 and len({b for a,b,y in gatepairs})==598 and all(a in states['gold'] for a,b,y in gatepairs)
 init_value=lambda b:init.get(b,b if isinstance(b,str) else 'x')
 assert all(init_value(a)==init_value(b) for a,b,y in gatepairs)
 omitted=states['gold']-{a for a,b,y in pairs};assert len(omitted)==2
 omitted_rows=[]
 for b in omitted:
  uses=[(n,p) for n,c in m['cells'].items() for p,bits in c['connections'].items() if c['port_directions'][p]=='input' and b in bits];assert not uses
  assert not any(b in p['bits'] for p in m['ports'].values() if p['direction']=='output')
  omitted_rows.append({'bit':b,'aliases':[n for n,v in m['netnames'].items() if b in v['bits']],'cell_input_uses':uses})
 folded=[p for p in pairs if p[0] in states['gold'] and p[1] not in states['gate']];assert len(folded)==1 and folded[0][1]=='0';a,b,y=folded[0];assert init_value(a)=='x'
 folded_row={'gold_bit':a,'gate_value':b,'gold_initial_value':'unconstrained','aliases':[n for n,v in m['netnames'].items() if a in v['bits']]};assert 'o_wb_data[31]_gold' in folded_row['aliases']
 outputs={b for p in m['ports'].values() if p['direction']=='output' for b in p['bits']};assert len(outputs)==40 and outputs<={y for a,b,y in pairs}
 text=(P/'proof.log').read_text();assert 'Of those cells 602 are proven and 0 are unproven.' in text and 'force def on 1199 initial reg values and 44 inputs' in text
 d={'status':'ALL_GATE_STATE_AND_OUTPUT_PROPERTIES_COVERED_WITH_EXPLICIT_INITIAL_REFINEMENT_LIMIT','properties':602,'gold_state_bits':601,'gate_state_bits':598,'gate_state_properties':598,'public_output_bits':40,'matched_state_initial_constraints_equal':True,'omitted_gold_state':omitted_rows,'folded_gold_state':folded_row,'single_positive_clock':'i_clk','sequential_types':dict(seqtypes),'intrinsic_proof_domain':'Yosys undef-aware equivalence. Induction log forces definedness on 1199 initial register values and 44 input bits; no explicit reset constraints were added. Not full four-state or initial-time case equality.','strict_initial_four_state_equivalence':False,'strict_unseen_certified':False,'physical_input_admitted':False,'next':'Certify separately stated sampled/startup Boolean contract before physical benchmark input admission; inspect pending lineage scan.','bindings':{str(p):sha(p) for p in [Path(__file__),P/'verification.json',P/'protocol.json',P/'proof.log',S/'commands.ys',S/'before.json',S/'build.log']}}
 (O/'verification.json').write_text(json.dumps(d,indent=2)+'\n');print(d['status'])
if __name__=='__main__':main()
