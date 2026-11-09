"""Authenticate entire block, repeated policy states and all observations."""
import json
import re
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/live_loaded_cold_ABBA_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and len(p['runs'])==len(r['rows'])==4
assert [run['mode'] for run in p['runs']]==['cold','live','live','cold']
states={};timings={};cpds={};bindings={};choices=[]
for spec,row in zip(p['runs'],r['rows']):
    assert spec['index']==row['index'] and spec['mode']==row['mode'] and len(row['stages'])==2
    assert all(sha(f)==h for f,h in spec['sources'].items())
    for index,stage in enumerate(row['stages']):
        assert stage['exit_code']==0 and stage['command']==spec['commands'][index]
        assert sha(out/f"run{spec['index']}_stage{index}.log")==stage['log_sha256']
    base=ROOT/'experiments'/spec['experiment'];receipt=json.loads((base/'receipt.json').read_text())
    verification=json.loads((base/'verification.json').read_text());protocol=json.loads((base/'protocol.json').read_text())
    assert verification['receipt_sha256']==sha(base/'receipt.json') and receipt['protocol_sha256']==sha(base/'protocol.json')
    assert len(receipt['rows'])==len(verification['rows'])==3
    assert all(sha(f)==h for group in ('sources','binaries') for f,h in protocol[group].items())
    bindings[spec['experiment']]=dict(receipt=sha(base/'receipt.json'),verification=sha(base/'verification.json'),protocol=sha(base/'protocol.json'))
    for case,vcase in zip(receipt['rows'],verification['rows']):
        width=case['width'];assert width==vcase['width'] and case['complete'] and case['error'] is None
        timings.setdefault((spec['mode'],width),[]).append(case['case_wall_s'])
        cpds.setdefault((spec['mode'],width),[]).append(case['rounds'][-1]['reload']['cpd_ns'])
        for rr in case['rounds']:
            work=base/f"gf2_d{width}_{rr['step']}";snapshot=work/'accepted_state.json'
            assert sha(snapshot)==rr['snapshot_sha256'];state=json.loads(snapshot.read_text())
            key=(spec['mode'],width,rr['step'])
            if key in states:assert states[key]==state
            else:states[key]=state
            native,reload=rr['native'],rr['reload']
            assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0
            assert all(sha(f)==h for f,h in native['files'].items()) and all(sha(f)==h for f,h in reload['files'].items())
            if spec['mode']=='live':
                text=(work/'run.log').read_text();m=re.search(r'same-target gate predicted_cpd_ns=([0-9.]+) reference_cpd_ns=([0-9.]+) selected=(\w+)',text);assert m
                pred,ref=map(float,m.groups()[:2]);assert m[3]==('reference' if pred>ref else 'predicted') and abs(reload['cpd_ns']-min(pred,ref))<=5.1e-5
                choices.append(dict(run=spec['index'],width=width,step=rr['step'],selected=m[3]))
rows=[]
for width in (32,64,128):
    a=timings['live',width];b=timings['cold',width];assert len(a)==len(b)==2
    assert len(set(cpds['live',width]))==len(set(cpds['cold',width]))==1
    rows.append(dict(width=width,live_seconds=a,cold_seconds=b,live_mean_s=sum(a)/2,cold_mean_s=sum(b)/2,live_over_cold=sum(a)/sum(b),live_final_cpd_ns=cpds['live',width][0],cold_final_cpd_ns=cpds['cold',width][0]))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,choices=choices,repeated_policy_snapshots_equal=12,scope='One whole-family ABBA block, all24 accepted snapshots physically checked by bound outer verifiers. Same-policy repeated states exact. Own canonical state divergence retained; no confidence interval or universal/generalized benefit.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
