"""Label-dependent final-owner payloads, never deployable forecast inputs."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from evaluate_prince_ready_owner_forecast_v1 import final_owners
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_final_other_oracle_inputs_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);canonicalp=E/'prince_native_canonical_v1_2026-10-20/receipt.json';canonical=json.loads(canonicalp.read_text());design=E/'prince_ready_owner_forecast_v1_2026-10-20/final_other_owner_mechanism_diagnostic_design_v1.json';bindings={str(p):sha(p) for p in [Path(__file__),canonicalp,design]};rows=[]
 for w in [96,128,160]:
  for ep in range(1,4):
   case=f'w{w:03d}/episode_{ep:02d}'
   if w==96:rows.append(dict(case=case,available=False,reason='No canonical legal final ownership label; no oracle mode job'));continue
   tick=time.perf_counter();source=E/'prince_native_cohort_v1_2026-10-20'/case;receipt=source/'receipt.json';v=json.loads(receipt.read_text());assert v['native_full_check_pass'];c=next(x for x in canonical['results'] if x['case']==case);assert c['semantic_consistency_gate_pass'] and c['original_zero_counter_gate_pass'];route=source/'output.route';assert sha(route)==v['files'][str(route)];owners=final_owners(route);resources=E/'prince_quality_domains_v1_2026-10-20'/f'w{w:03d}'/'resources.jsonl';domain={x['id'] for x in map(json.loads,resources.open())};assignment={}
   for net,nodes in owners.items():
    for node in nodes:assert node in domain and node not in assignment;assignment[node]=net+1
   ref=E/'prince_ownership_ledger_trial_v2_2026-10-20'/case/'capture';ids=(ref/'identity.txt').read_text().splitlines();resolved=(ref/'callback.tsv.resolved.sha256').read_text().strip();import struct
   rr=ref/'boundary/iteration_1.bin';nrr=struct.unpack_from('<Q',rr.read_bytes(),16)[0];mappingp=E/'prince_resident_consumer_v1_2026-10-20'/case/'NET_mapping.json';mapping=json.loads(mappingp.read_text());out=D/(case.replace('/','_')+'.oracle.txt');out.write_text('\n'.join(['LABEL_DEPENDENT_FINAL_OTHER_V1',ids[0],ids[1],ids[2],case,ids[6],resolved,f'{len(mapping)} {nrr} {len(domain)}',*[f'{n} {assignment.get(n,0)}' for n in sorted(domain)]])+'\n');rows.append(dict(case=case,available=True,payload=str(out),sha256=sha(out),oracle_generation_native_seconds=v['native_seconds'],prepare_seconds=time.perf_counter()-tick,occupied_CHANNELs=len(assignment),scope='Known cost subtotal excludes historical RTL/pack/place and verification; no fullpaid speed claim.'))
   for p in [receipt,route,resources,ref/'identity.txt',ref/'callback.tsv.resolved.sha256',rr,mappingp]:bindings[str(p)]=sha(p)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'manifest.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Final legal labels deliberately used for mechanism diagnosis, not forecast evaluation or deployable speedup.'),indent=2)+'\n');print('LABEL_ORACLE_INPUTS',sum(x['available'] for x in rows),'available of9')
if __name__=='__main__':main()
