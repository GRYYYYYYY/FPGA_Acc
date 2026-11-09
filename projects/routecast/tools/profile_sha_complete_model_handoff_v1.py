"""Fresh full model/handoff profile and original independent complete audits."""
import json,subprocess,sys,pstats
from pathlib import Path
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_complete_model_handoff_profile_v1_2026-10-10';assert not D.exists();D.mkdir();ep=R/'experiments/sha1_expat_topology_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';producer=R/'tools/run_sha1_actual_old_linear_undo_native_handoff_v1.py';auditor=R/'tools/run_shared_actual_old_linear_direct_lattice_audits_v4.py';bindings=closure([Path(__file__).resolve(),producer,auditor]);bindings[str(ep)]=sha(ep);commands=[[sys.executable,'-m','cProfile','-o',str(D/'profile.pstats'),str(producer),'sha1',str(ep),str(D/'handoff'),str(D/'native'),str(D/'model')],[sys.executable,str(auditor),str(D/'model'),'sha1']];(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,scope='Fresh full6273-query/two-round model, original selector/serialization, fresh independent full physical/event audits. Frozen development SHA input only for profile; profiler overhead and no native/canonical stages, not complete workflow/heldout/hardware gain.'),indent=2)+'\n');codes=[]
for i,cmd in enumerate(commands):
 with (D/f'stage{i}.log').open('w') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 codes.append(code)
 if code:break
out=dict(exit_codes=codes,scope='Full model/handoff diagnostic profiling; no complete native workflow gain.')
if codes==[0,0]:
 for p in [D/'handoff/receipt.json',D/'model/shared_audit_receipt.json']:
  v=json.loads(p.read_text())
  for section in ['bindings','files']:
   assert all(sha(k)==h for k,h in v.get(section,{}).items())
  bindings[str(p)]=sha(p)
 assert v['all_three_complete_audits_pass'] and v['fresh_independent_graph_context'];out['full_audits_pass']=True
 stats=pstats.Stats(str(D/'profile.pstats'));rows=[]
 for key,(primitive,total,selftime,cumulative,callers) in stats.stats.items():rows.append(dict(file=key[0],line=key[1],function=key[2],primitive_calls=primitive,total_calls=total,self_seconds=selftime,cumulative_seconds=cumulative))
 rows.sort(key=lambda x:x['cumulative_seconds'],reverse=True);(D/'function_costs.json').write_text(json.dumps(dict(total_calls=stats.total_calls,total_self_seconds=stats.total_tt,functions=rows,scope='All profiler functions retained; nested cumulative time not additive, no unprofiled speed measurement.'),indent=2)+'\n');bindings[str(D/'function_costs.json')]=sha(D/'function_costs.json');bindings[str(D/'profile.pstats')]=sha(D/'profile.pstats')
assert all(sha(k)==h for k,h in bindings.items());out['bindings']=bindings;(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'}))
