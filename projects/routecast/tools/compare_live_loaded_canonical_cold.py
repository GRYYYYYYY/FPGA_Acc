"""Bounded complete-policy comparison with explicit canonical state divergence."""
import json
from pathlib import Path
from pre_route_endpoints import sha, placements

ROOT=Path(__file__).resolve().parents[1]
paths={k:ROOT/'experiments'/n for k,n in [('live','live_loaded_two_updates_2026-10-06'),('cold','cold_canonical_two_updates_2026-10-06')]}
data={};protocols={}
for k,p in paths.items():
    data[k]=json.loads((p/'receipt.json').read_text());protocols[k]=json.loads((p/'protocol.json').read_text())
    assert json.loads((p/'verification.json').read_text())['receipt_sha256']==sha(p/'receipt.json')
    assert data[k]['protocol_sha256']==sha(p/'protocol.json')
rows=[]
for a,b,ca,cb in zip(data['live']['rows'],data['cold']['rows'],protocols['live']['cases'],protocols['cold']['cases']):
    width=a['width'];assert width==b['width']==ca['width']==cb['width']
    assert ca['inputs']==cb['inputs'] and ca['targets']==cb['targets']
    assert a['complete'] and b['complete'] and a['error'] is b['error'] is None
    rounds=[]
    for ar,br in zip(a['rounds'],b['rounds']):
        step=ar['step'];assert step==br['step']
        acmd=ar['native']['command'];bcmd=br['native']['command'];assert acmd[1:]==bcmd[1:]
        ap=paths['live']/f'gf2_d{width}_{step}';bp=paths['cold']/f'gf2_d{width}_{step}'
        for suffix in ('identity_probe','canonical'):
            positions=[]
            for p in (ap/suffix,bp/suffix):
                positions.append({name:row[:4] for name,row in placements(p/'design.place',sha(p/'design.net')).items()})
            assert positions[0]==positions[1]
        sa=json.loads((ap/'accepted_state.json').read_text());sb=json.loads((bp/'accepted_state.json').read_text())
        assert len(sa['records'])==len(sb['records'])
        changed=sum(x['answer']['physical_edge_ids']!=y['answer']['physical_edge_ids'] for x,y in zip(sa['records'],sb['records']))
        rounds.append(dict(step=step,live_cpd_ns=ar['reload']['cpd_ns'],cold_cpd_ns=br['reload']['cpd_ns'],canonical_net_equal=sha(ap/'canonical/design.net')==sha(bp/'canonical/design.net'),changed_physical_paths=changed))
    rows.append(dict(width=width,live_wall_s=a['case_wall_s'],cold_wall_s=b['case_wall_s'],live_over_cold=a['case_wall_s']/b['case_wall_s'],rounds=rounds))
out=ROOT/'experiments/live_loaded_canonical_cold_comparison_2026-10-06';out.mkdir()
(out/'report.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings={k:{'receipt_sha256':sha(p/'receipt.json'),'verification_sha256':sha(p/'verification.json')} for k,p in paths.items()},rows=rows,scope='Single serial observations, complete policy windows with same initial inputs/targets and canonical reload/direct audit/ledger treatment. Own canonical states evolve and differ; this is policy comparison, not fixed-input per-update causal speedup or interleaved statistical evidence. Initial routing/frontend/build and outer independent audits excluded.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
