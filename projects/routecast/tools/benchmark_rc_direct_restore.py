"""ABBA restore-only benchmark on three actual authenticated cache snapshots."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from rc_read_dependency_cache import RCReadDependencyCache
from rc_read_dependency_cache_direct_restore import DirectRestoreRCReadDependencyCache
root=Path(__file__).resolve().parents[1];out=root/'experiments/rc_direct_restore_abba_2026-10-06';out.mkdir();(out/'sources').mkdir();reference=root/'experiments/adder_tree_sparse_dependency_rc_transactions_2026-10-06';receipt=json.loads((reference/'receipt.json').read_text());verified=json.loads((reference/'verification.json').read_text());assert sha(reference/'receipt.json')==verified['receipt_sha256'];inputs={};payloads=[]
for row in receipt['steps']:
 p=reference/f"step_{row['step']}_cache.json";assert sha(p)==row['cache_sha256'];inputs[str(p)]=sha(p);payloads.append(p.read_bytes())
for n in ('benchmark_rc_direct_restore.py','rc_read_dependency_cache.py','rc_read_dependency_cache_direct_restore.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
protocol={'inputs_sha256':inputs,'reference_receipt_sha256':sha(reference/'receipt.json'),'sources_sha256':{p.name:sha(p) for p in (out/'sources').iterdir()},'nodes':15398,'order':['original','direct','direct','original'],'scope':'Prepared immutable bytes loading outside. Complete three snapshot JSON decode and dependency validation/record reconstruction timed. Roundtrip payload validation outside each timer; no native/transaction/overall net benefit inference.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');runs=[]
for trial,mode in enumerate(protocol['order']):
 cls=RCReadDependencyCache if mode=='original' else DirectRestoreRCReadDependencyCache;times=[]
 for payload in payloads:
  start=time.perf_counter();cache=cls.restore(protocol['nodes'],payload);times.append(time.perf_counter()-start);assert cache.payload()==payload and len(cache.records)==516;del cache
 row={'trial':trial,'mode':mode,'snapshot_s':times,'cohort_s':sum(times)};runs.append(row);print(row,flush=True)
assert all(sha(Path(p))==h for p,h in inputs.items());assert all(sha(root/'tools'/n)==h for n,h in protocol['sources_sha256'].items())
a=sum(r['cohort_s'] for r in runs if r['mode']=='original')/2;b=sum(r['cohort_s'] for r in runs if r['mode']=='direct')/2
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'runs':runs,'original_mean_s':a,'direct_mean_s':b,'direct_over_original':b/a,'all_snapshot_roundtrips_byte_equal':True},indent=2)+'\n');print(a,b,b/a)
