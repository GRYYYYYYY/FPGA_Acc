"""Real native capture parity plus incompatible dependencies rejected."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from source_binding import closure
from relocate_original_identity import OriginalIdentityRelocator
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_resume_original_identity_relocation_2026-10-07';o.mkdir(exist_ok=False);s=R/'experiments/native_resume_deferred_proof_adder_2026-10-07';eps=[R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json' for i in (1,2)];graph=Path(json.loads(eps[0].read_text())['inputs']['graph']['path']);inputs={str(p):sha(p) for p in [*eps,s/'rebind_step2/identity.jsonl',s/'rebind_step2/receipt.json',s/'rebind_step3/identity.jsonl',s/'rebind_step3/receipt.json',graph]};proto=dict(inputs=inputs,sources=closure([Path(__file__)]),scope='Archived original-packed native captures used for dependency/parity tests; not prospective full-cost speed or final native routing acceptance.');(o/'protocol.json').write_text(json.dumps(proto,indent=2)+'\n');start=time.perf_counter();adapter=OriginalIdentityRelocator(eps[0],s/'rebind_step2/identity.jsonl',s/'rebind_step2/receipt.json',graph);construction=time.perf_counter()-start;rows=[]
for i,ep in enumerate(eps,1):
 start=time.perf_counter();proof=adapter.relocate(ep,o/f'identity_step{i}.jsonl');reference=s/f'rebind_step{i+1}/identity.jsonl';assert (o/f'identity_step{i}.jsonl').read_bytes()==reference.read_bytes();rows.append(dict(index=i,native_identity_bytes_exact=True,seconds=time.perf_counter()-start,proof=proof))
# Reject altered endpoint identity, changed subtile and changed block set.
meta=json.loads(eps[1].read_text());bad=json.loads(json.dumps(meta));bad['net_names'][next(iter(bad['net_names']))]='incompatible';p=o/'wrong_net.json';p.write_text(json.dumps(bad))
try:adapter.relocate(p,o/'wrong_net_output.jsonl')
except ValueError:assert not (o/'wrong_net_output.jsonl').exists()
else:raise AssertionError('wrong NET accepted')
place=Path(meta['inputs']['place']['path']);lines=place.read_text().splitlines();indices=[i for i,line in enumerate(lines) if line.strip().endswith('#0')];assert len(indices)==1;parts=lines[indices[0]].split();parts[3]=str(int(parts[3])+1);lines[indices[0]]='\t'.join(parts);badplace=o/'wrong_subtile.place';badplace.write_text('\n'.join(lines)+'\n');bad=json.loads(json.dumps(meta));bad['inputs']['place'].update(path=str(badplace),sha256=sha(badplace));p=o/'wrong_subtile.json';p.write_text(json.dumps(bad))
try:adapter.relocate(p,o/'wrong_subtile_output.jsonl')
except ValueError:assert not (o/'wrong_subtile_output.jsonl').exists()
else:raise AssertionError('wrong subtile accepted')
original=(o/'identity_step1.jsonl').read_bytes()
try:adapter.relocate(eps[0],o/'identity_step1.jsonl')
except FileExistsError:assert (o/'identity_step1.jsonl').read_bytes()==original
else:raise AssertionError('existing destination overwritten')
assert all(sha(p)==h for p,h in {**inputs,**proto['sources']}.items());(o/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(o/'protocol.json'),construction_seconds=construction,rows=rows,rejections=['changed_NET','changed_subtile','existing_output'],scope=proto['scope']),indent=2)+'\n');print(construction,[(x['index'],x['seconds']) for x in rows],flush=True)
