"""Full edgewise maxplus invariants and independent native critical-path identity."""
import json,re
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_full_arrival_transfer_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==12 and all(sha(p)==h for p,h in r['bindings'].items());details=ROOT/'experiments/mux_joint_candidate_details_2026-10-06';dr=json.loads((details/'receipt.json').read_text());rows=[]
for row in r['rows']:
 if row['status']!='FULL_FANIN_TRANSFER':continue
 w,i=row['width'],row['index'];file=out/f'w{w}_m{i}.json';assert sha(file)==row['sha256'];data=json.loads(file.read_text());tg=json.loads((ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json').read_text());a={int(n):Fraction(v)for n,v in data['arrival_seconds'].items()};changed={e:Fraction(v)for e,v in data['updated_external_edge_seconds'].items()};incoming=defaultdict(list)
 for eid,e in tg['edges'].items():
  if not e['disabled']:incoming[e['sink']].append((e['source'],changed.get(eid,Fraction(e['max_delay_seconds']))))
 for n in a:assert a[n]==(max(a[u]+delay for u,delay in incoming[n])if incoming[n]else Fraction(0))
 assert Fraction(data['predicted_cpd_ns'])==a[data['worst_sink_node']]*10**9;assert abs(row['predicted_cpd_ns']-row['native_candidate_cpd_ns'])<.00001
 table=ROOT/f'experiments/mux_atom_timing_identity_2026-10-06/w{w}/atom_identity.jsonl';identity={x['node_id']:(x['atom'],x['port'],x['bit'])for x in map(json.loads,table.read_text().splitlines())if x['node_id']is not None};path=data['worst_path_edge_ids'];nodes=[tg['edges'][path[0]]['source']]+[tg['edges'][eid]['sink']for eid in path];logical=[identity[n]for n in nodes];native=next(x for x in dr['rows']if x['width']==w and x['index']==i);work=Path(next(iter(native['reload']['files']))).parent;body=(work/'report_timing.setup.rpt').read_text().split('#Path 1\n')[1].split('#Path 2')[0];reported=[]
 for line in body.splitlines():
  m=re.match(r'^(\S+)\.(inpad|outpad|in|out)\[(\d+)\]\s+\(',line)
  if m:reported.append((m[1],m[2],int(m[3])))
 assert logical==reported;rows.append(dict(width=w,index=i,all_node_recurrences_verified=len(a),native_critical_path_exact_logical_identity=True,cpd_difference_ns=row['difference_ns']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Allnode maxplus invariant andnativecriticalpathidentity/CPD, fourfrozencompletecases; retrospective oldlocals hypothesis passes here, not movedpacking invariant or genericSTA replacement.'),indent=2)+'\n');print(rows)
