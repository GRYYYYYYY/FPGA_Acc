"""Post-outcome failed-iteration resource alignment, not legal-route truth."""
import json,re,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from prepared_csr import read
from stream_native_route_audit import audit
from pooled_channel_pressure import KEYS


def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_failed_pressure_alignment_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('diagnose_cw32_failed_pressure_alignment.py','stream_native_route_audit.py','audit_native_route.py','prepared_csr.py','pre_route_endpoints.py','pooled_channel_pressure.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 variants={'independent':'multiplier_cw32_pressure_trial_2026-10-06','pooled':'multiplier_cw32_pooled_pressure_trial_2026-10-06','corridor':'multiplier_cw32_corridor_pressure_trial_2026-10-06'};protocol={'variants':variants,'cohort':[f'mult_{w}x{w}' for w in range(6,10)],'runs':'first off and first on only, all failed cases','sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Post-outcome final failed iteration occupancy diagnostics; not a legal completed route or predictor calibration/holdout. Raw-channel and fixed pool alignment only.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[]
 pattern=re.compile(r'^\s*\d+\s+(\d+)\s+(\d+)\s+(\d+)\s+(SOURCE|SINK|IPIN|OPIN|CHANX|CHANY)\s+',re.M)
 for name in protocol['cohort']:
  front=root/'experiments/multiplier_family_endpoints_cw32_2026-10-06'/name;fp=json.loads((front/'protocol.json').read_text());graph=fp['inputs']['rr_graph'];m,f=read(root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',graph['sha256']);pool=lambda n:tuple(f[k][n] for k in KEYS)
  for variant,folder in variants.items():
   base=root/'experiments'/folder/name;case=json.loads((base/'receipt.json').read_text());payload=base/'candidate.pressure';pressure={int(line.split()[0]) for line in payload.read_text().splitlines()[1:]};pressure_pools={pool(n) for n in pressure}
   for mode in ('off','on'):
    row=next(r for r in case['rows'] if r['mode']==mode);assert not row['success'];tag=f"{row['run']:02d}_{mode}";log=base/(tag+'.log');assert sha(log)==row['log_sha256'];text=log.read_text();matches=pattern.findall(text);native={int(n):(int(occ),int(cap),kind) for n,occ,cap,kind in matches};assert len(native)==row['final_overused_nodes'];route=root/'work'/folder/name/tag/'design.route';assert sha(route)==row['route_sha256'];physical=audit(graph['path'],route);occupancy={int(n):v for n,v in physical['node_occupancy'].items()};reconstructed={n:(occ,int(f['capacities'][n])) for n,occ in occupancy.items() if occ>f['capacities'][n]};assert set(reconstructed)==set(native)
    for n,(occ,cap,kind) in native.items():assert reconstructed[n]==(occ,cap)
    channels={n for n,(_,_,kind) in native.items() if kind in ('CHANX','CHANY')};channel_pools={pool(n) for n in channels};result={'design':name,'variant':variant,'mode':mode,'native_overused_nodes':len(native),'native_overused_types':dict(Counter(kind for occ,cap,kind in native.values())),'native_channel_overused_nodes':len(channels),'pressure_rows':len(pressure),'raw_channel_hits':len(channels&pressure),'raw_channel_recall':len(channels&pressure)/len(channels) if channels else None,'raw_channel_precision':len(channels&pressure)/len(pressure) if pressure else None,'native_overused_channel_pools':len(channel_pools),'pressure_pools':len(pressure_pools),'pool_hits':len(channel_pools&pressure_pools),'pool_recall':len(channel_pools&pressure_pools)/len(channel_pools) if channel_pools else None,'failed_route_and_final_log_occupancy_exact':True,'log_sha256':sha(log),'route_sha256':sha(route),'pressure_sha256':sha(payload),'case_receipt_sha256':sha(base/'receipt.json')};dest=out/f'{name}_{variant}_{mode}';dest.mkdir();(dest/'physical_failed_attempt.json').write_text(json.dumps(physical)+'\n');(dest/'native_overused.json').write_text(json.dumps(native,indent=2)+'\n');reports.append(result);print(json.dumps({k:result[k] for k in ('design','variant','mode','native_channel_overused_nodes','raw_channel_hits','pool_hits','native_overused_channel_pools')}),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
