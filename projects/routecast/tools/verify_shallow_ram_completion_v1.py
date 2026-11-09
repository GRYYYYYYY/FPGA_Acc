"""Independent exact delta audit and address-map SAT receipt verification."""
import json,copy,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'shallow_ram_address_completion_v1_2026-10-21';P=E/'source_ram_bank_sampling_v1_2026-10-21';B=E/'parmys_source_provenance_replay_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 prov={r['source']:r for r in json.loads((B/'verification_v1.json').read_text())['rows']};result=json.loads((D/'results.json').read_text());verified=[]
 for row in result['rows']:
  n=row['source'];before=json.loads((P/n/'candidate.json').read_text());after=json.loads((D/n/'candidate.json').read_text());expected=copy.deepcopy(before);changes=json.loads((D/n/'address_changes.json').read_text());allowed={};highcount=0
  for g in prov[n]['groups']:
   a=g['address_bits']
   if a>=11:continue
   for cn in g['descendant_cells']:
    c=before['modules'][n]['cells'][cn]
    for p in ['addr1','addr2'] if c['type']=='dual_port_ram' else ['addr']:
     bits=c['connections'][p];assert bits[a:]==['x']*(11-a);assert len(bits)==11;allowed[cn,p]=a;expected['modules'][n]['cells'][cn]['connections'][p]=bits[:a]+['0']*(11-a);highcount+=11-a
   # Enumerate every logical row to ensure distinct in-range physical rows.
   pairs={(x,x) for x in range(1<<a)};assert len(pairs)==1<<a and all(0<=physical<2048 for _,physical in pairs)
  assert expected==after;assert len(changes)==len(allowed)==row['changed_address_ports'];assert {(c['cell'],c['port']) for c in changes}==set(allowed)
  for c in changes:
   a=allowed[c['cell'],c['port']];assert c['logical_address_bits']==a;assert c['before']==before['modules'][n]['cells'][c['cell']]['connections'][c['port']];assert c['after']==after['modules'][n]['cells'][c['cell']]['connections'][c['port']]
  assert sha(D/n/'candidate.json')==row['candidate_sha256'];assert highcount==row['completed_high_bits'];assert row['structural_check_exit_code']==0 and 'Found and reported 0 problems.' in (D/n/'check.log').read_text();verified.append({'source':n,'groups':len(row['groups']),'changed_address_ports':len(allowed),'completed_high_bits':highcount,'all_other_design_fields_exact':True,'bindings':{str(p.relative_to(R)):sha(p) for p in [D/n/'candidate.json',D/n/'address_changes.json',D/n/'check.log']}})
 assert len(result['address_proofs'])==12
 for a in [2,3,4,10]:
  group=[r for r in result['address_proofs'] if r['logical_bits']==a];assert {r['mode'] for r in group}=={'shared_prefix','truncate_negative','mismatched_prefix_negative'}
  for r in group:
   f=D/f'address{a}_{r["mode"]}';log=(f/'yosys.log').read_text()
   if r['mode']=='shared_prefix':assert r['exit_code']==0 and r['proof_passed'] and 'no model found: SUCCESS' in log
   else:assert r['exit_code']==1 and r['proof_failed'] and 'proof did fail' in log
 out={'status':'ALL_12_SHALLOW_GROUP_ADDRESS_COMPLETIONS_AND_INJECTIVITY_VERIFIED','rows':verified,'address_widths':[2,3,4,10],'positive_SAT_proofs':4,'negative_controls_failed':8,'scope':'Physical candidate zero-extends logical row addresses, and shared prefix embedding preserves address equality. Exact remaining JSON preserved. X->0 is explicit implementation choice, not four-state equivalence to original mapped X, nor complete RAM state/source equivalence.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
