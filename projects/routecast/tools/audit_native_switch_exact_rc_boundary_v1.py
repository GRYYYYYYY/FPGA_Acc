"""Complete native switch precision and fixed original initial path RC comparison; no search-equivalence claim."""
import json,sys
from pathlib import Path
from fractions import Fraction
from collections import Counter
from math import lcm
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
from immutable_xml_prediction_audit import ImmutableXMLAudit
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha_native_resident_snapshot_v3_2026-10-10';vp=S/'independent_verification.json';v=json.loads(vp.read_text());assert v['all_native_switch_R_Tdel_equal_original_XML_loaded_to_float'] and all(sha(p)==h for p,h in v['bindings'].items());epfile=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);ids,classes,switches,digest=read(graph);assert digest==ep['graph_sha256'];xml=ImmutableXMLAudit(graph,digest);native={};used=Counter();snapshot=S/'on/resident.tsv'
for line in snapshot.read_text().splitlines():
 x=line.split('\t')
 if x[0]=='S':native[int(x[1])]=tuple(Fraction(float.fromhex(a)) for a in x[2:])
 elif x[0]=='E':used[int(x[3])]+=1
assert set(native)==set(switches) and all(r==c==0 for r,c in classes)
entries=[dict(switch_id=sid,exact_R=str(switches[sid][0]),exact_Tdel=str(switches[sid][1]),native_R=str(native[sid][0]),native_Tdel=str(native[sid][1]),R_difference=str(native[sid][0]-switches[sid][0]),Tdel_difference=str(native[sid][1]-switches[sid][1]),arc_count=used[sid]) for sid in sorted(switches)]
scale=lcm(1,*(switches[sid][1].denominator for sid in used));initialfile=R/'experiments/sha_overflow_guard_v1_2026-10-10/second_swap/model/initial.json';initial=json.loads(initialfile.read_text());assert len(initial['records'])==6273;paths=[]
for rec in initial['records']:
 exact=sum((switches[xml.graph.edges[e].switch_id][1] for e in rec['answer']['physical_edge_ids']),Fraction());binary=sum((native[xml.graph.edges[e].switch_id][1] for e in rec['answer']['physical_edge_ids']),Fraction());assert exact==Fraction(rec['floor_integer'],scale);paths.append(dict(connection_id=rec['connection_id'],original_minimum_delay=str(exact),native_binary_cost_on_original_path=str(binary),difference=str(binary-exact),native_same_path_within_original_budget=binary<=Fraction(rec['budget_integer'],scale)))
D=R/'experiments/native_switch_exact_rc_boundary_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(p):sha(p) for p in [Path(__file__).resolve(),vp,epfile,graph,snapshot,initialfile,R/'tools/buffered_rc_node_classes.py',R/'tools/immutable_xml_prediction_audit.py']};assert all(sha(p)==h for p,h in bindings.items());result=dict(bindings=bindings,node_RC_zero_for_all91088=True,switches=len(switches),switch_R_different=sum(native[s][0]!=switches[s][0] for s in switches),switch_Tdel_different=sum(native[s][1]!=switches[s][1] for s in switches),used_arcs_with_electrical_difference=sum(used[s] for s in used if native[s]!=switches[s]),original_integer_scale=scale,all6273_original_floor_paths_recomputed=True,original_paths_with_different_binary_delay=sum(Fraction(p['difference'])!=0 for p in paths),all_original_paths_budget_safe_under_native_binary=sum(p['native_same_path_within_original_budget'] for p in paths)==6273,max_absolute_same_path_delay_difference=str(max(abs(Fraction(p['difference'])) for p in paths)),switch_entries=entries,paths=paths,scope='All native switches and all original complete floor paths; binary exact-rational reinterpretation, not native floating accumulation/shortest path/weighted feedback state equivalence. NodeRCzero graph-specific. Graph+switchID exact metadata can preserve decimal model, acquisitioncost still required; no performance/heldout/hardware proof.');(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','switch_entries','paths','scope']})
