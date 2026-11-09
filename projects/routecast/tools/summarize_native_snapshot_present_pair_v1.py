"""Full-scope paired paths/budget outcomes only after independent audit."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_snapshot_present_pair_v1_2026-10-10';proof=O/'verification.json';v=json.loads(proof.read_text());assert v['all115572_per_mode_XML_fraction_raw_budget_and_scaled_objectives_pass'];assert all(sha(p)==h for p,h in v['bindings'].items())
transitions=Counter();changed=raw_lower=raw_higher=equal=both_accepted_changes=0;count=0
with (O/'events.jsonl').open() as s:
 for line in s:
  e=json.loads(line)
  for a,b in zip(e['modes']['unit'],e['modes']['observed_round2']):
   assert a['connection_id']==b['connection_id'];count+=1;transitions[a['status'],b['status']]+=1
   different=a.get('physical_edge_ids')!=b.get('physical_edge_ids');changed+=different
   both_accepted_changes+=different and a['committed'] and b['committed']
   if 'raw_unscaled' in a and 'raw_unscaled' in b:
    raw_lower+=b['raw_unscaled']<a['raw_unscaled'];raw_higher+=b['raw_unscaled']>a['raw_unscaled'];equal+=b['raw_unscaled']==a['raw_unscaled']
assert count==115572;assert all(sha(p)==h for p,h in v['bindings'].items())
out={'bindings':{**v['bindings'],str(proof):sha(proof),str(Path(__file__).resolve()):sha(Path(__file__))},'connections':count,'status_transitions':[{'unit':a,'observed':b,'count':n} for (a,b),n in sorted(transitions.items())],'different_paths':changed,'different_paths_both_budget_accepted':both_accepted_changes,'raw_delay_lower_observed':raw_lower,'raw_delay_higher_observed':raw_higher,'raw_delay_equal':equal,'scope':'Conditional fixed-native-round1 snapshot present1/.5 paired primary diagnostic; later local tree choices can mediate withinNET effects. Not current native NET search-state parity, wholeNET feedback, hotspot improvement, native candidate QoR, heldout or end-to-end gain.'}
f=O/'paired_summary_v1.json';assert not f.exists();f.write_text(json.dumps(out,indent=2)+'\n');print('PAIR SUMMARY',json.dumps({k:v for k,v in out.items() if k!='bindings'}),flush=True)
