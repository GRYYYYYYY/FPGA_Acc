"""Validate actual native LUT values against direct pre-edge state observations."""
import json,itertools,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_native_tag_access_path_trace_v1_2026-10-09';f=D/'trace_audit.json';pf=E/'full_tag_override_operands_trace_v1_2026-10-09/trace_audit.json';a=json.loads(f.read_text());p=json.loads(pf.read_text());assert a['replay_fidelity'] and p['replay_fidelity']
def evaluate(mask,values,positions):
 values=[['0','1'] if v in 'xz' else [v] for v in values]
 answers={mask[-1-sum(int(v)<<lane for v,lane in zip(row,positions))] for row in itertools.product(*values)}
 return next(iter(answers)) if len(answers)==1 else 'x'
rows=[]
for r,parent in zip(a['rows'],p['rows']):
 assert r['cycle']==parent['cycle']
 cached=evaluate('00000000000000010000000100000001',[r['hit'],r['tag_error'],r['fault']],[4,3,2])
 allow=evaluate('00000000000100000001000100010000',[r['bypass_error'],r['bypass'],r['cached_allow']],[4,3,2])
 assert cached==r['cached_allow'],('cached',r,cached)
 assert allow==r['access_allow'],('selector',r,allow)
 assert allow==parent['allow_input0'],('route',r,parent)
 rows.append({'cycle':r['cycle'],'cached_allow':cached,'access_allow':allow,'source_accessError':parent['io_cpu_writeBack_accessError']})
assert len(rows)==512
out={'matched_cached_lut_rows':512,'matched_selector_lut_rows':512,'matched_allow_route_rows':512,'first_native_rows':a['rows'][:6],'native_state_counts':{k:dict(collections.Counter(r[k] for r in a['rows'])) for k in ['tag_error','hit','fault','bypass','cached_allow','bypass_error','access_allow']},'scope':'Actual binary-completion LUT evaluation over observed native nodes and validated parent route input; not source/native Boolean proof or closed initialization/global history theorem. X-consensus evaluation expected to match actual primitives; failure is retained rather than treated as admission.','functional_admission':False,'hashes':{str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [f,pf,D/'cached_allow_lut_audit.json']}}
(D/'observed_path_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['first_native_rows','native_state_counts','functional_admission']},indent=2))
