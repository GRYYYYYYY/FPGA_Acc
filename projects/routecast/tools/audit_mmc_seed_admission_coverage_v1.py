"""Diagnose authenticated MMC v6 subset coverage and final router effort."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08';N=D/'seed/native/mmc';subset=N/'subset.json';receipt=N/'receipt.json';verification=D/'verification.json'
r=json.loads(receipt.read_text());assert r['files'][str(subset)]==sha(subset)
v=json.loads(verification.read_text());assert v['all_cases_both_complete_arms_authenticated']
for p,h in v['bindings'].items():assert sha(p)==h
s=json.loads(subset.read_text());records=s['records'];pending=s['pending'];required=v['cases'][0]['arms']['seed']['required'];ids={x['connection_id'] for x in records};assert len(ids)==len(records) and len(set(pending))==len(pending) and not ids.intersection(pending) and len(records)+len(pending)==required
admitted={x['net_id'] for x in s['decisions'] if x['admitted']};rejected={x['net_id'] for x in s['decisions'] if not x['admitted']};assert len(admitted)+len(rejected)==len(s['decisions']) and {x['net_id'] for x in records}==admitted
c,b=[v['cases'][0]['arms'][x] for x in ['cold','seed']]
out=dict(bindings={str(p):sha(p) for p in [subset,receipt,verification,Path(__file__)]},required_connections=required,seed_connections=len(records),pending_connections=len(pending),seed_connection_fraction=len(records)/required,admitted_nets=len(admitted),rejected_nets=len(rejected),admitted_net_fraction=len(admitted)/len(s['decisions']),native_iterations=dict(cold=c['iterations'],seed=b['iterations']),native_process_seconds=dict(cold=c['native_seconds'],seed=b['native_seconds']),decision='Whole-net capacity filtering discards over half the modeled connections; seeded exact routing has more iterations in this trial. Investigate selection and seed quality together with acquisition cost; coverage alone is not a gain metric.',scope='Authenticated single historical development trial. No causal attribution, route-work counter reconstruction, heldout behavior or complete optimization claim. Seed import feasibility does not imply exact-router savings.')
O=R/'experiments/mmc_seed_admission_coverage_v1_2026-10-09';O.mkdir(exist_ok=True);(O/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['bindings']},indent=2))
