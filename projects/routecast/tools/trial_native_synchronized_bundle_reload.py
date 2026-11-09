"""Coherent packed/placement/route reload with native digest checks enabled."""
import json,shutil,re,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'native_synchronized_bundle_reload_2026-10-06';work=root/'work/native_synchronized_bundle_reload_2026-10-06';out.mkdir();work.mkdir();shutil.copyfile(Path(__file__),out/'source.py');parent=base/'native_predictor_sync_capture_2026-10-06';r=json.loads((parent/'receipt.json').read_text());sourcework=root/'work/native_predictor_sync_capture_2026-10-06';packed=sourcework/'design.net.post_routing';assert sha(packed)==r['post_routing_netlist_sha256'];originalpacked=sourcework/'design.net';originalplace=sourcework/'design.place';originalroute=sourcework/'design.route';command=json.loads((base/'predictor_native_trace_import_2026-10-06/command.json').read_text())['command'];binary=root/'build/native_route_sync_capture_v2_2026-10-06/routecast_sync_capture_vpr';assert sha(binary)==r['capture_binary_sha256'];command[0]=str(binary);records=[]
for mode in ('stale_packed_digest','rebound_bundle'):
 wd=work/mode;wd.mkdir();shutil.copyfile(sourcework/'design.blif',wd/'design.blif');shutil.copyfile(packed,wd/'design.net');place=originalplace.read_text();route=originalroute.read_text()
 if mode=='rebound_bundle':
  marker='Netlist_ID: SHA256:'+sha(originalpacked);assert marker in place;place=place.replace(marker,'Netlist_ID: SHA256:'+sha(wd/'design.net'),1)
 (wd/'design.place').write_text(place)
 if mode=='rebound_bundle':
  marker='Placement_ID: SHA256:'+sha(originalplace);assert marker in route;route=route.replace(marker,'Placement_ID: SHA256:'+sha(wd/'design.place'),1)
 (wd/'design.route').write_text(route);assert place.splitlines()[1:]==originalplace.read_text().splitlines()[1:];assert route.splitlines()[1:]==originalroute.read_text().splitlines()[1:];cmd=command.copy();(out/f'{mode}_command.json').write_text(json.dumps({'command':cmd,'cwd':str(wd)})+'\n');start=time.perf_counter()
 with (out/f'{mode}.log').open('w') as log:code=subprocess.run(cmd,cwd=wd,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 text=(out/f'{mode}.log').read_text();cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text);mismatch=re.search(r'Found (\d+) mismatches between routing and packing results',text);fixup=re.search(r'Fixed (\d+) routing traces',text);records.append({'mode':mode,'exit_code':code,'wall_s':time.perf_counter()-start,'log_sha256':sha(out/f'{mode}.log'),'packed_sha256':sha(wd/'design.net'),'placement_sha256':sha(wd/'design.place'),'route_sha256':sha(wd/'design.route'),'vpr_success':code==0 and 'VPR succeeded' in text,'cpd_ns':float(cpd[1]) if cpd else None,'sync_mismatches':int(mismatch[1]) if mismatch else None,'sync_fixups':int(fixup[1]) if fixup else None});print(records[-1],flush=True)
 assert '--verify_file_digests' not in cmd
assert records[0]['exit_code']!=0
(out/'receipt.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'capture_receipt_sha256':sha(parent/'receipt.json'),'runs':records,'scope':'Native synchronized packed netlist reloaded with only netlist/placement digest header updates; coordinates and route body unchanged. Explicit native digest verification retained. Not crossprocess atom/timing cache snapshot, seed-preserving reroute, or pre-route mapping evidence.'},indent=2)+'\n')
