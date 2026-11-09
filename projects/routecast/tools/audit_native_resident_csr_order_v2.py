"""Full native edge iteration CSR ordering versus original XML physical edge IDs."""
import json,sys
from pathlib import Path
from array import array
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha_native_resident_snapshot_v4_2026-10-10';vp=S/'independent_verification.json';v=json.loads(vp.read_text());assert v['all91088_native_nodes_and801735_arc_multiset_equal_original_XML'] and all(sha(p)==h for p,h in v['bindings'].items());epfile=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';graph,digest,nodes,f,rc,qs=load_endpoints(epfile);snapshot=S/'on/resident.tsv';degrees=array('Q',[0])*len(nodes);dest=array('Q');switch=array('Q');source=array('Q');previous=-1
for line in snapshot.read_text().splitlines():
 x=line.split('\t')
 if x[0]!='E':continue
 u,v,s=map(int,x[1:]);assert u>=previous;previous=u;degrees[u]+=1;source.append(u);dest.append(v);switch.append(s)
rows=array('Q',[0])
for n in degrees:rows.append(rows[-1]+n)
assert rows.tobytes()==f['row_offsets'].tobytes();mismatch=[i for i in range(len(dest)) if (dest[i],switch[i])!=(f['dest_ranks'][i],f['switch_ids'][i])];identity=sum(i==e for i,e in enumerate(f['edge_ids']));D=R/'experiments/native_resident_csr_order_v2_2026-10-10';assert not D.exists();D.mkdir();bindings={str(p):sha(p) for p in [Path(__file__).resolve(),vp,epfile,graph,snapshot,R/'tools/class_cached_rc_endpoint_context_v1.py']};assert all(sha(p)==h for p,h in bindings.items());result=dict(bindings=bindings,nodes=len(nodes),arcs=len(dest),all_CSR_row_offsets_equal=True,ordered_arc_mismatch_count=len(mismatch),identity_original_physical_edge_ID_slots=identity,all_native_ordered_arcs_equal_original_CSR=not mismatch,all_native_CSR_slots_equal_original_physical_edge_ID=identity==len(dest),scope='Full actual RR adjacency order and physicaledge-ID contract only. Parallel arcs retain multiplicity. No prospective model equivalence/zero-copy/completeworkflow gain.')
if mismatch:result['mismatches']=[dict(slot=i,native_source=source[i],native_dest=dest[i],native_switch=switch[i],original_dest=f['dest_ranks'][i],original_switch=f['switch_ids'][i],original_eid=f['edge_ids'][i]) for i in mismatch]
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','scope','mismatches']})
