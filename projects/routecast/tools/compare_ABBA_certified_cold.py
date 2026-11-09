"""Audited ABBA lifecycle costs versus fresh serial cold-only follow-up."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments/capture_lifecycle_ABBA_2026-10-06';cold=root/'experiments/gf2_certified_cold_two_updates_2026-10-06';a=json.loads((base/'verification.json').read_text());r=json.loads((cold/'receipt.json').read_text());v=json.loads((cold/'verification.json').read_text());assert a['receipt_sha256']==sha(base/'receipt.json') and v['receipt_sha256']==sha(cold/'receipt.json');assert r['all_cases_retained'] and len(r['rows'])==3;rows=[]
for x in a['rows']:
 c=next(y for y in r['rows'] if y['width']==x['width']);assert c['complete'] and c['error'] is None
 rows.append({'width':x['width'],'cold_case_s':c['case_wall_s'],'certified_mean_s':x['certified_mean_s'],'fused_mean_s':x['fused_mean_s'],'fused_over_cold':x['fused_mean_s']/c['case_wall_s'],'certified_over_cold':x['certified_mean_s']/c['case_wall_s'],'cold_certificate_issue_validate_s':sum(y['certificate_issue_validate_s'] for y in c['rounds'])})
result={'bindings':{str(base/'receipt.json'):sha(base/'receipt.json'),str(cold/'receipt.json'):sha(cold/'receipt.json')},'source_sha256':sha(Path(__file__)),'rows':rows,'scope':'ABBA means compared with subsequent single cold-only run; not interleaved three-policy statistical benchmark. Cold uses same current canonical certificate reuse as candidate pipelines; direct import differs from two-alternative quality selection. No baseline extra selected reload. All included/excluded lifecycle timing scopes retained; no full-design gain.'};(base/'certified_cold_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
