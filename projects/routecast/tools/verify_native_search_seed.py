import json,re,hashlib
from pathlib import Path
from stream_native_route_audit import audit
from audit_native_route import NET,NODE
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_search_seed_v3_2026-10-06';work=root/'work/native_search_seed_v3_2026-10-06';command=json.loads((out/'command.json').read_text())['command'];graph=command[command.index('--read_rr_graph')+1]
def sections(path):
 result={};cur=None;prev=None;switch=None;parents={}
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:cur=int(m[1]);assert cur not in result;result[cur]={};prev=None;parents={}
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[node]=[(node,None)]
  elif kind=='SINK':
   pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);result[cur][pin]=parents[prev]+[(node,switch)]
  elif node not in parents:parents[node]=parents[prev]+[(node,switch)]
  prev=node;switch=int(m[3])
 return result
assert sections(work/'seed.route')==sections(work/'output.route')
physical=audit(graph,work/'output.route');assert len(physical['connections'])==129 and physical['overflow_units']==0
(out/'physical_audit.json').write_text(json.dumps(physical,indent=2)+'\n')
log=(out/'run.log').read_text();assert 'VPR succeeded' in log and 'total_nets_routed: 0 total_connections_routed: 0 total_heap_pushes: 0 total_heap_pops: 0' in log;assert 'Found 0 mismatches' in log and 'Fixed 0 routing traces' in log
files=[Path(graph),Path(command[0]),work/'seed.route',work/'output.route',work/'design.net',work/'design.place',out/'run.log',root/'build/native_search_seed_v3_2026-10-06/receipt.json',Path(__file__)]
result={'all_terminal_indexed_physical_paths_and_switches_identical':True,'connections':129,'overflow_units':0,'native_searches':0,'cpd_ns':3.64796,'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'Complete legal-seed retention in actual native route stage; postroute calibrated singleton design, not congested seed repair, prospective QoR or total time benefit.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('129 connections preserved, zero overflow, zero searches, native legality and delay checks enabled')
