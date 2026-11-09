import json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from canonical_reload_ignored_invariants_v1 import canonical_reload,binary,identity
from shared_compact_native_inventory_v1 import Inventory
out=R/'experiments/ultraembedded_mmc_cold_canonical_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(binary):sha(binary),str(identity):sha(identity)};rows=[]
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=['mmc'],scope='Original VPR objects semantic reload of both frozen candidate cold native routes, ignored-pin/packed-byte/physical-sequence/FULL checks. Original zero-counter gate separately retained. Experimental async timing remains synthetic, no original HDL/physical timing/heldout/netgain claim.'),indent=2)+'\n')
for name in ['mmc']:
 mode='cold';graph=R/'experiments/ultraembedded_mmc_rr_only_v1_2026-10-08'/name/'rr_graph.xml';inventory=Inventory(graph);bindings[str(graph)]=sha(graph)
 src=R/'experiments/ultraembedded_mmc_native_cold_v1_2026-10-08'/name;proof=src/'verification.json';v=json.loads(proof.read_text());assert v['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and all(sha(k)==x for k,x in v['bindings'].items());rp=src/'receipt.json';r=json.loads(rp.read_text());assert all(sha(k)==x for k,x in r['bindings'].items()) and all(sha(k)==x for k,x in r['files'].items());bindings.update({str(proof):sha(proof),str(rp):sha(rp)});cmd=json.loads((src/'protocol.json').read_text()).get('command',r.get('command'));assert cmd;candidate=dict(files=r['files'],command=cmd,width=128,decision='R',cpd_ns=r['diagnostic_cpd_ns']);tick=time.perf_counter();row=dict(name=name,mode=mode,status='REJECTED')
 try:
  result=canonical_reload(candidate,src,out/name,inventory);row['canonical']=result;assert result['semantic_consistency_gate_pass'];row['status']='SEMANTIC_CANONICAL_PASS'
 except Exception as error:row['error']=repr(error)
 row['seconds']=time.perf_counter()-tick;rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(mode,row['status'],row.get('error'),flush=True)
assert all(sha(k)==x for k,x in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n')
