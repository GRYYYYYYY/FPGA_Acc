"""Complete frozen-family accounting with stage-specific compatibility, including pending and failed inputs."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_family_flattened_inventory_v1_2026-10-09';D=E/'vexriscv_family_input_readiness_v2_2026-10-09';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
proof=E/'vexriscv_family_flattened_verification_v1_2026-10-09/verification.json';authority=json.loads(proof.read_text());assert authority['members']==32
for p,h in authority['bindings'].items():assert sha(p)==h
receipt=json.loads((B/'receipt.json').read_text())
for p,h in {**receipt['bindings'],**receipt['files']}.items():assert sha(p)==h
assert len(receipt['members'])==32
plan=json.loads((B/'protocol.json').read_text())
for p,h in plan['bindings'].items():assert sha(p)==h
snapshot=(B/'progress.json').read_bytes();(D/'progress_snapshot.json').write_bytes(snapshot);assert json.loads(snapshot)==receipt['members'];completed={r['member']:r for r in json.loads(snapshot)};rows=[];bindings={str(proof):sha(proof),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__),str(B/'protocol.json'):sha(B/'protocol.json'),str(D/'progress_snapshot.json'):sha(D/'progress_snapshot.json')};supported={'$_MUX_','$_NOT_','$_AND_','$_OR_','$_XOR_','$_DFF_P_','$_DFF_N_','$_DFF_PP0_','$_DFF_PP1_'}
for member in plan['members']:
 name=Path(member['archived_path']).stem;row=dict(member=name,prediction_admitted=False)
 if name not in completed:row.update(status='PENDING_IN_SNAPSHOT');rows.append(row);continue
 prior=completed[name]
 if prior['exit_code']!=0:
  log=B/name/'log.txt';bindings[str(log)]=sha(log);row.update(status='FAILED_FRONTEND',exit_code=prior['exit_code'],errors=[s for s in log.read_text().splitlines() if 'ERROR:' in s]);rows.append(row);continue
 p=B/name/'design.json';h=sha(p);modules=json.loads(p.read_text())['modules'];assert len(modules)==1;m=modules[prior['top']];cells=m['cells'];census=Counter(c['type'] for c in cells.values());assert dict(census)==prior['hierarchical_cell_types'];assert sha(p)==h;bindings[str(p)]=h
 undefined=Counter(str(bit) for c in cells.values() for bits in c['connections'].values() for bit in bits if type(bit)!=int and bit not in ('0','1'));inout={n:len(p['bits']) for n,p in m['ports'].items() if p['direction']=='inout'};initial={}
 for net in m['netnames'].values():
  init=net.get('attributes',{}).get('init')
  if init is None:continue
  assert len(init)==len(net['bits'])
  for bit,state in zip(net['bits'],init[::-1]):
   if state=='x':continue
   if bit in initial:assert initial[bit]==state
   initial[bit]=state
 asyncinit=[n for n,c in cells.items() if c['type'] in ('$_DFF_PP0_','$_DFF_PP1_') and c['connections']['Q'][0] in initial];reasons=[]
 if inout:reasons.append('BIDIRECTIONAL_LOWERING_REQUIRED')
 if undefined:reasons.append('UNDEFINED_PIN_SEMANTICS_REQUIRED')
 if set(census)-supported:reasons.append('UNSUPPORTED_PRIMITIVE_TYPES')
 if asyncinit:reasons.append('ASYNC_DEFINED_INIT_ENCODING_REQUIRED')
 row.update(status='SYNTHESIZED_SNAPSHOT',boolean_cut_type_and_value_compatible=not reasons,conversion_obligations=reasons,inout_ports=inout,undefined_pin_counts=dict(undefined),unsupported_types=sorted(set(census)-supported),negative_edge_ff=census['$_DFF_N_'],defined_init_bits=len(initial),async_defined_init_cells=asyncinit,remaining_prediction_gates=['complete mapped/reconstructed native input and independent proof','architecture timing contract','family provenance/exposure split','frozen prediction/label experiment protocol']);rows.append(row);print(name,row['boolean_cut_type_and_value_compatible'],reasons,flush=True)
assert len(rows)==32;(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,status_counts=dict(Counter(r['status'] for r in rows)),scope='All32 terminal accounting after independent full-family verification. Compatible is only type/value/port screening, not exporter correctness, native acceptance, unseen-family claim or completed prediction assessment.'),indent=2)+'\n');print('complete32 snapshot readiness inventory',flush=True)
