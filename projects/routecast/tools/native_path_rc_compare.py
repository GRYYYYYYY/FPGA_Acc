"""Compare native routed paths to native delay labels; singleton identity only."""
import json,math,shutil,time
from pathlib import Path
from collections import defaultdict,Counter
from audit_native_route import NET,NODE
from path_rc import PathRC
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
out=Path('experiments/native_path_rc_compare_2026-10-04')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for name in ('native_path_rc_compare.py','path_rc.py','rr_graph.py','audit_native_route.py','pre_route_endpoints.py'):
 shutil.copyfile(Path(__file__).with_name(name),out/'source'/name)
specs={
 'diffeq':('baseline_cluster_criticality_v7_2026-10-04','experiments/pre_route_endpoints_2026-10-04/diffeq_mapping.json'),
 'elliptic':('elliptic_cluster_criticality_v7_2026-10-04','experiments/elliptic_endpoints_2026-10-04/mapping.json')}
inputs={}
for design,(folder,mapping) in specs.items():
 protocol=json.loads((Path('experiments')/folder/'protocol.json').read_text())
 for key in ('route','graph'):inputs[f'{design}_{key}']=protocol['inputs'][key]
 for key,path in [('mapping',Path(mapping)),('labels',Path('experiments')/folder/'routecast_cluster_criticality.jsonl')]:inputs[f'{design}_{key}']={'path':str(path.resolve()),'sha256':sha(path)}
assert all(sha(e['path'])==e['sha256'] for e in inputs.values())
(out/'protocol.json').write_text(json.dumps({'inputs':inputs,'scope':'native already-routed path expansion vs native route-tree delay, only singleton net/SINK identity; no training/search/candidate CPD','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}},indent=2)+'\n')
summary={};start=time.monotonic()
for design in specs:
 graph=read_rr_graph(inputs[f'{design}_graph']['path']);model=PathRC(graph)
 arcs=defaultdict(list)
 for eid,e in enumerate(graph.edges):arcs[(e.source,e.sink,e.switch_id)].append(eid)
 mapping=json.loads(Path(inputs[f'{design}_mapping']['path']).read_text())
 excluded={r['net_id'] for r in mapping['excluded_nets']}
 key=lambda r:(r['net'],r['block'],r['port'],r['bit'])
 pins={key(r):r for r in mapping['pin_details'] if r['role']=='SINK'}
 labels=defaultdict(list)
 for line in Path(inputs[f'{design}_labels']['path']).read_text().splitlines():
  r=json.loads(line)
  if r['net_id'] in excluded:continue
  pin=pins[key(r)];assert pin['net_id']==r['net_id']
  value=r['native_route_delay_s'];assert math.isfinite(value) and value>=0
  labels[(r['net_id'],pin['rr_node'])].append(value)
 paths=defaultdict(list);net=None;current=None;sw=None;prefix={};source=None
 for line in Path(inputs[f'{design}_route']['path']).read_text().splitlines():
  match=NET.match(line)
  if match:net=int(match[1]);current=None;prefix={};source=None;continue
  match=NODE.match(line)
  if not match:
   if line.lstrip().startswith('Node:'):raise ValueError('unparsed route node')
   continue
  nid=int(match[1]);kind=match[2];next_sw=int(match[3]);assert graph.nodes[nid].type==kind
  if kind=='SOURCE':
   assert not prefix;source=nid;path=()
  elif nid in prefix and kind!='SINK':path=prefix[nid]
  else:
   candidates=arcs[(current,nid,sw)];assert candidates
   path=prefix[current]+(min(candidates),)
  prefix[nid]=path;current=nid;sw=next_sw
  if kind=='SINK' and net not in excluded:paths[(net,nid)].append((source,path))
 assert set(paths)==set(labels)
 assert all(len(paths[k])==len(labels[k]) for k in labels)
 records=[];ambiguous=0
 for k,values in labels.items():
  if len(values)!=1:ambiguous+=len(values);continue
  source,path=paths[k][0];state=model.path(source,path)
  estimate=float(state.delay);native=values[0]
  records.append({'net_id':k[0],'sink':k[1],'path_delay_s':estimate,'native_route_delay_s':native,'difference_s':estimate-native,'path_fraction':str(state.delay)})
 errors=[abs(r['difference_s'])*1e9 for r in records];relative=[abs(r['difference_s'])/r['native_route_delay_s'] for r in records if r['native_route_delay_s']>0]
 summary[design]={'nonclock_connections':sum(map(len,labels.values())),'singleton_connections_compared':len(records),'ambiguous_connections_excluded':ambiguous,'mean_abs_error_ns':sum(errors)/len(errors),'max_abs_error_ns':max(errors),'mean_relative_error':sum(relative)/len(relative),'within_1ps':sum(v<=0.001 for v in errors),'path_underestimates_gt_1ps':sum(r['difference_s']<-1e-12 for r in records),'path_overestimates_gt_1ps':sum(r['difference_s']>1e-12 for r in records)}
 (out/f'{design}_comparison.json').write_text(json.dumps(records,indent=2)+'\n')
assert all(sha(e['path'])==e['sha256'] for e in inputs.values())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'elapsed_s':time.monotonic()-start,'inputs_unchanged':True,'summary':summary,'outputs':{p.name:sha(p) for p in out.glob('*_comparison.json')}},indent=2)+'\n')
print(json.dumps(summary,indent=2))
