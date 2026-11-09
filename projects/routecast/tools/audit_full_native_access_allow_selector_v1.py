"""Audit actual exported native access-allow selector and X witness."""
import re,json,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';f=E/'full_tag_access_error_trace_v1_2026-10-09/design.v';bf=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';nf=E/'full_native_ram_gates_v3_2026-10-09/gates.json';s=f.read_text();blif=bf.read_text();n=max(json.loads(nf.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})))
mask='00000000000100000001000100010000';assert mask in s
assert '.names new_n5371 new_n5369 b5 new_n5368\n-10 1\n0-1 1' in blif
aliases={b:[k for k,v in n['netnames'].items() if v['bits']==[b]] for b in [5,1926,1856]};assert 'dataCache_1.stageB_bypassCache' in aliases[5]
routes={}
for lane,net in [(4,'lut_new_n5371_output_0_0'),(3,'latch_b5_output_0_0'),(2,'lut_new_n5369_output_0_0')]:
 pattern=r'\.datain\(\\'+re.escape(net)+r' \),\s*\.dataout\(\\lut_new_n5368_input_0_'+str(lane)+r' \)';assert re.search(pattern,s);routes[lane]=net
for bypass_error,cached_allow,bypass in itertools.product([0,1],repeat=3):
 index=(bypass_error<<4)|(bypass<<3)|(cached_allow<<2);assert int(mask[-1-index])==int((not bypass and cached_allow) or (bypass and not bypass_error))
def consensus(a,b,c):
 outcomes={int(mask[-1-((x<<4)|(y<<3)|(z<<2))]) for x in ([0,1] if a=='x' else [int(a)]) for y in ([0,1] if b=='x' else [int(b)]) for z in ([0,1] if c=='x' else [int(c)])}
 return str(next(iter(outcomes))) if len(outcomes)==1 else 'x'
rows=[{'bypass_error':a,'bypass':b,'cached_allow':c,'allow':consensus(a,b,c)} for a,b,c in itertools.product('01x',repeat=3)]
assert consensus('0','0','x')==consensus('0','x','x')=='x'
D=E/'full_native_access_allow_selector_v1_2026-10-09';D.mkdir(exist_ok=True)
out={'mask':mask,'routes':routes,'aliases':aliases,'binary_function':'allow = (!bypass AND cached_allow) OR (bypass AND !bypass_error)','all8_binary_completions_verified':True,'ternary_completion_table':rows,'local_witness':'cached_allowX and bypass_error0 produce allowX when bypass0 orX.','scope':'Actual exported LUT/BLIF/port-order audit and local completion witness. Actual native tagerror/hit and cached_allow values are not yet directly observed; do not substitute source probes for native state equality or assert complete native upstream cause.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [f,bf,nf]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['binary_function','all8_binary_completions_verified','local_witness','scope']},indent=2))
