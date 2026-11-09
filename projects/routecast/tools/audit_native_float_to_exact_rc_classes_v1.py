"""Full native float-bit to original exact RC electrical class recoverability audit."""
import json,struct,sys
from fractions import Fraction
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha_native_resident_snapshot_v1_2026-10-10';p=S/'independent_verification.json';proof=json.loads(p.read_text());assert proof['all91088_native_nodes_and801735_arc_multiset_equal_original_XML'] and all(sha(q)==h for q,h in proof['bindings'].items());epfile=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/cold/demand/sha1/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);indices,classes,switches,digest=read(graph);assert digest==ep['graph_sha256'];snapshot=S/'on/resident.tsv';groups=defaultdict(set);raw={};node_errors=[]
def bits(value):return struct.pack('!f',value).hex()
for line in snapshot.read_text().splitlines():
 x=line.split('\t')
 if x[0]!='N':continue
 n=int(x[1]);r,c=map(float.fromhex,x[9:11]);key=(bits(r),bits(c));exact=classes[indices[n]];groups[key].add(exact);raw[n]=key;binary=(Fraction(r),Fraction(c));node_errors.append((n,binary[0]-exact[0],binary[1]-exact[1]))
assert len(raw)==len(indices)==91088
collisions={k:v for k,v in groups.items() if len(v)>1};different_r=sum(dr!=0 for n,dr,dc in node_errors);different_c=sum(dc!=0 for n,dr,dc in node_errors);different_initial=sum((Fraction(float.fromhex(nextline[9]))*Fraction(float.fromhex(nextline[10]))/2)!=classes[indices[int(nextline[1])]][0]*classes[indices[int(nextline[1])]][1]/2 for nextline in (line.split('\t') for line in snapshot.read_text().splitlines() if line.startswith('N\t')))
D=R/'experiments/native_float_exact_rc_classes_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(q):sha(q) for q in [Path(__file__).resolve(),p,epfile,graph,snapshot,R/'tools/buffered_rc_node_classes.py']};entries=[]
for key,values in sorted(groups.items()):entries.append(dict(native_R_bits=key[0],native_C_bits=key[1],exact_pairs=[[str(r),str(c)] for r,c in sorted(values)]))
result=dict(bindings=bindings,node_count=len(indices),original_textual_RC_classes=len(classes),native_bit_pair_classes=len(groups),ambiguous_native_pairs=len(collisions),nodes_with_R_binary_decimal_difference=different_r,nodes_with_C_binary_decimal_difference=different_c,nodes_with_initial_RC_delay_difference=different_initial,max_absolute_R_difference=str(max(abs(dr) for n,dr,dc in node_errors)),max_absolute_C_difference=str(max(abs(dc) for n,dr,dc in node_errors)),entries=entries,scope='Original graph-bound exact decimal electrical sidecar recoverability from nativefloat32 nodebits. Binaryvalues alone not exact predictor contract. Switch exactR/Tdel still original XML metadata, not native switch parity. First metadata acquisition cost retained; no directresidentmodel or fullgain.')
if not collisions:
 recovered={k:next(iter(v)) for k,v in groups.items()};assert all(recovered[raw[n]]==classes[indices[n]] for n in range(len(indices)));result['all91088_exact_node_RC_pairs_recoverable_with_graph_bound_sidecar']=True
assert all(sha(q)==h for q,h in bindings.items());(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','entries','scope']})
