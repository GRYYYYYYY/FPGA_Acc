"""Live first/reverse predictions serialized in native NET namespaces."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger, physical_paths
from staged_placement_reroute import stage_reroute_with_repair
from serialize_live_native_candidate import serialize
from stream_native_route_audit import audit

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/live_native_serialization_2026-10-06';out.mkdir()
(out/'protocol.json').write_text(json.dumps(dict(sources={str(p):sha(p) for p in (Path(__file__),ROOT/'tools/serialize_live_native_candidate.py')},scope='Six fresh staged predictions and serialization. Original RR physical audit and archived route semantic parity; no new native run, timing benefit or production publication.'),indent=2)+'\n')
rows=[]
def paths(path):return {n:sorted(v) for n,v in physical_paths(path).items() if v}
for width in (32,64,128):
    original=ROOT/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{width}/endpoints.json'
    swapped=ROOT/f'experiments/gf2_d{width}_placement_swap_2026-10-06/endpoints.json'
    first=ROOT/f'experiments/loaded_quality_gate_original_reload_2026-10-06/gf2_d{width}_A'
    initial=ROOT/f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}/design.route'
    for step,(source,target,route) in enumerate(((original,swapped,initial),(swapped,original,first/'design.route'))):
        ctx=PersistentRCContext(source);state=import_native_ledger(ctx,route)
        result=stage_reroute_with_repair(state,target);candidate=result['repair'] or result['incremental']
        assert candidate['failure'] is None
        if step==0:
            native=ROOT/f'work/gf2_identity_reuse_continuous_two_updates_v2_2026-10-06/gf2_d{width}/0/work/gf2_d{width}_native_seeded_native_import_2026-10-06'
            old=native/'design.route'
        else:
            native=ROOT/f'experiments/loaded_quality_gate_reverse_2026-10-06/gf2_d{width}_A/identity_probe'
            old=native.parent/'predicted.route'
        text,bindings=serialize(candidate,target,native/'identity.jsonl',native/'design.place')
        file=out/f'gf2_d{width}_{step}.route';file.write_text(text)
        assert paths(file)==paths(old)
        graph=Path(json.loads(target.read_text())['inputs']['graph']['path'])
        physical=audit(graph,file);assert len(physical['connections'])=={32:264,64:491,128:908}[width] and physical['overflow_units']==0
        (out/f'gf2_d{width}_{step}_prediction.json').write_text(json.dumps(candidate,indent=2)+'\n')
        rows.append(dict(width=width,step=step,connections=len(bindings),route_sha256=sha(file),inputs={str(p):sha(p) for p in (source,target,route,native/'identity.jsonl',native/'design.place',old)},path_parity=True))
        print(width,step,'live serialization parity',len(bindings),flush=True)
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
