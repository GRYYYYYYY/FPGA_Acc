"""Explicit source-only inherited history and dense post-STA timing payloads."""
import json,struct,sys,time
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 start=time.perf_counter();E=R/'experiments';out=E/'mmc_source_context_inputs_v1_2026-10-18';out.mkdir(exist_ok=False);bindings=closure([Path(__file__)])
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p):
  d=load(p);assert all(sha(k)==h for k,h in d['bindings'].items());bindings.update(d['bindings']);return d
 spec=admit(E/'mmc_source_context_input_ablation_protocol_v1_2026-10-18/protocol.json');source=E/'mmc_dense_post_STA_source_v1_2026-10-18';dense=admit(source/'verification_v1.json');owners=admit(source/'per_NET_owner_verification_v1.json');assert dense['physical_connections']==115572 and owners['NETs']==55300;raw=load(source/'receipt.json');graph=Path(raw['bindings'].keys().__iter__().__next__()) if False else Path(json.loads((source/'protocol.json').read_text())['command'][json.loads((source/'protocol.json').read_text())['command'].index('--read_rr_graph')+1]);graphhash=sha(graph);bindings[str(graph)]=graphhash;values={x['connection_id']:x for x in load(source/'dense_physical_criticalities.json')};history={};count=0;context=source/'context.tsv'
 with context.open() as f:
  for line in f:
   x=line.split()
   if x[0]!='N':continue
   node=int(x[1]);value=struct.unpack('<f',struct.pack('<I',int(x[4])))[0];assert value>=1 and value.is_integer();count+=1
   if value>1:history[str(node)]=int(value)-1
 assert count==904438 and len(history)==109404;hp=out/'source_history.json';hp.write_text(json.dumps(history,sort_keys=True));bindings[str(hp)]=sha(hp);bindings[str(context)]=sha(context);cases=[]
 for case in ['case_01','case_02','case_03']:
  carrier_dir=E/f'mmc_multiplacement_feedback_inputs_v1_2026-10-18/{case}/timing';carrierproof=carrier_dir/'verification.json';cv=admit(carrierproof);assert cv['all_native_pin_identities_preserved'];carrier=carrier_dir/'remapped_criticalities.json';old=load(carrier);ep=Path(cv['after_endpoint']);endpoint=load(ep);assert endpoint['graph_sha256']==graphhash;queries={q['connection_id']:q for q in endpoint['connections']};assert len(old)==len(values)==len(queries)==115572;rows=[]
  for previous in old:
   cid=previous['connection_id'];s=values[cid];q=queries[cid];assert previous['local_sink_pin']==s['local_sink_pin'] and previous['global_pin']==s['global_pin'];assert (previous['net'],previous['source_rr'],previous['target_rr'])==(q['net_id'],q['source'],q['sink']);value=s['criticality'];assert struct.unpack('<I',struct.pack('<f',value))[0]==s['criticality_float32_bits'];f=Fraction(value);rows.append(dict(previous,criticality_float32_text=s['criticality_float32_text'],criticality=value,criticality_numerator=f.numerator,criticality_denominator=f.denominator))
  folder=out/case;folder.mkdir();payload=folder/'post_STA_criticalities.json';payload.write_text(json.dumps(rows));local={**bindings,str(payload):sha(payload),str(carrier):sha(carrier)};proof=dict(schema='ROUTECAST_SOURCE_CONTEXT_INPUT_V1',bindings=local,endpoint=str(ep),graph_sha256=graphhash,history_file=str(hp),post_STA_criticality_file=str(payload),identity_carrier=str(carrier),identity_carrier_proof=str(carrierproof),source_dense_verification=str(source/'verification_v1.json'),source_owner_verification=str(source/'per_NET_owner_verification_v1.json'),source_criticalities=str(source/'dense_physical_criticalities.json'),source_history_snapshot=str(context),source_iteration=21,history_nonzero_entries=len(history),connections=len(rows),model_present_factor=1,native_source_present_factor_observed=dense['native_price_present_factor'],scope='Prior original-placement source data. Target identities remapped only; no target STA, cold labels or native present-factor substitution. All original warm initial frames/budgets remain unchanged.');(folder/'verification.json').write_text(json.dumps(proof,indent=2));cases.append(dict(case=case,proof=str(folder/'verification.json'),proof_sha256=sha(folder/'verification.json')))
 assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,staging_process_seconds=time.perf_counter()-start,scope='Input extraction/staging paid; independent validation pending, no predictor executed.'),indent=2));print('SOURCE_CONTEXT_INPUTS_STAGED',len(history),flush=True)
if __name__=='__main__':main()
