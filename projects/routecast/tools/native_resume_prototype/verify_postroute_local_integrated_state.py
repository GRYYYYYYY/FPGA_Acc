"""Independent original RR edge/NET-owner capacity and native transaction closure."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
seq=R/'experiments/native_resume_postroute_local_integrated_adder_2026-10-07';ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json';graph,digest,nodes,f,rc,qs=load_endpoints(ep);arcs={(u,f['dest_ranks'][s],f['switch_ids'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};rows=[];bindings={str(Path(__file__)):sha(__file__)}
build=R/'build/native_route_transaction_post_route_v5_2026-10-07';bp=json.loads((build/'protocol.json').read_text());br=json.loads((build/'receipt.json').read_text());assert br['binary_sha256']==sha(build/'routecast_transaction_vpr') and br['protocol_sha256']==sha(build/'protocol.json') and br['private_archive_sha256']==sha(build/'libvpr.a');assert bp['hook_sha256']==sha(R/'tools/native_route_transaction/hook_post_route_v5.cpp') and bp['api_sha256']==sha(build/'source/vpr_api.cpp');assert all(sha(p)==h for p,h in bp['inputs'].items());bindings.update(bp['inputs'])
for i in (1,2,3):
 ep=R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json';meta=json.loads(ep.read_text());assert meta['graph_sha256']==digest and all(sha(v['path'])==v['sha256'] for v in meta['inputs'].values());expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in meta['connections']);bindings[str(ep)]=sha(ep)
 for mode in ('workflow','cold'):
  b=R/f'experiments/native_resume_postroute_local_integrated_adder_step{i}_{mode}_2026-10-07';final=b/'canonical';paths=physical_paths(final/'design.route');assert Counter((n,p[0][0],p[-1][0]) for n,ps in paths.items() for p in ps)==expected;occ=Counter()
  for name,ps in paths.items():
   union=set()
   for p in ps:
    assert all((u,v,sw) in arcs for (u,_),(v,sw) in zip(p,p[1:]));union.update(u for u,_ in p)
   occ.update(union)
  assert all(v<=f['capacities'][n] for n,v in occ.items());bindings[str(final/'design.route')]=sha(final/'design.route')
  if mode=='workflow':
   w=b/'first';status=json.loads((w/'tx.attempt0.json').read_text());assert status==dict(committed=True,mutation_started=True,epoch_before=0,epoch_after=1,error='')
   binding=json.loads((w/'live.binding.json').read_text());assert binding['epoch']==0 and binding['graph']=='SHA256:'+digest and binding['export_route']=='SHA256:'+sha(w/'live.route') and binding['identity']=='SHA256:'+sha(w/'live.identity.jsonl')
   norm=lambda p:{n:Counter(ps) for n,ps in physical_paths(p).items() if ps}
   assert norm(w/'live.route')==norm(w/'live.parent.route');
   producer=json.loads((w/'live.search/receipt.json').read_text());assert all(sha(p)==h for p,h in producer['inputs'].items());bindings.update(producer['inputs']);
   receipt=json.loads((b/'receipt.json').read_text());first=next(stage['native'] for stage in receipt['stages'] if stage['stage']=='first');assert '--route' in first['command'] and '--analysis' not in first['command'];
   assert norm(w/'candidate.route')==norm(w/'tx.attempt0.after.route')==norm(final/'design.route')
   for p in (w/'tx.attempt0.json',w/'live.binding.json',w/'candidate.route',w/'live.route',w/'live.identity.jsonl'):bindings[str(p)]=sha(p)
  rows.append(dict(index=i,mode=mode,endpoints=len(meta['connections']),all_arcs_valid=True,zero_owner_capacity_overflow=True,live_commit_verified=mode=='workflow'))
(seq/'state_verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Original RR XML independently loaded, final routes all endpoints/arcs/unique NET owner capacity. Workflow live parent physical paths and generated candidate equals committed and normalized routes; three serial post-route epoch0→1 commits. No persistent native epoch claim.'),indent=2)+'\n');print('PASS',len(rows))
