"""Independent unchanged-path certificate reuse and current-pin/partition proof."""
import json,re
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha,placements
from audit_native_route import NET,NODE
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_trim_seed_v2_2026-10-18';rp=D/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());G=R/'experiments/mmc_native_state_geometry_v1_2026-10-18';g=json.loads((G/'protocol.json').read_text());P=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18';epfile=P/'demand/endpoints.json';ep=json.loads(epfile.read_text());oldmeta=json.loads(Path(g['previous_endpoint']).read_text());assert ep['graph_sha256']==oldmeta['graph_sha256'];proofpath=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/native/mmc/verification.json';proof=json.loads(proofpath.read_text());assert proof['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and proof['overflow_units']==0 and proof['original_native_FULL_check_pass'];assert all(sha(p)==h for p,h in proof['bindings'].items())
oldroute=Path(g['previous_native_route']);seed=D/'seed.route';before=physical_paths(oldroute);after=physical_paths(seed);selected=set(r['selected_connection_ids']);pending=set(r['pending_connection_ids']);qs={q['connection_id']:q for q in ep['connections']};assert selected.isdisjoint(pending) and selected|pending==set(qs);assert len(selected)==r['selected_connections'] and len(pending)==r['pending_connections'];names={ep['net_names'][str(qs[c]['net_id'])] for c in selected};assert set(after)==names
for name in names:assert after[name]==before[name]
# Compare every printed node type/switch/pin, not only terminal paths.
def printed(path):
 result={};name=None
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:
   name=m[2];assert name not in result;result[name]=[]
  n=NODE.match(line)
  if n:
   pin=re.search(r'Net_pin_index:\s*(\d+)',line);result[name].append((int(n[1]),n[2],int(n[3]),int(pin[1]) if pin else None))
 return result
for line in seed.read_text().splitlines():
 if line.startswith('Net '):assert NET.match(line),'Unexpected nonphysical NET envelope'
 assert not line.startswith('Block '),'Unexpected stale global Block metadata'
oldprinted=printed(oldroute);seedprinted=printed(seed);assert set(seedprinted)==names
for name in names:assert seedprinted[name]==oldprinted[name]
oldocc=Counter(n for rows in oldprinted.values() for n in {x[0] for x in rows});newocc=Counter(n for rows in seedprinted.values() for n in {x[0] for x in rows});assert all(v<=oldocc[n] for n,v in newocc.items())
identity={row['name']:row for row in map(json.loads,Path(ep['inputs']['native_identity']['path']).read_text().splitlines())};mapping=json.loads((P/'mmc/mapping.json').read_text());pos=placements(P/'mmc/design.place',ep['inputs']['net']['sha256']);sites={}
for pin in mapping['pin_details']:
 x,y,z,layer,bid=pos[pin['block']];site=(x,y,layer,pin['class_id']);node=pin['rr_node'];assert node not in sites or sites[node]==site;sites[node]=site
expected=Counter((ep['net_names'][str(qs[c]['net_id'])],qs[c]['source'],qs[c]['sink']) for c in selected);actual=Counter((name,path[0][0],path[-1][0]) for name,paths in after.items() for path in paths);assert actual==expected
for name,rows in seedprinted.items():
 native=identity[name];assert not native['ignored'];source=next(x for x in native['pins'] if x['index']==0);source_site=tuple(source[k] for k in ['x','y','layer','class'])
 for node,kind,switch,pin in rows:
  if kind=='SOURCE':assert sites[node]==source_site
  if kind=='SINK':
   matches=[x for x in native['pins'] if x['index']>0 and tuple(x[k] for k in ['x','y','layer','class'])==sites[node]];assert len(matches)==1 and pin==matches[0]['index']
assert seed.read_text().splitlines()[0]=='Placement_File: design.place Placement_ID: SHA256:'+ep['inputs']['place']['sha256']
bindings={**r['bindings'],str(rp):sha(rp),str(proofpath):sha(proofpath),str(P/'mmc/mapping.json'):sha(P/'mmc/mapping.json'),str(Path(__file__)):sha(__file__)};assert all(sha(p)==h for p,h in bindings.items())
with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(bindings=bindings,selected_connections=len(selected),pending_connections=len(pending),retained_nets=len(names),all_paths_and_printed_node_type_switch_pin_sequences_identical_to_old_native=True,all_current_native_local_pins_and_endpoints_match=True,no_global_NET_or_stale_Block_envelope=True,complete_disjoint_selected_pending_partition=True,uniqueNET_occupancy_monotone_subset_of_authenticated_old_legal_state=True,scope='Exact certificate reuse: graph epoch unchanged, old originalXML/FULL physical proof freshly authenticated, all retained printed sequences identical, capacity follows monotone NET removal. Not a new full XML arc scan, target native routing, canonical completion or QoR result.'),f,indent=2);f.write('\n')
print('PASS lean trim seed',len(selected),'selected',len(pending),'pending; exact old paths/current pins/capacity subset',flush=True)
