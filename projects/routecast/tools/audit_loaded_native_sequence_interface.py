"""Evidence audit: existing same-process sequence versus GF2 estimator contract."""
import json
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/native_candidate_adder_sequence_2026-10-06'
r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text())
assert all(sha(path)==h for path,h in v['sha256'].items())
assert sha(r['command'][0])==r['binary_sha256']
source=ROOT/'build/native_candidate_multi_pair_2026-10-06/source/route.cpp'
text=source.read_text()
needles={
 'declared_block_pairs':'ROUTECAST_MOVE_PAIRS',
 'cold_candidate_seed_removed':'unsetenv("ROUTECAST_NATIVE_SEED")',
 'recursive_native_route':'bool candidate_ok=route(net_list,width_fac,router_opts',
 'packing_sync':'sync_netlists_to_routing(net_list,device_ctx,mutable_atom,mutable_cluster',
 'explicit_AR_decision':"sequence[step]=='A'",
 'STA_refresh':'delay_calc->clear_cache()',
 'accepted_placement_serialization':'"accepted.place",registry.block_locs()',
 'rollback_timing_observation':'restored delay matrix and all edge-delay/STA metric observations',
}
anchors={}
for name,needle in needles.items():
    assert needle in text
    anchors[name]=[i for i,line in enumerate(text.splitlines(),1) if needle in line]
requirements=[
 dict(requirement='Same-process compatible move, FULL/packing/STA and rejection rollback',status='existing bounded evidence',evidence='Five adder-tree sequence runs; explicit A/R decisions; verifier binds outputs and rejection-prefix byte equality'),
 dict(requirement='Current GF2 target sequence and three widths at channel128',status='not established by this evidence',evidence='Archived sequence dataset is adder_tree_2L_032bits at channel300'),
 dict(requirement='Import live estimator physical candidate without replacing it by native cold routing',status='interface gap',evidence='Candidate unsets seed and calls recursive native route; this is different candidate generation'),
 dict(requirement='Compare predicted and cold reference CPD for same target placement',status='interface gap in this audited variant',evidence='A/R externally prescribed; no same-target two-bundle quality selection in this sequence'),
 dict(requirement='Post-sync NET/pin identity and owner ledger returned for next estimator update',status='integration gap',evidence='Final route/packed net/accepted place outputs exist; GF2 Python owner handoff and six-state parity unverified'),
 dict(requirement='Fair complete lifecycle timing benefit',status='missing',evidence='No fresh GF2 integrated policy-equivalent benchmark in audited artifacts'),
]
out=ROOT/'experiments/loaded_native_sequence_interface_audit_2026-10-06';out.mkdir()
(out/'report.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings={str(p):sha(p) for p in (parent/'receipt.json',parent/'verification.json',source,Path(r['command'][0]))},verified_cases=v['cases'],candidate_steps=v['candidate_steps'],source_anchors=anchors,requirements=requirements,scope='Current authenticated archived implementation audit, not a fresh native run or universal absence claim. Other timing-gated variants exist and need separate audit.'),indent=2)+'\n')
print('authenticated',v['cases'],'cases',v['candidate_steps'],'steps; estimator candidate import remains interface gap')
