"""Post-evaluation diagnostics; frozen primary metrics are never rewritten."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
src=R/'experiments/ethernet_hotspots_v1_2026-10-08'
proof=src/'metric_verification.json';p=json.loads(proof.read_text())
assert p['histogram_ranks_topk_mae_and_full_vector_scope_pass'] and all(sha(k)==v for k,v in p['bindings'].items())
vf=src/'comparison_vectors.json';cf=src/'comparison.json'
v=json.loads(vf.read_text());c=json.loads(cf.read_text());bins=v['bins']
bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(vf):sha(vf),str(cf):sha(cf)}
out=R/'experiments/ethernet_hotspot_diagnostic_v1_2026-10-08';out.mkdir()
methods=['native','geometry','rc_initial','wire_independent','wire_shared']
values={m:{tuple(x['key']):(x['geometry'] if m=='geometry' else (x['native'] if m=='native' else x['predictions'][m])/x['capacity']) for x in bins} for m in methods}
tops={m:sorted(values[m],key=lambda k:(-values[m][k],k))[:20] for m in methods}
boundary={m:values[m][tops[m][-1]] for m in methods}
envelopes={m:{k for k,val in values[m].items() if val>=boundary[m]} for m in methods}
def group_hist(keys):
    return dict(Counter(str((k[0],k[3],k[4])) for k in keys))
summary={}
for m in methods:
    strict=sum(x>boundary[m] for x in values[m].values())
    tied=sum(x==boundary[m] for x in values[m].values())
    summary[m]=dict(boundary=boundary[m],strictly_above=strict,tied_at_boundary=tied,top20_direction_segment_histogram=group_hist(tops[m]),boundary_envelope_size=len(envelopes[m]))
    if m!='native':
        overlap=len(set(tops[m])&set(tops['native']))
        assert overlap/20==c['metrics'][m]['spatial']['precision_at_k']
        summary[m].update(frozen_top20_overlap=overlap,predicted_top20_in_native_boundary_envelope=len(set(tops[m])&envelopes['native']),boundary_envelopes_intersection=len(envelopes[m]&envelopes['native']),native_utilization_at_predicted_top20=[values['native'][k] for k in tops[m]],predicted_utilization_at_native_top20=[values[m][k] for k in tops['native']])
groups=defaultdict(list)
for x in bins:groups[(x['key'][0],x['key'][3],x['key'][4])].append(x)
group_rows=[]
for k,items in sorted(groups.items()):
    cap=sum(x['capacity'] for x in items);truth=sum(x['native'] for x in items)
    row=dict(key=list(k),bins=len(items),capacity_sum=cap,native_demand_sum=truth,native_capacity_weighted_utilization=truth/cap,methods={})
    for m in methods[1:]:
        row['methods'][m]=dict(mean_utilization=sum(values[m][tuple(x['key'])] for x in items)/len(items),mae=sum(abs(values[m][tuple(x['key'])]-values['native'][tuple(x['key'])]) for x in items)/len(items),mean_signed_error=sum(values[m][tuple(x['key'])]-values['native'][tuple(x['key'])] for x in items)/len(items))
    group_rows.append(row)
rows=[dict(key=list(k),values={m:values[m][k] for m in methods},native_rank=sorted(values['native'],key=lambda j:(-values['native'][j],j)).index(k)+1) for k in sorted(set().union(*map(set,tops.values())))]
assert all(sha(k)==v for k,v in bindings.items())
(out/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,summary=summary,groups=group_rows,top_union_bins=rows,scope='Post-hoc diagnostic of frozen metrics, not new primary metric or tuning/heldout success. Boundary envelopes disclose ties; spatial demand counts node coverage, so long resources appear in several bins.'),indent=2)+'\n')
print(json.dumps(summary),flush=True)
