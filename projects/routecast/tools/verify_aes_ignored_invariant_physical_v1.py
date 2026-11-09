"""Additional invariants; does not turn original nonzero-counter gate green."""
import json,sys
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
from stream_native_route_audit import audit
out=R/'experiments/aes_ignored_invariant_canonical_v1_2026-10-08';receipt=out/'receipt.json';proof=out/'verification.json';d=json.loads(receipt.read_text());p=json.loads(proof.read_text());assert all(sha(k)==v for k,v in p['bindings'].items());bindings={str(receipt):sha(receipt),str(proof):sha(proof),str(Path(__file__)):sha(Path(__file__))};rows=[]
def physical_sequences(path):
 answer={};name=None
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:name=m[2];assert name not in answer;answer[name]=[]
  n=NODE.match(line)
  if n:assert name is not None;answer[name].append((int(n[1]),n[2],int(n[3])))
 return answer
for row in d['rows']:
 row={**row['canonical'],'trial':row['trial'],'name':row['name']}
 name=row['name'];original=R/'experiments'/row['trial']/name/'output.route';canonical=out/(row['trial']+'_'+name)/'design.route';assert physical_sequences(original)==physical_sequences(canonical)
 graph=Path(row['command'][row['command'].index('--read_rr_graph')+1]);result=audit(graph,canonical);assert result['overflow_units']==0
 w=out/(row['trial']+'_'+name);assert (w/'design.net').read_bytes()==(w/'design.net.post_routing').read_bytes()
 for file in [original,canonical,graph]:bindings[str(file)]=sha(file)
 rows.append({'trial':row['trial'],'name':name,'all_physical_NET_node_type_switch_sequences_unchanged':True,'canonical_full_original_xml_arc_branch_unique_NET_capacity_audit_pass':True,'canonical_final_packed_netlist_byte_identical':True,'original_strict_zero_counter_gate_pass':False,'canonical_mismatches':row['mismatches'],'canonical_fixups':row['fixups'],'cpd_ns':row['cpd_ns']})
assert all(sha(k)==v for k,v in bindings.items());(out/'physical_invariants_verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Additional independent physical/state invariants. Original strict zero-counter gate remains failed. No unseen-family or completeworkflow gain claim.'},indent=2)+'\n');print(rows)
