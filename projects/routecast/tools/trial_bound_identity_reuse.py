"""Fresh native seeds, GF2 target parity, and bound-input rejection probes."""
import json
from pathlib import Path
from bound_identity_reuse import seed, reuse
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'experiments/gf2_bound_identity_reuse_2026-10-06';out.mkdir()
    prior=ROOT/'experiments/gf2_identity_rebinding_fresh_2026-10-06'
    protocol=json.loads((prior/'protocol.json').read_text())
    assert all(sha(p)==h for p,h in protocol['sources'].items())
    sources=[Path(__file__),ROOT/'tools/bound_identity_reuse.py',ROOT/'tools/guarded_identity_rebinding.py',ROOT/'tools/native_identity_cache.py']
    frozen=dict(parent_protocol_sha256=sha(prior/'protocol.json'),sources={str(p):sha(p) for p in sources},
                scope='Three fresh native cache seeds; same-NET cross-place identity reuse and input rejection. No lifecycle benefit claim.')
    (out/'protocol.json').write_text(json.dumps(frozen,indent=2)+'\n')
    results=[]
    for i in range(0,6,2):
        a,b=protocol['cases'][i:i+2]
        case=out/f"gf2_d{a['width']}";case.mkdir()
        assert all(sha(p)==h for spec in (a,b) for p,h in spec['inputs'].items())
        seed_path=case/'seed.json'
        expected=seed(a['command'],a['source'],case/'cache',seed_path)
        rows=reuse(seed_path,expected,b['command'],b['source'])
        target=Path(protocol['cases'][i+1]['source'])/'identity.jsonl'
        assert rows==[json.loads(s) for s in target.read_text().splitlines()]
        (case/'rebound.json').write_text(json.dumps(rows,indent=2)+'\n')
        bad=case/'changed_input';bad.write_text('different bytes\n')
        rejected=[]
        for name,index in [('binary',0),('architecture',1),('blif',2),
                           ('net',b['command'].index('--net_file')+1),
                           ('graph',b['command'].index('--read_rr_graph')+1)]:
            cmd=b['command'].copy();cmd[index]=str(bad)
            try: reuse(seed_path,expected,cmd,b['source'])
            except ValueError as error:
                assert str(error)=='identity input changed: '+name
                rejected.append(name)
            else: raise AssertionError('accepted changed '+name)
        tampered=case/'tampered_seed.json';tampered.write_bytes(seed_path.read_bytes()+b' ')
        try: reuse(tampered,expected,b['command'],b['source'])
        except ValueError as error:
            assert str(error)=='seed receipt changed';rejected.append('seed_receipt')
        else: raise AssertionError('accepted changed seed')
        results.append(dict(width=a['width'],seed=str(seed_path),seed_sha256=expected,
                            rebound_sha256=sha(case/'rebound.json'),target=str(target),target_sha256=sha(target),
                            pins=sum(len(r['pins']) for r in rows),rejected=rejected))
    assert all(sha(p)==h for spec in protocol['cases'] for p,h in spec['inputs'].items())
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),cases=results),indent=2)+'\n')
    print([(r['width'],r['pins'],len(r['rejected'])) for r in results])

if __name__=='__main__':main()
