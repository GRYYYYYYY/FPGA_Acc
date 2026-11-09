"""Actual exported32 one-bit bank macro write pins and primitive commit semantics."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_bank_macro_commit_v1_2026-10-09';D.mkdir(exist_ok=True)
P=R/'experiments/full_ibus_bank_history_preedge_trace_v1_2026-10-09';V=P/'design.v';F=P/'primitives.v';N=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';A=R/'experiments/full_ibus_bank_unknown_hold_v1_2026-10-09/audit.json';v=V.read_text();m=max(json.loads(N.read_text())['modules'].values(),key=lambda x:len(x['cells']));a=json.loads(A.read_text());pa=m['netnames']['IBusCachedPlugin_cache.banks_0.s0.pa']['bits'];pd=m['netnames']['IBusCachedPlugin_cache.banks_0.s0.pd']['bits']+m['netnames']['IBusCachedPlugin_cache.banks_0.s1.pd']['bits'][:12];records=[]
def route(term):
 rm=re.search(r'\.datain\(([^)]+)\),\s*\.dataout\('+re.escape(term)+r' \)',v);assert rm,term;return rm[1].strip()
for r in a['records']:
 raw=next(x for x in r['routes_lsb_first'] if x.startswith('\\dual_port_ram_'));name=raw.removesuffix('_output_1_0');match=re.search(r'\\dual_port_ram\s+#\(\s*\.ADDR_WIDTH\(10\),\s*\.DATA_WIDTH\(1\)\s*\) '+re.escape(name)+r'\s*\((.*?)\n\s*\);',v,re.S);assert match,name;body=match[1]
 addr=re.search(r'\.addr1\(\{([^}]+)\}',body);terms=[t.strip() for t in addr[1].split(',')][::-1];assert [route(t) for t in terms]==['\\latch_b'+str(b)+'_output_0_0' for b in pa]
 pins={p:route(re.search(r'\.'+p+r'\(([^)]+)\)',body)[1].strip()) for p in ['clock','data1','data2','we1','we2']}
 assert pins['clock']=='\\clk_output_0_0' and pins['data1']=='\\latch_b'+str(pd[r['lane']])+'_output_0_0' and pins['we1']=='\\latch_b2691_output_0_0'
 assert pins['we2']==pins['data2']=='\\lut_const0_output_0_0';records.append({'lane':r['lane'],'instance':name,'addr1_sources':pa,'pins':pins,'raw_visible_output':raw})
assert re.search(r"LUT_K #\(\s*\.K\(5\),\s*\.LUT_MASK\(32'b0+\)\s*\) \\lut_const0",v)
f=F.read_text();prim=f[f.index('module dual_port_ram #('):];prim=prim[:prim.index('endmodule')];assert 'Mem[addr1] = data1;' in prim and 'if(we1)' in prim and 'always@(posedge clock)' in prim and 'initial' not in prim
out={'records':records,'primitive':prim,'scope':'All32 actual visible bank macros commit on commonclock using old pendingpw/pa/pd, second writeport disabled and arrays uninitialized. Primitive uses blocking write and two separate always blocks: crossport read/write collision scheduling remains separate; no actual native memory-content trace/equivalence asserted.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [V,F,N,A]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS32actualbankmacrocommitpinbindings')
