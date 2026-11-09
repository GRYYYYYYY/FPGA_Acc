"""Exact same-run repair-event counts; repeated pairs are not state-cycle proof."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'experiments/mux_detour_score_online_loop_2026-10-06'
receipt=json.loads((p/'receipt.json').read_text());assert len(receipt['rows'])==12
rows=[];bindings={}
for r in receipt['rows']:
 if r['status']=='PRIOR_ALLOCATION_SKIP':continue
 f=p/f"w{r['width']}_m{r['index']}/result.json";assert sha(f)==r['result_sha256'];bindings[str(f)]=sha(f);d=json.loads(f.read_text())
 for j,t in enumerate(d['result']['trace']):
  c=t['candidate'];releases=[e for e in c.get('events',[]) if e['type']=='RELEASE'];pairs=[(e['failed_query']['connection_id'],tuple(e['blocker_NETs'])) for e in releases]
  assert len(releases)==c['repairs']
  rows.append(dict(case=f.parent.name,attempt=j,repairs=c['repairs'],release_events=len(releases),unique_failed_owner_pairs=len(set(pairs)),repeated_failed_owner_pairs=len(pairs)-len(set(pairs)),completed=c['completed_connections'],required=c['required_connections']))
(p/'repair_repetition_diagnosis.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),receipt_sha256=sha(p/'receipt.json'),bindings=bindings,rows=rows,scope='All searched cases, exact archived same-run repair-event counting only. Repeated query/owner pairs do not prove identical state or infinite cycles.'),indent=2)+'\n')
print('attempts',len(rows),'repair caps hit',sum(r['repairs']==32 for r in rows),'repeated pairs',sum(r['repeated_failed_owner_pairs'] for r in rows))
