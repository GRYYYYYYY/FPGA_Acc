"""Complete continuous workflow vs fresh cold quality/time evidence."""
import json,re,sys
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_adder_transfer_2026-10-07/repair_verified';out.mkdir(exist_ok=False);rows=[];bindings={str(Path(__file__)):sha(Path(__file__))}
for w,i in ((32,3),):
 results=[]
 for mode in ('workflow','cold'):
  d=ROOT/f'experiments/native_resume_adder_pipeline_v2_step{i}_{mode}_2026-10-07';rp=d/'receipt.json';r=json.loads(rp.read_text());p=json.loads((d/'protocol.json').read_text());assert r['protocol_sha256']==sha(d/'protocol.json')
  for mapping in (r['files'],p['inputs'],p['sources'],r['canonical']['files']):assert all(sha(f)==h for f,h in mapping.items());bindings.update(mapping)
  c=r['canonical'];assert c['exit_code']==0 and c['fixups']==c['mismatches']==0 and F(str(c['cpd_ns']))==F(r['cpd_ns']);assert r['all_target_endpoints_match'] and r['physical_audit']['overflow_units']==0
  final=d/('exchange_canonical' if mode=='workflow' else 'canonical');log=(final/'reload.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;assert int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1])==r['wirelength']
  ps=physical_paths(final/'design.route');source=Path(r['selected_work'])/'output.route';norm=lambda paths:{n:Counter(v) for n,v in paths.items() if v};assert norm(ps)==norm(physical_paths(source));ep=ROOT/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json';meta=json.loads(ep.read_text());actual=Counter((name,path[0][0],path[-1][0]) for name,paths in ps.items() for path in paths);expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in meta['connections']);assert actual==expected
  if mode=='workflow':
   ex=json.loads((d/'exchange/receipt.json').read_text());assert ex['unchanged_floor_cache'] and len(ex['records'])==len(meta['connections']);assert all(sha(f)==h for f,h in ex['bindings'].items());bindings.update(ex['bindings']);assert {x['connection_id'] for x in ex['records']}=={x['connection_id'] for x in meta['connections']}
  assert sum(s['seconds'] for s in r['stages'])<=r['internal_seconds'];results.append(r);bindings[str(rp)]=sha(rp)
 a,b=results;quality=F(a['cpd_ns'])<=F(b['cpd_ns']) and a['wirelength']<=b['wirelength'];timewin=a['internal_seconds']<b['internal_seconds']
 rows.append(dict(width=w,index=i,connections=len(meta['connections']),cpd_pair=[a['cpd_ns'],b['cpd_ns']],wire_pair=[a['wirelength'],b['wirelength']],workflow_seconds=a['internal_seconds'],cold_seconds=b['internal_seconds'],ratio=a['internal_seconds']/b['internal_seconds'],joint_quality_pass=quality,time_win=timewin,complete_gain_pass=quality and timewin,workflow_stages=[dict(stage=s['stage'],seconds=s['seconds']) for s in a['stages']]))
assert all(sha(f)==h for f,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Fresh sequential single paired run per snapshot; continuous internal clock includes floor initialization, candidate generation/proof, shared-context exchange, serialization, native synchronization and final FULL/STA/resource/endpoint proof. Excludes imports, last receipt publication, prior mapping/seed/endpoint/graph generation and compilation; no heldout-family or controlled repeated-time conclusion.'),indent=2)+'\n');print(rows)
