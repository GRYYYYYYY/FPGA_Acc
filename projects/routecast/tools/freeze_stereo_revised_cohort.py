"""Bind revised endpoint cohort and prove unchanged selected connection records."""
import json
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha

def run():
    root=Path('experiments/stereo_prospective_validation_2026-10-05')
    out=root/'incremental_cohort_undriven_v2.json'
    if out.exists():raise ValueError('fresh output required')
    paths={'policy':root/'protocol.json','old_cohort':root/'incremental_cohort.json',
           'old_endpoints':root/'endpoints/endpoints.json',
           'endpoints':root/'endpoints_undriven_v2/endpoints.json',
           'alignment':root/'endpoints_undriven_v2/accounting_alignment_audit.json',
           'frontend_protocol':root/'endpoints_undriven_v2/protocol.json'}
    bindings={k:{'path':str(p.resolve()),'sha256':sha(p)} for k,p in paths.items()}
    policy=json.loads(paths['policy'].read_text());old=json.loads(paths['old_cohort'].read_text())
    before=json.loads(paths['old_endpoints'].read_text())['connections']
    rows=json.loads(paths['endpoints'].read_text())['connections']
    audit=json.loads(paths['alignment'].read_text())
    assert audit['native_retained_multiset_exact'] and audit['all_remaining_connection_records_exact']
    assert audit['endpoint_sha256']==bindings['endpoints']['sha256']
    assert old['endpoints_sha256']==bindings['old_endpoints']['sha256']
    assert old['policy_sha256']==bindings['policy']['sha256']
    assert len(rows)==81610 and len({r['connection_id'] for r in rows})==81610
    threshold=policy['policy']['fanout_threshold'];assert threshold==old['fanout_threshold']==64
    counts=Counter(r['net_id'] for r in rows);selected=sorted(n for n,c in counts.items() if c>=threshold)
    cohort=[]
    for net in selected:
        group=sorted((r for r in rows if r['net_id']==net),key=lambda r:r['connection_id'])
        sources={r['source'] for r in group};assert len(sources)==1
        cohort.append({'net_id':net,'source':next(iter(sources)),'fanout':counts[net],
                       'distinct_sink_classes':len({r['sink'] for r in group}),
                       'connection_ids':[r['connection_id'] for r in group]})
    assert cohort==old['ordered_cohort']
    selected_set=set(selected)
    key=lambda r:(r['net_id'],r['connection_id'])
    assert sorted((r for r in rows if r['net_id'] in selected_set),key=key)==sorted((r for r in before if r['net_id'] in selected_set),key=key)
    assert len(selected)==18 and sum(c['fanout'] for c in cohort)==2514
    result={**old,'endpoints_sha256':bindings['endpoints']['sha256'],'source_sha256':sha(__file__),
            'total_connections':len(rows),'total_nets':len(counts),'ordered_cohort':cohort,
            'input_bindings':bindings,'selected_records_exactly_unchanged':True,
            'revision_provenance':audit['revision_provenance'],
            'scope':'revised frontend binding; original endpoint-only selection and all selected records unchanged; not a pristine prospective frontend or executed feedback result'}
    assert all(sha(paths[k])==v['sha256'] for k,v in bindings.items())
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'selected_nets':18,'selected_connections':2514,'total_nets':len(counts),'selected_records_exactly_unchanged':True,'output_sha256':sha(out)}),flush=True)

if __name__=='__main__':run()
