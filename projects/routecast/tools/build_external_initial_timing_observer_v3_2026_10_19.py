"""Extend read-only native initialized timing snapshot with exact current pin witness."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def main():
 old=R/'build/native_initial_timing_snapshot_v2_2026-10-17';rp=old/'receipt.json';p=json.loads(rp.read_text());assert sha(old/'sequence_vpr')==p['binary_sha256'] and all(sha(f)==h for f,h in p['bindings'].items());out=R/'build/native_initial_timing_pin_snapshot_v3_2026-10-19';out.mkdir(exist_ok=False);template=R/'tools/native_search_seed/initial_timing_pin_observer_v3.cpp';symbol=p['symbol'];source=template.read_text().replace('REAL','__real_'+symbol).replace('WRAP','__wrap_'+symbol);(out/'observer.cpp').write_text(source);compile=[s.replace(str(old),str(out)) for s in p['compile']];link=[s.replace(str(old),str(out)) for s in p['link']];paths=[rp,old/'sequence_vpr',template,out/'observer.cpp',Path(__file__).resolve()];bindings={**p['bindings'],**{str(f):sha(f) for f in paths}};(out/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Existing initialized timing observer plus read-only same-process native net/local/global pin, block name/id, physical pin/class and RR SOURCE/SINK witness. Original REAL getter, atom aggregation and first-getter-exit preserved; no routing search or input mutation.'),indent=2))
 for name,cmd in [('compile',compile),('link',link)]:
  with (out/(name+'.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  print('INITIAL_PIN_OBSERVER_'+name.upper(),r.returncode,flush=True)
  if r.returncode:raise SystemExit(r.returncode)
 assert all(sha(f)==h for f,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(out/'sequence_vpr'),symbol=symbol,bindings={str(f):sha(f) for f in [out/'protocol.json',out/'observer.cpp',out/'observer.o',out/'compile.log',out/'link.log']}),indent=2));print('INITIAL_TIMING_PIN_OBSERVER_BUILT',flush=True)
if __name__=='__main__':main()
