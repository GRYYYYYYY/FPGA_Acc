"""Full12 equality to independent XML/Fraction, packed sink and trace certificates."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'retained_seed_session_cohort_v1_2026-10-08';bindings={}
def read(p):
 d=json.loads(p.read_text())
 for f,h in d.get('bindings',{}).items():
  assert sha(f)==h,f
  assert f not in bindings or bindings[f]==h
  bindings[f]=h
 bindings[str(p)]=sha(p);return d
r=read(D/'receipt.json');p=read(D/'protocol.json');assert r['protocol_sha256']==sha(D/'protocol.json')
assert r['cache_stats']==dict(builds=3,hits=0,evictions=0)
proof=read(E/'endpoint_compatible_branch_trim_v1_2026-10-08/verification.json');assert proof['complete_twelve_cases_independent_branch_forest_pass']
pins=read(E/'retained_branch_sink_identity_v2_2026-10-08/certificate.json');assert pins['all_twelve_unique_sink_identity_maps_pass']
serial=read(E/'retained_branch_native_serialization_v1_2026-10-08/receipt.json');assert serial['all_twelve_serialized_paths_pass']
assert len(r['rows'])==12 and {(x['width'],x['index']) for x in r['rows']}=={(w,i) for w in (8,16,32) for i in range(4)}
for row in r['rows']:
 w,i=row['width'],row['index'];forest=read(D/f'w{w}_m{i}/forest.json');old=read(E/f'endpoint_compatible_branch_trim_v1_2026-10-08/w{w}_m{i}.json')
 assert forest['retained']==old['retained'] and forest['released']==old['released']
 oldrow=next(x for x in serial['rows'] if x['width']==w and x['index']==i)
 assert sha(row['route'])==row['route_sha256']==oldrow['route_sha256']==sha(oldrow['route'])
 assert row['retained']==oldrow['retained_connections'] and row['retained_nets']==oldrow['retained_nets']
 assert len(forest['released'])==row['released']
covered=sum(x['setup_seconds']+x['selection_serialization_seconds'] for x in r['rows']);assert covered<=r['cohort_component_seconds']
bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,complete12_original_fraction_forests_equal=True,complete12_packed_sink_identity_and_serialized_bytes_equal=True,cohort_component_seconds=r['cohort_component_seconds'],covered_component_seconds=covered,residual_seconds=r['cohort_component_seconds']-covered,scope='Fresh session production full cohort inherits independent original XML/Fraction and packed pin certificates by entire forest and exact seed bytes. Historical data only verification inputs. No new native loader execution, full workflow or unseen family/time gain proof.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'})
