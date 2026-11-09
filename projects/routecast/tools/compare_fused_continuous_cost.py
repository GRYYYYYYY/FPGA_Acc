"""Whole-cohort verified current lifecycle versus archived original/cold windows."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];names={'certified':'gf2_fused_continuous_two_updates_2026-10-06','original':'gf2_continuous_two_updates_v2_2026-10-06','cold':'gf2_cold_two_updates_2026-10-06'};receipts={};bindings={}
for k,name in names.items():
 base=root/'experiments'/name;v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');r=json.loads((base/'receipt.json').read_text());assert r['all_cases_retained'] and len(r['rows'])==3;receipts[k]=r;bindings[str(base/'receipt.json')]=sha(base/'receipt.json')
rows=[]
for c in receipts['certified']['rows']:
 w=c['width'];o=next(x for x in receipts['original']['rows'] if x['width']==w);b=next(x for x in receipts['cold']['rows'] if x['width']==w);assert c['complete'] and o['complete'] and b['complete']
 for i in [1,2]:
  a=root/'experiments'/names['certified']/f'gf2_d{w}_accepted{i}.json';old=root/'experiments'/names['original']/f'gf2_d{w}_accepted{i}.json';assert sha(a)==c['rounds'][i-1]['snapshot_sha256'] and sha(old)==o['rounds'][i-1]['snapshot_sha256'];assert json.loads(a.read_text())==json.loads(old.read_text())
 row={'width':w,'certified_case_wall_s':c['case_wall_s'],'archived_original_case_wall_s':o['case_wall_s'],'archived_cold_case_wall_s':b['case_wall_s'],'certified_over_original':c['case_wall_s']/o['case_wall_s'],'certified_over_cold':c['case_wall_s']/b['case_wall_s'],'all_two_snapshots_exact':True};rows.append(row);print(row,flush=True)
out=root/'experiments'/names['certified']/'cost_comparison.json';out.write_text(json.dumps({'bindings':bindings,'source_sha256':sha(Path(__file__)),'rows':rows,'scope':'Current certified lifecycle single run vs archived serial runs, not paired statistical speedup. Same original selected states, cold policy selection differs. Includes measured context/stage/native tails/audits/certificateissue/selection/advance; excludes initialnativegeneration/commonfrontends/sandboxassembly/outerverifier. No from-design or production gain.'},indent=2)+'\n')
