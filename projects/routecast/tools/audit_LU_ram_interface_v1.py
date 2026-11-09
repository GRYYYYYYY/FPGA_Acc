"""Exact local RAM caller/library interface evidence; no behavioral repair."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow';lp=S/'primitives.v';library=lp.read_text();a=library.index('module dual_port_ram');b=library.index('endmodule',a)+len('endmodule');body=library[a:b];assert re.search(r'if\(we2\)\s*begin\s*Mem\[addr2\]\s*=\s*data2',body);bindings={str(lp):sha(lp),str(Path(__file__)):sha(Path(__file__))};rows=[]
for name in ['LU32PEEng','LU64PEEng','LU8PEEng']:
 p=S/'benchmarks/verilog'/(name+'.v');text=p.read_text();bindings[str(p)]=sha(p);masked=re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:' '*len(m[0]),text,flags=re.S);instances=[]
 for m in re.finditer(r'\bdual_port_ram\s+(\w+)\s*\((.*?)\);',masked,re.S):
  ports={n:v.strip() for n,v in re.findall(r'\.(\w+)\s*\(([^()]*)\)',m[2])};assert 'we1' in ports and 'we2' in ports
  raw=text[m.start():m.end()];instances.append(dict(instance=m[1],line=text.count('\n',0,m.start())+1,ports=ports,raw_instance=raw,we2_is_literal_zero=bool(re.fullmatch(r"(?:1'b0|1'd0|0)",ports['we2'])),rdreq_connected_to_write_enable=ports['we2']=='rdreq'))
 assert instances;rows.append(dict(name=name,instances=instances,nonzero_we2_count=sum(not x['we2_is_literal_zero'] for x in instances),rdreq_as_we2_count=sum(x['rdreq_connected_to_write_enable'] for x in instances)))
assert all(sha(k)==h for k,h in bindings.items());D=R/'experiments/LU_ram_interface_audit_v1_2026-10-10';D.mkdir();(D/'audit.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,library_module=body,native_semantic_admitted=False,scope='Named-port lexical instance connections and exact behavioral write clause. Caller Read-enable comments differ from library we2 write semantics. Does not prove reachable corruption, intended original hard-block contract, FIFO correctness, same-address collision freedom or source-to-synth equivalence. No HDL edits/port rewiring/blackboxing.'),indent=2)+'\n');print([(r['name'],len(r['instances']),r['rdreq_as_we2_count']) for r in rows])
