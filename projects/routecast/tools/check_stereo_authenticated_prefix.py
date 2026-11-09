"""Real-graph exact batch output parity against a copied completed baseline prefix."""
import json,subprocess,time,shutil
from pathlib import Path
from prepared_csr import read
from pre_route_endpoints import sha

def run():
    base=Path('experiments/stereo_prospective_validation_2026-10-05')
    baseline=base/'ordinary_additive_class_cache_prediction_undriven_v2'
    out=base/'authenticated_host_prefix100';out.mkdir()
    rows=[]
    with (baseline/'net_results.jsonl').open() as f:
        for _ in range(100):rows.append(json.loads(next(f)))
    assert len({r['net_id'] for r in rows})==100
    (out/'baseline_prefix.json').write_text(json.dumps(rows)+'\n')
    binary=Path('build/routecast_csr_authenticated');shutil.copyfile(binary,out/'consumer')
    (out/'consumer').chmod(0o755)
    protocol={'baseline_protocol_sha256':sha(baseline/'protocol.json'),
              'prefix_sha256':sha(out/'baseline_prefix.json'),'binary_sha256':sha(binary),
              'driver_sha256':sha(__file__),'queries':100,
              'scope':'exact completed-prefix output parity, no full-cohort or speedup claim; baseline runs concurrently'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    p=json.loads((baseline/'protocol.json').read_text())
    start=time.monotonic()
    m,payload=read(base/'streaming_csr_class_cache_v3/csr',p['inputs']['graph']['sha256'])
    assert sha(base/'streaming_csr_class_cache_v3/csr/manifest.json')==p['csr_manifest_sha256']
    validation_s=time.monotonic()-start
    query=''.join(' '.join(map(str,[r['source'],*sorted(map(int,r['result']['paths']))]))+'\n' for r in rows)
    # Completed results must include every requested distinct sink before replay.
    e=json.loads(Path(p['inputs']['endpoints']['path']).read_text())
    assert sha(p['inputs']['endpoints']['path'])==p['inputs']['endpoints']['sha256']
    for r in rows:
        assert set(map(int,r['result']['paths']))=={v['sink'] for v in e['connections'] if v['net_id']==r['net_id']}
    (out/'queries.txt').write_text(query)
    start=time.monotonic()
    result=subprocess.run([str((out/'consumer').resolve()),str((base/'streaming_csr_class_cache_v3/csr').resolve()),'--batch'],input=query,capture_output=True,text=True)
    wall=time.monotonic()-start
    (out/'stdout.jsonl').write_text(result.stdout);(out/'stderr.log').write_text(result.stderr)
    assert result.returncode==0,result.stderr
    actual=[json.loads(v) for v in result.stdout.splitlines()]
    assert actual==[r['result'] for r in rows]
    assert sha(binary)==protocol['binary_sha256'] and sha(__file__)==protocol['driver_sha256']
    receipt={'exit_code':result.returncode,'exact_all_paths_and_counters':True,'queries':100,
             'csr_authenticate_s':validation_s,'consumer_load_and_batch_s':wall,
             'protocol_sha256':sha(out/'protocol.json'),'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

if __name__=='__main__':run()
