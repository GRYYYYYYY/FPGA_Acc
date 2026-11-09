"""Posthoc native/predicted per-net channel sharing; no cost changes."""
import json,shutil
from pathlib import Path
from collections import Counter,defaultdict
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
out=Path('experiments/clma_sharing_diagnosis_2026-10-04')
if out.exists():raise ValueError('fresh output required')
inputs=json.loads(Path('experiments/clma_spatial_diagnosis_2026-10-04/protocol.json').read_text())['inputs'];ep=Path('experiments/clma_constant_policy_2026-10-04/endpoints.json');inputs={**inputs,'endpoints':{'path':str(ep.resolve()),'sha256':sha(ep)}}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
(out/'protocol.json').write_text(json.dumps({'inputs':inputs,'scope':'posthoc per-net channel sharing/native path cohorts, no causal claim or model tuning','cohort':'all original nonclock/nonconstant connections, exact net/source/sink multiplicities','fanout_bins':['1','2-4','5-16','17+'],'source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}},indent=2)+'\n')
g=read_rr_graph(inputs['graph']['path']);e=json.loads(ep.read_text());expected=Counter((r['net_id'],r['source'],r['sink']) for r in e['connections']);allowed={r['net_id'] for r in e['connections']};records=[];net=None;prefix={};current=None;source=None;switch=None;arcset={(a.source,a.sink,a.switch_id) for a in g.edges}
for line in Path(inputs['route']['path']).read_text().splitlines():
 m=NET.match(line)
 if m:net=int(m[1]);prefix={};current=None;source=None;continue
 m=NODE.match(line)
 if not m:
  if line.lstrip().startswith('Node:'):raise ValueError('unparsed node')
  continue
 nid=int(m[1]);kind=m[2];next_switch=int(m[3]);assert g.nodes[nid].type==kind
 if kind=='SOURCE':assert not prefix;source=nid;path=(nid,)
 elif nid in prefix and kind!='SINK':path=prefix[nid]
 else:
  assert (current,nid,switch) in arcset
  path=prefix[current]+(nid,)
 prefix[nid]=path;current=nid;switch=next_switch
 if kind=='SINK' and net in allowed:records.append({'net_id':net,'source':source,'sink':nid,'nodes':path})
assert Counter((r['net_id'],r['source'],r['sink']) for r in records)==expected
cohorts={'native':records}
for name in ('blend','own_excluded_pressure'):
 p=json.loads(Path(inputs[name]['path']).read_text());cohorts[name]=[{**r,'nodes':[r['source']]+[g.edges[eid].sink for eid in r['physical_edge_ids']]} for r in p['connections']]
 assert Counter((r['net_id'],r['source'],r['sink']) for r in cohorts[name])==expected
results={};pernets={}
for name,rows in cohorts.items():
 nets=defaultdict(list)
 for r in rows:nets[r['net_id']].append({n for n in r['nodes'] if g.nodes[n].type in {'CHANX','CHANY'}})
 bins=defaultdict(lambda:{'nets':0,'connections':0,'connection_channel_touches':0,'net_channel_touches':0});details={}
 for net,paths in nets.items():
  n=len(paths);bin='1' if n==1 else '2-4' if n<=4 else '5-16' if n<=16 else '17+'
  connection=sum(map(len,paths));union=len(set().union(*paths));item={'fanout':n,'connection_channel_touches':connection,'net_channel_touches':union,'sharing_saved':connection-union};details[str(net)]=item
  b=bins[bin];b['nets']+=1;b['connections']+=n;b['connection_channel_touches']+=connection;b['net_channel_touches']+=union
 connection=sum(x['connection_channel_touches'] for x in bins.values());union=sum(x['net_channel_touches'] for x in bins.values())
 results[name]={'connections':len(rows),'nets':len(nets),'connection_channel_touches':connection,'net_channel_touches':union,'saved_fraction':1-union/connection,'bins':dict(bins)};pernets[name]=details
(out/'per_net.json').write_text(json.dumps(pernets,indent=2)+'\n');assert all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'exact_native_and_prediction_endpoint_multisets':True,'inputs_unchanged':True,'summaries':results,'per_net_sha256':sha(out/'per_net.json')},indent=2)+'\n');print(json.dumps(results,indent=2))
