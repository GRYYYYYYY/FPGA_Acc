"""Reconstruct selected union ledger and endpoints independently of importer."""
import json,re
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
from stream_native_route_audit import audit
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_selected_state_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json') and p['source_sha256']==sha(ROOT/'tools/trial_bitonic_selected_state.py');cold=ROOT/'experiments/bitonic_swapped_cold_2026-10-07/verification.json';assert sha(cold)==p['cold_verification_sha256'];refs=json.loads(cold.read_text())['rows'];rows=[]
for row,ref in zip(r['rows'],refs):
 n=row['count'];assert n==ref['count'];assert all(sha(f)==d for f,d in row['files'].items());work=out/f'n{n}';ep=json.loads((work/'endpoints.json').read_text());ledger=json.loads((work/'ledger.json').read_text());names={v:int(k) for k,v in ep['net_names'].items()};unions=defaultdict(set);ends=[];name=None;source=None
 for line in (work/'design.route').read_text().splitlines():
  m=NET.match(line)
  if m:name=m[2];source=None
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);unions[names[name]].add(node)
  if m[2]=='SOURCE':source=node
  elif m[2]=='SINK':ends.append((name,source,node))
 expected=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);assert Counter(ends)==expected
 actual={str(k):sorted(v) for k,v in unions.items() if v};assert actual==ledger['unions'];occupancy={str(k):v for k,v in Counter(x for nodes in unions.values() for x in nodes).items()};assert occupancy==ledger['node_occupancy'];assert ledger['records']==len(ends)==ref['connections']
 graph=Path(row['command'][row['command'].index('--read_rr_graph')+1]);a=audit(graph,work/'design.route');assert a['node_occupancy']==occupancy and not a['overflow_units'];text=(work/'selected.log').read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;assert not any(int(y) for x in re.findall(r'Found (\d+) mismatches|Fixed (\d+) routing traces',text) for y in x if y)
 assert F(row['cpd_ns'])<=F(ref['cold_cpd_ns']) and row['wirelength']<=ref['cold_wirelength'];assert row['selection']==('candidate' if ref['joint_nonregression'] else 'cold');rows.append(dict(count=n,selection=row['selection'],connections=len(ends),zero_fixup_FULL_STA=True,independent_endpoint_union_ledger=True,cpd_ns=row['cpd_ns'],wirelength=row['wirelength']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope=p['scope']),indent=2)+'\n');print(rows)
