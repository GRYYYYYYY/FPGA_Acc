"""Independent v1 frontier import, callback receipts and v2 frontier coverage."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];OLD=R/'experiments/mmc_A_only_joint_CBS_v1_2026-10-21';D=R/'experiments/mmc_A_only_joint_CBS_resume_v2_2026-10-21';P=D/'verification.json';A=D/'independent_verification_v1.json';v=json.loads(P.read_text());a=json.loads(A.read_text());ov=json.loads((OLD/'verification.json').read_text());assert all(sha(p)==h for p,h in a['bindings'].items());assert all(sha(p)==h for k in ['bindings','files'] for p,h in v[k].items());bindings={str(p):sha(p) for p in [P,A,OLD/'verification.json',Path(__file__)]};rows=[]
def key(m):return tuple((int(n),tuple(sorted(rs))) for n,rs in sorted(m.items(),key=lambda x:int(x[0])) if rs)
def norm(st):return {'masks':{int(n):set(rs) for n,rs in st['masks'].items()},'trees':{int(n):p for n,p in st['trees'].items()}}
def check_checkpoint(cp,states,registry,conflicts,assessed,serial):
 assert cp['serial']==serial and {tuple((int(n),tuple(rs)) for n,rs in k) for k in cp['seen']}==set(registry)
 assert set(map(int,cp['states']))==set(states)
 for sid,st in states.items():assert norm(cp['states'][str(sid)])==st
 expected_frontier=set(states)-assessed;assert set(cp['frontier'])==expected_frontier and len(cp['frontier'])==len(expected_frontier)
 pending=[]
 for sid,conflict in conflicts:
  remaining=[]
  for net,node in sorted(set(map(tuple,conflict))):
   cm={n:set(rs) for n,rs in states[sid]['masks'].items()};assert node not in cm.get(net,set());cm.setdefault(net,set()).add(node)
   if key(cm) not in registry:remaining.append([net,node])
  if remaining:pending.append({'state':sid,'remaining':remaining})
 assert cp['pending']==pending
for row in v['rows']:
 case=row['case'];prior=next(r for r in ov['rows'] if r['case']==case);initial={int(p.stem.split('_')[-1]):str(p) for p in (OLD/case).glob('initial_NET_*.json')};states={0:{'masks':{},'trees':initial}};registry={key({}):0};assessed=set();conflicts=[];serial=0
 def child(e,path):
  global serial
  sid,parent=e['state'],e['parent'];net,node=e['forbidden'];assert parent in states;pm=states[parent]['masks'];cm={n:set(rs) for n,rs in pm.items()};assert node not in cm.get(net,set());cm.setdefault(net,set()).add(node);k=key(cm);assert k not in registry;registry[k]=sid;serial=max(serial,sid);r=json.loads(Path(path).read_text());assert r['net_id']==net and r['extra_forbidden']==sorted(cm[net]) and e['pruned']==(not r['all_connections_within_budget'])
  if not e['pruned']:
   ct=dict(states[parent]['trees']);ct[net]=str(path);states[sid]={'masks':cm,'trees':ct}
 for e in prior['events']:
  serial=max(serial,e['state'])
  if 'parent' in e:child(e,OLD/case/('query_%03d_NET_%d'%(e['state'],e['forbidden'][0]))/'result.json')
  else:assert e['state'] in states;assessed.add(e['state']);conflicts.append((e['state'],e['conflict']))
 imported_path=D/case/'imported_checkpoint.json';imported=json.loads(imported_path.read_text());check_checkpoint(imported,states,registry,conflicts,assessed,serial);initial_serial=serial;requests=json.loads((D/case/'route_requests.json').read_text());assert len(requests)==row['queries'];available={str(p) for p in (OLD/case).glob('query_*/result.json')};request_index=0;assessment_index=0;cache_hits=0;new_raw=0
 for e in row['events']:
  if 'parent' not in e:
   sid=e['state'];assert sid in states and sid not in assessed,(case,sid,'membership',sid in states,sid in assessed);assessment_index+=1;st=json.loads((D/case/('assessment_%03d.json'%assessment_index)).read_text());assert {int(n):p for n,p in st['trees'].items()}==states[sid]['trees'] and e['conflict']==st['conflict'][len(st['conflict'])-len(e['conflict']):],(case,sid,'assessment_match',st['conflict'],e['conflict']);assessed.add(sid);conflicts.append((sid,st['conflict']));continue
  req=requests[request_index];request_index+=1;assert req['request']==request_index and e['state']==initial_serial+request_index and req['net_id']==e['forbidden'][0];path=req['result'];doc=json.loads(Path(path).read_text());assert req['extra_forbidden']==doc['extra_forbidden']
  if req['reused']:assert path in available;cache_hits+=1
  else:assert path not in available and str(D) in path;available.add(path);new_raw+=1
  child(e,path)
 assert request_index==len(requests) and cache_hits==row['cache_hits'] and new_raw==row['new_raw_searches']
 if row['status']=='FEASIBLE':
  st=json.loads((D/case/('assessment_%03d.json'%row['last_assessment'])).read_text());assert row['last_assessment']==assessment_index+1 and st['full_CHANNEL_capacity_feasible'];trees={int(n):p for n,p in st['trees'].items()};masks={int(n):set(rs) for n,rs in row['masks'].items()};assert any(s['trees']==trees and s['masks']==masks for s in states.values());assert json.loads((D/case/'checkpoint.json').read_text()) is None
 else:
  cp=json.loads((D/case/'checkpoint.json').read_text());check_checkpoint(cp,states,registry,conflicts,assessed,serial)
 rows.append({'case':case,'imported_frontier_states':len(imported['frontier']),'imported_unfinished_parent_states':len(imported['pending']),'new_assessments':row['expanded'],'route_requests':len(requests),'new_raw_searches':new_raw,'exact_cache_hits':cache_hits,'import_and_continuation_no_branch_loss_verified':True,'producer_event_conflict_aliasing_reconstructed_from_frozen_assessments':True,'status':row['status']})
assert all(sha(p)==h for p,h in bindings.items());out={'status':'A_ONLY_FRONTIER_IMPORT_QUERY_REUSE_AND_CONTINUATION_BRANCH_COVERAGE_VERIFIED','rows':rows,'bindings':bindings,'event_log_erratum':'Producer v2 events conflict list shares mutable pending list and stores only an unprocessed suffix after pops. Complete conflict disjunction is independently recovered from frozen assessment files, tree identity and masks are reconstructed and checked; these physical assessments and queries are unaffected. Original module and receipts preserved; future v3 module copies the event list.', 'scope':'Exact preserved input domain, all recorded old/new query receipts and monotone branch/frontier bookkeeping. Functional capacity/budget proofs inherited from independent original XML audit. Not all3 quality, native/canonical or matched gain.'};(D/'continuation_trace_verification_v2.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
