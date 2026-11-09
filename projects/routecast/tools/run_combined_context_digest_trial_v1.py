"""Prespecified alternative-candidate ABBA timing, explicit nested adapters."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'combined_context_digest_trial_v1_2026-10-20';O=E/'xtea_placement_feedback_decisions_v1_2026-10-13'
def load(p):return json.loads(p.read_text())
def main():
    D.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [Path(__file__),*[R/'tools'/n for n in ['run_warm_epoch_retained_update_v1.py','run_frozen_digest_session_v1.py','frozen_digest_session_v1.py','run_factored_context_session_v1.py','factored_multiplicative_context_v1.py']]]}
    for cid in [2,6]:
        receipt=O/f'candidate_{cid:02d}/model/receipt.json';manifest=D/f'frozen_manifest_{cid}.json';manifest.write_text(json.dumps(load(receipt)['bindings'],indent=2)+'\n');bindings[str(receipt)]=sha(receipt);bindings[str(manifest)]=sha(manifest)
    protocol=dict(candidates=[2,6],order=['baseline','combined','combined','baseline'],bindings=bindings,
        scope='Two exposed frozen XTEAcandidates prespecified beforetiming;each separateprocess with fullcold adapter caches. Common original producer/prepared inputs;combined factors roundprices and reads/compares full frozen file bytes before digest reuse. Not independent family or fullpaid workflow.',requirements='Exactinitial/final/roundstate and complete event parity;no changed candidate/selection/native config;include adapter overhead in processclock.')
    (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
    for cid in protocol['candidates']:
        source=O/f'candidate_{cid:02d}';prep=source/'prepared'
        for i,mode in enumerate(protocol['order']):
            out=D/f'candidate_{cid:02d}'/f'run_{i}_{mode}';out.mkdir(parents=True)
            args=[str(R/'tools/run_warm_epoch_retained_update_v1.py'),str(E/f'xtea_placement_feedback_cohort_v2_2026-10-13/candidate_{cid:02d}/demand/endpoints.json'),str(out/'model'),str(prep/'base/verification.json'),str(prep/'timing'),str(prep/'warm'),'local']
            if mode=='combined':
                args=[str(R/'tools/run_frozen_digest_session_v1.py'),str(D/f'frozen_manifest_{cid}.json'),str(out/'cache_stats.json'),str(R/'tools/run_factored_context_session_v1.py'),str(out/'factored_adapter.json'),*args]
            start=time.perf_counter()
            with (out/'model.log').open('x') as log:code=subprocess.call(['python3',*args],stdout=log,stderr=subprocess.STDOUT,cwd=R)
            elapsed=time.perf_counter()-start
            if code:raise RuntimeError((cid,mode,code))
            for name in ['initial.json','sketch.json']:assert load(out/'model'/name)==load(source/'model'/name)
            rows.append(dict(candidate_id=cid,mode=mode,exit_code=code,process_seconds=elapsed,output=str(out)))
            (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('COMBINED_TRIAL',cid,i,mode,elapsed,flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (D/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
