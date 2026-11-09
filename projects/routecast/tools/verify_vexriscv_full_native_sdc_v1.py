"""Independent native SDC load evidence and structurally unused input reconciliation."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'vexriscv_full_native_sdc_v1_2026-10-09';D=E/'vexriscv_full_native_sdc_verification_v1_2026-10-09';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();receipt=json.loads((B/'receipt.json').read_text());assert receipt['exit_code']==0
for p,h in {**receipt['bindings'],**receipt['files']}.items():assert sha(p)==h
p=E/'vexriscv_family_flattened_inventory_v1_2026-10-09/VexRiscvFull/design.json';m=json.loads(p.read_text())['modules']['VexRiscvFull'];used={b for c in m['cells'].values() for port,bits in c['connections'].items() if c['port_directions'][port]=='input' for b in bits}|{b for port in m['ports'].values() if port['direction']=='output' for b in port['bits']};unused=[];scalarunused=set()
for name,port in m['ports'].items():
 if port['direction']!='input':continue
 for i,bit in enumerate(port['bits']):
  if bit not in used:unused.append(dict(port=name,index=i,bit=bit))
 if len(port['bits'])==1 and port['bits'][0] not in used:scalarunused.add(name)
log=(B/'native.log').read_text();assert 'Applied 5 SDC commands' in log and "Constrained Clock 'clk'" in log;assert 'Setting default timing constraints' not in log and 'Exiting before packing as requested' in log
assert 'Starting Clustering' not in log
swept=int(re.search(r'Swept input\(s\)\s*:\s*(\d+)',log)[1]);assert swept==len(unused)==3
unmatched=re.findall(r"get_ports target name or pattern '([^']+)' matched no ports",log);assert len(unmatched)==2 and set(unmatched)==scalarunused=={'dBus_rsp_payload_last'}
D.mkdir(exist_ok=False);report=dict(bindings={str(x):sha(x) for x in (Path(__file__).resolve(),B/'receipt.json',B/'native.log',B/'development.sdc',p)},native_applied_commands=5,clock_domain='clk',unused_inputs=unused,native_swept_input_count=swept,unmatched_patterns=unmatched,scope='Actual SDC parser/load/domain and unmatched-pattern reconciliation against source structural unused inputs. No exported atom-pin identity/full timing coverage, routing STA, product deadline or prediction admission.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native5commands, clk and three unused inputs; no clustering')
