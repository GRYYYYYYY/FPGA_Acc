"""Exact actual BLIF access-allow to CSR capture dependency and binary formula."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];f=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';text=f.read_text();nodes={}
for match in re.finditer(r'^\.names ([^\n]+)\n([^.]*)',text,re.M):
 ns=match[1].split();rows=[r.split() for r in match[2].splitlines() if r.strip() and not r.startswith('#')];nodes[ns[-1]]={'inputs':ns[:-1],'rows':rows}
assert nodes['new_n5366']['inputs']==['new_n5374','new_n5324','new_n5367']
assert nodes['new_n5937']['inputs']==['new_n5324','new_n5366','new_n5375','new_n5938','new_n5940']
def evaluate(node,values):
 t=nodes[node];bs=[values[n] for n in t['inputs']];polarity=int(t['rows'][0][1]);assert all(int(r[1])==polarity for r in t['rows']);hit=any(all(p=='-' or int(p)==b for p,b in zip(pattern,bs)) for pattern,_ in t['rows']);return polarity if hit else 1-polarity
witnesses=[];checked=0
for a,b,allow,c,d,e in itertools.product([0,1],repeat=6):
 values={'new_n5324':a,'new_n5374':b,'new_n5367':allow,'new_n5375':c,'new_n5938':d,'new_n5940':e};values['new_n5366']=evaluate('new_n5366',values);actual=evaluate('new_n5937',values)
 expected=int((a or not allow or b) and not c and d and e);assert actual==expected
 flipped=dict(values);flipped['new_n5367']=1-allow;flipped['new_n5366']=evaluate('new_n5366',flipped);opposite=evaluate('new_n5937',flipped)
 if actual!=opposite:witnesses.append({'inputs':values,'capture':actual,'capture_with_allow_inverted':opposite})
 checked+=1
assert witnesses
out={'checked_binary_rows':checked,'actual_nodes':{n:nodes[n] for n in ['new_n5367','new_n5366','new_n5937']},'capture_formula':'(new_n5324 || !new_n5367 || new_n5374) && !new_n5375 && new_n5938 && new_n5940','sensitivity_witnesses':witnesses,'conclusion':'Actual native access-allow new_n5367 feeds new_n5366 then CSR capture new_n5937; it is not a disconnected unknown. Capture sensitivity exists at explicit binary boundary assignments.','scope':'Actual BLIF local dependency/formula, not observed values of every capture operand or reachable binary history. Under a=b=c=0,d=e=1 an unknown allow produces unknown capture by binary-completion consensus; actual fulltrace operand premise not yet observed.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest()}}
D=R/'experiments/full_csr_capture_access_dependency_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checked':checked,'sensitivity_witnesses':len(witnesses),'formula':out['capture_formula']}))
