"""All3 post-routing packed-netlist canonical FULL/STA reload, original gates retained."""
import json,sys,time
from pathlib import Path
from types import SimpleNamespace
from class_cached_rc_endpoint_context_v1 import load_endpoints
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from shared_rr_inventory import SharedRRInventory
from canonical_reload_pin_index_v2 import canonical_reload,binary,identity
from source_binding_v2 import closure
from native_route_ledger_import_compact import physical_paths
from collections import Counter
E=R/'experiments';B=E/'adder_direct_from_inputs_checked_native_v6_2026-10-09';D=E/'adder_direct_from_inputs_checked_canonical_v6_2026-10-09';D.mkdir(exist_ok=False)
r=json.loads((B/'receipt.json').read_text());p=json.loads((B/'protocol.json').read_text());assert all(sha(f)==h for f,h in r['bindings'].items())
bindings={**r['bindings'],**closure([Path(__file__)]),str(B/'receipt.json'):sha(B/'receipt.json'),str(B/'protocol.json'):sha(B/'protocol.json'),str(binary):sha(binary),str(identity):sha(identity)}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='All3 fresh canonical reloading of postrouting packednet bytes, exact identity/site pin rebinding, original FULL/STA and original zero counters separately reported.'),indent=2)+'\n')
rows=[];inventory=None;start=time.perf_counter()
for plan,old in zip(p['plans'],r['rows']):
 ep=Path(plan['endpoints'])
 if inventory is None:
  graph,digest,nodes,fields,rc,q=load_endpoints(ep);inventory=SharedRRInventory(SimpleNamespace(graph=graph,digest=digest,n=len(nodes),fields=fields))
 src=B/f'step_{plan["step"]}';files={str(f):sha(f) for f in src.iterdir() if f.is_file()}
 inp=dict(width=300,decision='C',command=plan['command'],cpd_ns=float(old['cpd_ns']),files=files)
 row=canonical_reload(inp,src,D/f'step_{plan["step"]}',inventory)
 a=Counter((name,path) for name,paths in physical_paths(src/'output.route').items() for path in paths);b=Counter((name,path) for name,paths in physical_paths(D/f'step_{plan["step"]}/design.route').items() for path in paths);assert a==b
 row['step']=plan['step'];row['all516_named_paths_equal']=True;rows.append(row);bindings.update(row['files']);print(plan['step'],row['exit_code'],row['mismatches'],row['fixups'],row['cpd_ns'],flush=True)
assert all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Actual3 canonical packednet identity/FULL/STA reload; original zero counter gate separately preserved. Same physical paths and CPD as seeded native results, budget failures therefore unchanged. Not original HDL equivalence, all-modelbudget success or fullworkflow gain.'),indent=2)+'\n')
