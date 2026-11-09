"""Independent source epoch payload and physical identity reconstruction."""
import json,struct,sys
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 root=R/'experiments/mmc_source_context_inputs_v1_2026-10-18';receipt=json.loads((root/'receipt.json').read_text());assert all(sha(k)==h for k,h in receipt['bindings'].items());base={**receipt['bindings'],**closure([Path(__file__)]),str(root/'receipt.json'):sha(root/'receipt.json')};cases=[]
 for entry in receipt['cases']:
  proof=Path(entry['proof']);assert sha(proof)==entry['proof_sha256'];p=json.loads(proof.read_text());assert p['schema']=='ROUTECAST_SOURCE_CONTEXT_INPUT_V1' and all(sha(k)==h for k,h in p['bindings'].items());bindings={**base,**p['bindings'],str(proof):sha(proof)};v=json.loads(Path(p['source_dense_verification']).read_text());assert v['all_physical_pin_global_NET_local_identity_and_RR_endpoints_equal'];owner=json.loads(Path(p['source_owner_verification']).read_text());assert owner['NETs']==55300;assert all(sha(k)==h for k,h in {**v['bindings'],**owner['bindings']}.items());actual={}
  with Path(p['source_history_snapshot']).open('rb') as f:
   for line in f:
    x=line.split(b'\t')
    if x[0]!=b'N':continue
    node=int(x[1]);value=struct.unpack('<f',struct.pack('<I',int(x[4])))[0];assert value.is_integer() and value>=1
    if value>1:actual[str(node)]=int(value-1)
  history=json.loads(Path(p['history_file']).read_text());assert history==actual and len(history)==p['history_nonzero_entries']==109404;dense={x['connection_id']:x for x in json.loads(Path(p['source_criticalities']).read_text())};old={x['connection_id']:x for x in json.loads(Path(p['identity_carrier']).read_text())};rows=json.loads(Path(p['post_STA_criticality_file']).read_text());ep=json.loads(Path(p['endpoint']).read_text());queries={q['connection_id']:q for q in ep['connections']};assert ep['graph_sha256']==p['graph_sha256'];seen=set();mutable={'criticality','criticality_numerator','criticality_denominator','criticality_float32_text'}
  for row in rows:
   cid=row['connection_id'];assert cid not in seen;seen.add(cid);d=dense[cid];o=old[cid];q=queries[cid];assert row.keys()==o.keys() and all(row[k]==o[k] for k in row if k not in mutable);assert (row['net'],row['source_rr'],row['target_rr'])==(q['net_id'],q['source'],q['sink']);assert row['local_sink_pin']==d['local_sink_pin'] and row['global_pin']==d['global_pin'];bits=d['criticality_float32_bits'];value=struct.unpack('<f',struct.pack('<I',bits))[0];assert Fraction(row['criticality_numerator'],row['criticality_denominator'])==Fraction(value);assert struct.pack('<f',row['criticality'])==struct.pack('<I',bits) and row['criticality_float32_text']==d['criticality_float32_text']
  assert seen==dense.keys()==old.keys()==queries.keys() and len(seen)==115572;assert p['model_present_factor']==1 and p['native_source_present_factor_observed']==v['native_price_present_factor'];assert all(sha(k)==h for k,h in bindings.items());out=proof.parent/'independent_verification_v1.json';out.write_text(json.dumps(dict(status='source_history_and_post_STA_payload_and_all115572_target_physical_identities_verified',bindings=bindings,connections=len(seen),inherited_history_entries=len(history),only_criticality_payload_changed=True,history_exact_native_multiplier_minus1=True,model_present_factor_unchanged=True,scope='Source timing prior remapped to target physical identities; no target STA or label selection. Native present-factor not transferred.'),indent=2));cases.append(dict(case=entry['case'],verification=str(out),sha256=sha(out)));print('SOURCE_INPUT_VERIFIED',entry['case'],flush=True)
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all3_source_context_input_payloads_independently_verified',bindings={**base,**{r['verification']:r['sha256'] for r in cases}},cases=cases),f,indent=2)
if __name__=='__main__':main()
