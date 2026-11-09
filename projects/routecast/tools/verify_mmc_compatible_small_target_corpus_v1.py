"""Post-run lineage and exact controlled corpus scope audit; no timing replay."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
O=R/'experiments/mmc_compatible_small_target_matched_corpus_v1_2026-10-10'
p=O/'verification.json';v=json.loads(p.read_text());bindings={**v['bindings'],str(p):sha(p),str(Path(__file__).resolve()):sha(Path(__file__))}
contract=R/'experiments/compatible_multi_bidi_contract_v1_2026-10-10/verification.json'
c=json.loads(contract.read_text());assert c['all_requested_minimum_objectives_raw_delays_directed_paths_singleparent_pass']
assert all(sha(q)==h for q,h in c['bindings'].items());bindings.update(c['bindings']);bindings[str(contract)]=sha(contract)
assert all(sha(q)==h for q,h in bindings.items())
r=v['runs'];assert [x['variant'] for x in r]==['original','candidate','candidate','original']
assert all(x['requests']==15353 and x['unique_target_paths']==31877 for x in r)
for x in r:
 if x['variant']=='candidate':
  assert x['stats']['multi_attempts']==x['stats']['merged']==15353 and x['stats']['bidi_calls']==31877
  assert x['paths_different_from_first_original']==10362
 else:assert x['paths_different_from_first_original']==0
assert v['all_requested_physical_exact_RC_minimum_objectives_pass']
(O/'lineage_verification.json').write_text(json.dumps(dict(bindings=bindings,all_current_candidate_and_original_sources_match_preexisting_random_contract=True,complete_fixed_small_target_corpus_pass=True,search_ratio=v['candidate_over_original'],candidate_source_bindings_added_postrun=True,scope='Post-run lineage audit: candidate sources match earlier frozen random contract; measured runner unchanged. No claim of candidate-specific pre-run source snapshot in this harness, statistical generalization, full corpus, endogenous feedback, native or end-to-end gain.'),indent=2)+'\n')
print('MMC SMALL TARGET LINEAGE PASS',v['candidate_over_original'])
