"""Native delayed bank address/payload registers and real export instances."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_pending_write_registers_v1_2026-10-09';D.mkdir(exist_ok=True)
N=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';V=R/'experiments/full_ibus_bank_history_preedge_trace_v1_2026-10-09/design.v';m=max(json.loads(N.read_text())['modules'].values(),key=lambda x:len(x['cells']));v=V.read_text()
pa=m['netnames']['IBusCachedPlugin_cache.banks_0.s0.pa']['bits'];assert pa==m['netnames']['IBusCachedPlugin_cache.banks_0.s1.pa']['bits'];pd=m['netnames']['IBusCachedPlugin_cache.banks_0.s0.pd']['bits']+m['netnames']['IBusCachedPlugin_cache.banks_0.s1.pd']['bits'][:12];wa=m['netnames']['IBusCachedPlugin_cache.banks_0.WA']['bits'];data=m['ports']['iBus_rsp_payload_data']['bits'];records=[]
for kind,qs,ds in [('address',pa,wa),('data',pd,data)]:
 for lane,(q,d) in enumerate(zip(qs,ds)):
  c=next(c for c in m['cells'].values() if c['connections'].get('Q')==[q]);assert c['type']=='$_DFF_P_' and c['connections']=={'C':[254],'D':[d],'Q':[q]}
  match=re.search(r"DFF #\(\s*\.INITIAL_VALUE\(1'bx\)\s*\) \\latch_b"+str(q)+r'\s*\(\s*\.D\(\\latch_b'+str(q)+r'_input_0_0 \),\s*\.Q\(\\latch_b'+str(q)+r'_output_0_0 \),\s*\.clk\(\\latch_b'+str(q)+r'_clock_0_0 \)\s*\);',v);assert match,q
  routes={}
  for target in ['input','clock']:
   dest='\\latch_b'+str(q)+'_'+target+'_0_0';rm=re.search(r'\.datain\(([^)]+)\),\s*\.dataout\('+re.escape(dest)+r' \)',v);assert rm;routes[target]=rm[1].strip()
  assert routes['clock']=='\\clk_output_0_0'
  records.append({'kind':kind,'lane':lane,'Q':q,'D':d,'export_initial':'x','routes':routes,'register':c})
assert len(records)==42
out={'records':records,'native_write_address_bits':wa,'scope':'Actual42 native/export unreset/uninitialized pending address10/data32 registers, commonclk routes. Native dataD exactly sharedtop32input; addressD exactly actualWA. Data/inputroute source names retained; dynamic address history and macrocommit/rawarray remain unproved.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [N,V]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS42actualpendingaddress/dataregisters')
