"""Every original node subtree, CSR element, RC class/increment and refreshed query verified."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints as original
from owned_static_rr_context_v1 import load_endpoints as candidate,diagnostics
R=Path(__file__).resolve().parents[1];ep=R/'experiments/sha1_compact_json_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';D=R/'experiments/owned_static_rr_context_full_sha_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(x):sha(x) for x in [Path(__file__).resolve(),R/'tools/owned_static_rr_context_v1.py',ep]};times={};tick=time.perf_counter();a=original(ep);times['original']=time.perf_counter()-tick;tick=time.perf_counter();b=candidate(ep);times['candidate_cold']=time.perf_counter()-tick
assert a[:2]==b[:2];assert len(a[2])==len(b[2]);tree=lambda x:(x.tag,tuple(x.attrib.items()),x.text,x.tail,tuple(tree(c) for c in x))
assert all(tree(x)==tree(y) for x,y in zip(a[2],b[2]));assert a[3].keys()==b[3].keys() and all(bytes(a[3][k])==bytes(b[3][k]) for k in a[3]);assert a[4].scale==b[4].scale and tuple(a[4].increments)==b[4].increments and all(a[4].initial(n)==b[4].initial(n) for n in range(len(a[2])));assert tuple(a[4].rc.classes)==b[4].rc.classes and a[4].rc.switches==b[4].rc.switches and tuple(a[4].rc.node_classes)==b[4].rc.node_classes;assert a[5]==b[5]
modified=json.loads(ep.read_text());modified['connections']=list(reversed(modified['connections']));p=D/'reordered_current_endpoints.json';p.write_text(json.dumps(modified)+'\n');tick=time.perf_counter();c=candidate(p);times['candidate_reaccess']=time.perf_counter()-tick;assert c[5]==modified['connections'] and c[5]!=b[5] and all(x is y for x,y in zip(b[:5],c[:5]));assert diagnostics()['loads']==1 and diagnostics()['accesses']==2
rejected=0
for mutate in [lambda:b[3]['capacities'].__setitem__(0,0),lambda:b[2][0].attrib.__setitem__('type','BAD'),lambda:setattr(b[2][0],'tag','BAD')]:
 try:mutate()
 except (TypeError,AttributeError):rejected+=1
assert rejected==3
bad=json.loads(ep.read_text());bad['graph_sha256']='0'*64;pbad=D/'wrong_digest_endpoints.json';pbad.write_text(json.dumps(bad)+'\n')
try:candidate(pbad)
except AssertionError:pass
else:raise AssertionError('digest mismatch accepted')
for p in [p,pbad]:bindings[str(p)]=sha(p)
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,node_count=len(a[2]),edge_count=len(a[3]['edge_ids']),every_node_subtree_CSR_RC_increment_initial_class_switch_exact=True,current_queries_refreshed=True,static_payload_mutations_rejected=rejected,digest_mismatch_rejected=True,diagnostics=diagnostics(),reader_seconds=times,scope='Full same SHA graph static context and queryrefresh component contract only. Reordered complete query list is loader test, not a placement transaction. No dynamic model/audit reuse, native/workflow/family/hardware claim.'),indent=2)+'\n');print('FULL STATIC CONTEXT PARITY',times,diagnostics())
