"""Actual budgets and original-XML resource exclusion for surviving paths."""
import json
from fractions import Fraction as F
from pathlib import Path
from immutable_xml_prediction_audit import ImmutableXMLAudit
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_multiresource_reroute_2026-10-06';parent=ROOT/'experiments/mux_multiresource_budgets_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==12;rows=[];last=None
for case,row in zip(p['cases'],r['rows']):
 if row['status']=='ALLOCATION_NOT_SUBMITTED':continue
 w,i=row['width'],row['index'];af=parent/f'w{w}_m{i}.json';a=json.loads(af.read_text());pf=out/f'w{w}_m{i}/prediction.json';assert sha(pf)==row['prediction_sha256'];d=json.loads(pf.read_text());ep=json.loads(Path(case['target']).read_text())
 if last!=w:xml=ImmutableXMLAudit(ep['inputs']['graph']['path'],ep['graph_sha256']);last=w
 pair_bans={}
 for q in ep['connections']:
  if str(q['net_id']) in a['restrictions']:pair_bans.setdefault((q['source'],q['sink']),set()).update(a['restrictions'][str(q['net_id'])])
 checked=0;violations=[]
 update=json.loads((pf.parent/'update.json').read_text());initial=update['incremental'];expanded=set(a['expanded_connection_ids']);assert set(initial['affected']['affected_complete_net_connection_ids'])==expanded
 committed={e['query']['connection_id'] for e in initial['events'] if e['committed']};assert {r['connection_id'] for r in initial['records']}==({q['connection_id'] for q in ep['connections']}-expanded)|committed
 for rec in d['records']:
  cid=str(rec['connection_id']);delay=F(rec['answer']['delay']*10**9,d['scale']);limit=F(a['budgets_ns'][cid])
  if delay>limit:violations.append(dict(connection_id=int(cid),delay_ns=str(delay),limit_ns=str(limit)))
  if (rec['source'],rec['sink']) in pair_bans:
   used={rec['source']}
   for eid in rec['answer']['physical_edge_ids']:edge=xml.graph.edges[eid];used.add(edge.source);used.add(edge.sink)
   assert not pair_bans[rec['source'],rec['sink']].intersection(used);checked+=1
 calls=json.loads((pf.parent/'avoid_queries.json').read_text());assert calls['restrictions']==a['restrictions'] and calls['expanded_connection_ids']==sorted(expanded)
 for q in calls['calls']:assert q['forbidden']==sorted(pair_bans.get((q['source'],q['sink']),set()))
 rows.append(dict(width=w,index=i,surviving_paths=len(d['records']),restricted_paths_checked=checked,budget_violations=violations,query_calls=len(calls['calls']),allocation_sha256=sha(af),query_log_sha256=sha(pf.parent/'avoid_queries.json')))
(out/'avoidance_budget_verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),auditor_sha256=sha(Path(__file__)),rows=rows,scope='All surviving actual integer delays versus allocation; original XML path node exclusion for selected endpoint pairs. Partial paths do not prove full vector realization. Call log restriction flags checked; native physical verification is separate.'),indent=2)+'\n');print(rows)
