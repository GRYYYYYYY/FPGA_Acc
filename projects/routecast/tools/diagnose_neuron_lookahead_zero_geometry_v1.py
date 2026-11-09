"""Full explicit-pin join of initialized lookahead values, proxy floors and RR endpoint geometry."""
import hashlib,json,math,resource,struct,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*2**30,2*2**30))
 cap=R/'experiments/neuron_initial_lookahead_snapshot_v1_2026-10-17';proof=json.loads((cap/'lookahead_verification.json').read_text());assert proof['all_pass']
 for p,h in proof['bindings'].items():assert sha(Path(p))==h
 assert json.loads((cap/'terminal.json').read_text())['exit_status']==0
 initial=R/'experiments/neuron_quotient_astar_pipeline_v1_2026-10-17/model/initial.json'
 mp=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json'
 records=json.loads(initial.read_text())['records'];manifest=json.loads(mp.read_text());bycid={x['connection_id']:x for x in records};pins={(x['net'],x['local_sink_pin']):x for x in manifest}
 assert len(bycid)==len(pins)==77106 and set(bycid)==set(range(77106))
 ids=set()
 for x in manifest:
  o=bycid[x['connection_id']];assert (x['net'],x['source_rr'],x['target_rr'])==(o['net_id'],o['source'],o['sink']);ids.update([o['source'],o['sink']])
 graph=R/'experiments/titan23_neuron_graph_recovery_v1_2026-10-13/neuron/rr_graph.xml';nodes={};node_count=0
 for event,e in ET.iterparse(graph,events=['end']):
  if e.tag=='node':
   node_count+=1;n=int(e.attrib['id'])
   if n in ids:
    loc=e.find('loc');nodes[n]=dict(type=e.attrib['type'],**{k:int(loc.attrib[k]) for k in ['xlow','xhigh','ylow','yhigh']})
   e.clear()
  elif e.tag=='rr_nodes':break
 assert set(nodes)==ids
 counts=Counter();seen=set();examples=[]
 for seq,line in enumerate((cap/'work/lookahead_delay.tsv').open(),1):
  p=line.strip().split('\t');assert p[0]=='D' and int(p[1])==seq
  m=pins[(int(p[2]),int(p[4]))];cid=m['connection_id'];assert cid not in seen and m['global_pin']==int(p[3]);seen.add(cid)
  o=bycid[cid];v=struct.unpack('<f',int(p[6],16).to_bytes(4,'little'))[0];assert math.isfinite(v) and v>=0
  a,b=nodes[o['source']],nodes[o['sink']];dx=max(0,a['xlow']-b['xhigh'],b['xlow']-a['xhigh']);dy=max(0,a['ylow']-b['yhigh'],b['ylow']-a['yhigh']);d=dx+dy
  kind='zero' if v==0 else 'positive';counts[kind]+=1;counts[kind+'/floor_zero' if o['floor_integer']==0 else kind+'/floor_positive']+=1
  counts[kind+'/overlapping_xy' if d==0 else kind+'/separated_xy']+=1;counts[kind+'/'+a['type']+'->'+b['type']]+=1
  if v==0 and o['floor_integer']>0 and d>0 and len(examples)<10:examples.append(dict(cid=cid,net=o['net_id'],local_sink_pin=m['local_sink_pin'],source=o['source'],sink=o['sink'],minimum_box_manhattan=d,floor_integer=o['floor_integer']))
 assert len(seen)==77106 and counts['zero']==76968 and counts['positive']==138
 vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route'
 files=[Path(__file__).resolve(),cap/'lookahead_verification.json',cap/'work/lookahead_delay.tsv',initial,mp,graph,vendor/'route_common.cpp',vendor/'router_lookahead_map.cpp',vendor/'router_lookahead_map_utils.cpp']
 bindings={str(p):sha(p) for p in files}
 out=R/'experiments/neuron_lookahead_zero_geometry_v1_2026-10-17';out.mkdir()
 result=dict(all_pass=True,all_explicit_connection_identities=77106,rr_nodes_scanned=node_count,unique_endpoint_nodes=len(nodes),counts=dict(counts),examples=examples,bindings=bindings,source_findings=['get_cost_from_lookahead delegates to router lookahead expected cost.','SOURCE/OPIN map takes minimum across reachable segments and layers.','Empty source map returns huge finite delay, not zero.','A reachable SINK special entry uses zero downstream cost and adds reachable_wire_inf.delay.'],scope='Observed zero/geometry/floor association only. Does not identify the actual chosen map entry or establish zero-delay cause; no labels, new model, budgets, routing settings or vendor source changed.',promoted=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['all_pass','rr_nodes_scanned','unique_endpoint_nodes','counts']},indent=2))
if __name__=='__main__':main()
