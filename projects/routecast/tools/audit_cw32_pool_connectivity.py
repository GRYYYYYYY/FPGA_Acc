"""Static CSR-authenticated pool pin-access differences, no interchangeable claim."""
import json,shutil
from pathlib import Path
from collections import defaultdict
from prepared_csr import read
from pre_route_endpoints import sha
from pooled_channel_pressure import KEYS

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_pool_connectivity_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_cw32_pool_connectivity.py','prepared_csr.py','pre_route_endpoints.py','pooled_channel_pressure.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Static direct external adjacency and direct OPIN-SOURCE/IPIN-SINK class access; switch-aware external signatures. Differences refute identical direct access, do not prove absence of multi-hop alternatives or native route impossibility. Same signatures do not prove electrical interchangeability.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');summary=[]
 for name in protocol['cohort']:
  prepared=root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name;p=json.loads((prepared/'protocol.json').read_text());r=json.loads((prepared/'receipt.json').read_text());assert sha(prepared/'protocol.json')==r['protocol_sha256'];auditroot=root/'experiments/multiplier_family_length_switch_csr_audit_cw32_2026-10-06'/name;a=json.loads((auditroot/'receipt.json').read_text());assert a['all_node_metadata_and_edge_costs_match_original_xml'] and a['parent_receipt_sha256']==sha(prepared/'receipt.json');m,f=read(prepared/'csr',p['graph']['sha256']);groups=defaultdict(list);incoming=defaultdict(set);outgoing=defaultdict(set);source_classes=defaultdict(set);sink_classes=defaultdict(set)
  for u in range(m['nodes']):
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot];sid=f['switch_ids'][slot];outgoing[u].add((v,sid));incoming[v].add((u,sid))
    if f['types'][u]==0 and f['types'][v]==2:source_classes[v].add(u)
    if f['types'][u]==3 and f['types'][v]==1:sink_classes[u].add(v)
  for n,cap in enumerate(f['capacities']):
   if f['types'][n] in (4,5) and cap>0:groups[tuple(f[k][n] for k in KEYS)].append(n)
  reports=[]
  for key,nodes in groups.items():
   if len(nodes)<2:continue
   members=set(nodes);external_in={n:frozenset((u,s) for u,s in incoming[n] if u not in members) for n in nodes};external_out={n:frozenset((v,s) for v,s in outgoing[n] if v not in members) for n in nodes};src={n:frozenset(c for u,s in incoming[n] for c in source_classes[u]) for n in nodes};sink={n:frozenset(c for v,s in outgoing[n] for c in sink_classes[v]) for n in nodes};reports.append({'key':key,'nodes':nodes,'distinct_external_input_signatures':len(set(external_in.values())),'distinct_external_output_signatures':len(set(external_out.values())),'distinct_direct_source_class_sets':len(set(src.values())),'distinct_direct_sink_class_sets':len(set(sink.values())),'source_class_access_by_node':{str(n):sorted(src[n]) for n in nodes},'sink_class_access_by_node':{str(n):sorted(sink[n]) for n in nodes}})
  dest=out/name;dest.mkdir();(dest/'pools.json').write_text(json.dumps(reports)+'\n');row={'design':name,'multi_track_pools':len(reports),'different_external_adjacency_pools':sum(x['distinct_external_input_signatures']>1 or x['distinct_external_output_signatures']>1 for x in reports),'different_direct_pin_class_access_pools':sum(x['distinct_direct_source_class_sets']>1 or x['distinct_direct_sink_class_sets']>1 for x in reports),'pools_sha256':sha(dest/'pools.json'),'csr_receipt_sha256':sha(prepared/'receipt.json'),'xml_audit_receipt_sha256':sha(auditroot/'receipt.json')};summary.append(row);print(json.dumps(row),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':summary},indent=2)+'\n')
if __name__=='__main__':main()
