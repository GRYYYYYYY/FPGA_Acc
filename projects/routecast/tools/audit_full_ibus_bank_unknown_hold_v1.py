"""Actual visible-bank export LUTs propagate heldX when read-enableX."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_bank_unknown_hold_v1_2026-10-09';D.mkdir(exist_ok=True)
P=R/'experiments/full_ibus_bank_history_preedge_trace_v1_2026-10-09';V=P/'design.v';v=V.read_text();N=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';m=max(json.loads(N.read_text())['modules'].values(),key=lambda x:len(x['cells']))
qs=m['netnames']['IBusCachedPlugin_cache.fetchStage_read_banksValue_0_data']['bits'];held=m['netnames']['IBusCachedPlugin_cache.banks_0.s0.held']['bits']+m['netnames']['IBusCachedPlugin_cache.banks_0.s1.held']['bits'][:12];records=[]
for lane,(q,h) in enumerate(zip(qs,held)):
 match=re.search(r"LUT_K #\(\s*\.K\((\d+)\),\s*\.LUT_MASK\((\d+)'b([01]+)\)\s*\) \\lut_b"+str(q)+r'\s*\(\s*\.in\(\{([^}]+)\}\),\s*\.out\(\\lut_b'+str(q)+r'_output_0_0 \)\s*\);',v);assert match,q
 k=int(match[1]);mask=match[3];routes=[]
 for term in reversed([t.strip() for t in match[4].split(',')]):
  if term in ["1'b0","1'b1"]:routes.append(term);continue
  rm=re.search(r'\.datain\(([^)]+)\),\s*\.dataout\('+re.escape(term)+r' \)',v);assert rm,(q,term);routes.append(rm[1].strip())
 hi=routes.index('\\latch_b'+str(h)+'_output_0_0');ei=routes.index('\\latch_b2693_output_0_0');checks=0
 for bits in itertools.product([0,1],repeat=k):
  if any(r.startswith("1'b") and bits[i]!=int(r[-1]) for i,r in enumerate(routes)):continue
  if bits[ei]!=0:continue
  assert mask[-1-sum(b<<i for i,b in enumerate(bits))]==str(bits[hi]);checks+=1
 records.append({'lane':lane,'Q':q,'held':h,'K':k,'mask':mask,'routes_lsb_first':routes,'hold_pin':hi,'er_pin':ei,'checked_er0_rows':checks})
a=json.loads((P/'trace_audit.json').read_text());assert len(records)==32
assert all(r['native_held']=='x'*32 and r['native_data']=='x'*32 for r in a['rows'])
cycles=[r['cycle'] for r in a['rows'] if r['native_er']=='x'];assert cycles==list(range(6,512))
out={'records':records,'observed_unknown_er_cycles':cycles,'conclusion':'All32 actual visible-bank LUTs select held when er0 for every other input assignment. With erX/heldX, completion includes held0 and held1 through er0, so consensus remainsX regardless raw/fwd/hit. Actual506cycles6..511 satisfy erX/heldX/dataX.','scope':'Actual export mask/routes and observations establish persistent visible unknown from held/read-enable path without assuming native raw contents. No raw-array write equivalence or full functional repair/admission.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [V,N,P/'trace_audit.json']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS32actualLUTs,506observedunknown-enablecycles')
