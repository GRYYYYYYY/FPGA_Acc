"""Independent sorted-rank/heap selection semantics and captured event counts."""
import hashlib,itertools,json,math,sys
from array import array
from pathlib import Path
from verify_mmc_pressure_risk_v2_2026_10_18 import rank_info
from verify_anchored_outcomes_v1_2026_10_18 import calc,assert_metrics

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(info):
 assert sha(info['path'])==info['sha256'];a=array(info.get('typecode','d'));a.frombytes(Path(info['path']).read_bytes());assert len(a)==info['values'] and all(math.isfinite(x) and x>=0 for x in a)
 if 'byteorder' in info:assert info['byteorder']==sys.byteorder
 return a

def main():
 root=Path('experiments/mmc_NET_pressure_quality_v1_2026-10-18');rp=root/'results.json';r=json.loads(rp.read_text());assert r['status']=='all540_NET_diagnostic_cells_computed_independent_metrics_pending';source=Path('experiments/mmc_NET_pressure_exposure_v1_2026-10-18');target=Path('experiments/mmc_NET_pressure_targets_v1_2026-10-18');plan=json.loads((source/'protocol.json').read_text());domains=json.loads((source/'NET_domains.json').read_text());sm=json.loads((source/'vector_manifest.json').read_text());tm=json.loads((target/'vector_manifest.json').read_text());out=Path('experiments/mmc_NET_pressure_quality_verification_v1_2026-10-18');out.mkdir(exist_ok=False)
 bindings={**r['bindings'],str(rp.resolve()):sha(rp),str(Path(__file__).resolve()):sha(__file__)}
 for name in ['tools/verify_mmc_pressure_risk_v2_2026_10_18.py','tools/verify_anchored_outcomes_v1_2026_10_18.py']:bindings[str(Path(name).resolve())]=sha(name)
 for p,h in bindings.items():assert sha(p)==h
 rows=r['rows'];assert len(rows)==540 and {(x['case'],x['policy'],x['target'],x['source'],x['method']) for x in rows}==set(itertools.product(plan['cases'],plan['policies'],plan['targets'],plan['sources'],plan['methods']))
 summaries=[]
 for case in plan['cases']:
  ids=domains[case]['NET_ids'];assert ids==sorted(set(ids)) and len(ids)==55300;k=len(ids)//20;vectors={};stats={}
  for row in rows:
   if row['case']!=case:continue
   pref=case+'__'+row['source']+'__'+row['method'];tref=case+'__'+row['policy']+'__'+row['target'];assert row['prediction_vector']==pref and row['truth_vector']==tref
   for ref,manifest in [(pref,sm),(tref,tm)]:
    if ref not in vectors:vectors[ref]=read(manifest[ref]);assert len(vectors[ref])==len(ids);stats[ref]=rank_info(vectors[ref],k)
   pred,truth=vectors[pref],vectors[tref];expected=calc(pred,truth,k,stats[pref],stats[tref]);assert_metrics(row['metrics'],expected)
   total=sum(truth);selected=sum(truth[i] for i in stats[pref]['selected']);capture=selected/total if total else None;enrichment=capture*len(ids)/k if capture is not None else None
   assert row['total_target_count']==total and row['selected_target_count']==selected and row['target_count_capture_fraction']==capture
   if enrichment is None:assert row['enrichment_over_uniform_selection'] is None
   else:assert abs(row['enrichment_over_uniform_selection']-enrichment)<1e-12
  summaries.append(dict(case=case,cells=180));print('INDEPENDENT NET QUALITY PASS',case,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,cells_verified=540,scope='Complete NET domain, full sorted doubled-integer average ranks, deterministic selection and both tie intervals, independent selected-target counts/capture/enrichment. Observational exposed-trace diagnostics; not independent-family, causal, per-NET heap or native utility evidence.'),f,indent=2)
if __name__=='__main__':main()
