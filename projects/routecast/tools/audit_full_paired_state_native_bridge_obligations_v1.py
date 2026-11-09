"""Join actual full-output paired states to intermediate/native state inventory."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'full_source_structural_initial_obligations_v1_2026-10-09/initial_obligations.json';M=E/'full_structural_native_register_mapping_v1_2026-10-09/mapping_audit.json';a=json.loads(I.read_text());mapping=json.loads(M.read_text());index=collections.defaultdict(list)
for row in mapping['rows']:index[row['bit']].append(row)
records=[]
for r in a['registers']:
 matches=index[r['mapped_bit']];assert len(matches)==1,(r,matches);n=matches[0]
 records.append({'source_bit':r['source_bit'],'intermediate_bit':r['mapped_bit'],'native_status':n['status'],'native_candidates':n['native_candidates'],'source_reset_kind':r['reset_kind'],'intermediate_cell':n['cell'],'native_drivers':n['native_drivers'],'obligation':'Prove native transition under the complete relation and its base, retaining shared-state/constant/dead/guarded-memory cases as applicable; named correspondence is not proof.'})
assert len(records)==1741
counts=collections.Counter(r['native_status'] for r in records);targetcounts=collections.Counter(r['native_candidates'][0] for r in records if r['native_status']=='unique_native_state')
D0=E/'full_native_eliminated_state_influence_v1_2026-10-09/influence_audit.json';dead={r['structural_bit']:r for r in json.loads(D0.read_text())['records']};eliminated=[r for r in records if r['native_status']=='unresolved'];assert len(eliminated)==50
for r in eliminated:
 proof=dead[r['intermediate_bit']];assert not proof['external_outputs'] and not proof['retained_states'] and not proof['memory_inputs'];r['existing_noninterference_record']=proof
out={'eliminated_with_existing_noninterference':len(eliminated),'paired_source_register_bits':len(records),'native_status_counts':dict(counts),'unique_native_targets':len(targetcounts),'merged_paired_target_groups':sum(v>1 for v in targetcounts.values()),'constant_values':dict(collections.Counter(str(r['native_candidates']) for r in records if r['native_status']=='constant')),'records':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [I,M,D0]},'scope':'Complete1741 source/intermediate paired-state join to actual intermediate/native alias inventory. Classifies bridge obligations without accepting aliases, local counter/start proofs, or binary boundary function proofs as global state transfer/init proof.'}
d=E/'full_paired_state_native_bridge_obligations_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'bridge_obligations.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['records','hashes']},indent=2))
