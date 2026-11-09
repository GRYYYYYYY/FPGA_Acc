"""Check source four-state expression against all actual pre-edge observations."""
import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_tag_access_error_trace_v1_2026-10-09';f=D/'trace_audit.json';p=E/'full_tag_override_operands_trace_v1_2026-10-09/trace_audit.json';a=json.loads(f.read_text());b=json.loads(p.read_text());assert a['replay_fidelity'] and b['replay_fidelity']
def land(x,y):
 if '0' in [x,y]:return '0'
 return '1' if x==y=='1' else 'x'
def lor(x,y):
 if '1' in [x,y]:return '1'
 return '0' if x==y=='0' else 'x'
def inv(x):return {'0':'1','1':'0'}.get(x,'x')
records=[]
for r,parent in zip(a['rows'],b['rows']):
 assert r['cycle']==parent['cycle']
 bypass=land(land(inv(r['stageB_request_wr']),r['io_mem_rsp_valid']),r['io_mem_rsp_payload_error'])
 cached=lor(land(r['stageB_waysHits'],r['stageB_tagsReadRsp_0_error']),land(r['stageB_loadStoreFault'],inv(r['stageB_mmuRsp_isPaging'])))
 result=bypass if r['stageB_bypassCache']=='1' else cached
 assert result==parent['io_cpu_writeBack_accessError']
 records.append({'cycle':r['cycle'],'branch':'bypass' if r['stageB_bypassCache']=='1' else 'cached','bypass_value':bypass,'cached_value':cached,'observed_accessError':result})
assert len(records)==512 and all(r['cached_value']=='x' and r['branch']=='cached' and r['observed_accessError']=='x' for r in records)
out={'matched_expression_rows':512,'branch_counts':dict(collections.Counter(r['branch'] for r in records)),'observed_bypass_selector_counts':dict(collections.Counter(r['stageB_bypassCache'] for r in a['rows'])),'records':records,'conclusion':'Unread source tag error plus unknown hit produce cached accessErrorX all512 observations; procedural bypass selector0/X selects cached branch; fault contribution0 throughout.','constant_initialization_correction':'Original source stageB_wayInvalidate is X cycles0/1 then0; proc optimized constant0 does not prove original initial0.','scope':'Actual source expression path and frozen observations. Native upstream equivalence and complete42370 external mismatch attribution remain unproved.','hashes':{str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [f,p,D/'reference.v']}}
(D/'observed_path_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['records','hashes']},indent=2))
