"""Load exact frozen MMC graph, export initialized indexed metadata, exit before routing."""
import json,os,subprocess,sys,time,shutil,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'build/native_indexed_cost_dump_v1_2026-10-10';O=R/'experiments/mmc_native_indexed_cost_dump_v1_2026-10-10';O.mkdir(exist_ok=False)
b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['source_sha256'].items())
bindings={**b['bindings'],**b['source_sha256'],str(B/'receipt.json'):sha(B/'receipt.json'),str(B/'sequence_vpr'):sha(B/'sequence_vpr'),str(Path(__file__).resolve()):sha(Path(__file__))}
epfile=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';ep=json.loads(epfile.read_text());bindings[str(epfile)]=sha(epfile)
assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());bindings.update({v['path']:v['sha256'] for v in ep['inputs'].values()})
source=Path(ep['inputs']['net']['path']).parent
for name in ['design.blif','design.net','design.place']:shutil.copyfile(source/name,O/name);bindings[str(O/name)]=sha(O/name)
arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';bindings[str(arch)]=sha(arch);graph=Path(ep['inputs']['graph']['path'])
command=[str(B/'sequence_vpr'),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_INDEXED_COST_DUMP']=str(O/'indexed.tsv')
(O/'startup.json').write_text(json.dumps(dict(bindings=bindings,command=command,scope='Metadata-only startup, before fanout/criticality routing.'),indent=2)+'\n')
tick=time.perf_counter()
with (O/'native.log').open('w') as log:status=subprocess.run(command,cwd=O,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
elapsed=time.perf_counter()-tick;assert status==0 and not (O/'output.route').exists()
log=(O/'native.log').read_text();assert 'ROUTECAST indexed cost metadata exported before routing' in log and 'RouterOpts.base_cost_type: DELAY_NORMALIZED_LENGTH' in log
lines=[line.split() for line in (O/'indexed.tsv').read_text().splitlines()];assert lines[0]==['G','904438','8']
indexed={int(x[1]):x for x in lines if x[0]=='I'};assert len(indexed)==8
counts=Counter({(int(x[1]),int(x[2])):int(x[3]) for x in lines if x[0]=='N'});assert sum(counts.values())==904438
xmlcounts=Counter();stack=[];segments={}
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='segments':segments={int(x.get('id')):dict(x.attrib) for x in el}
 if el.tag=='node':
  kind=el.get('type');seg=el.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
  xmlcounts[kind,sid]+=1;stack[-2].remove(el);el.clear()
 if el.tag=='rr_nodes':break
 stack.pop()
types={0:'SOURCE',1:'SINK',2:'IPIN',3:'OPIN',4:'CHANX',5:'CHANY'}
nativecounts=Counter()
for (kind,index),count in counts.items():nativecounts[types[kind],int(indexed[index][2])]+=count
assert nativecounts==xmlcounts
ratios={}
for kind in [4,5]:
 ids=[index for (t,index) in counts if t==kind];costs={int(indexed[i][2]):float(indexed[i][3]) for i in ids}
 assert set(costs)=={0,1} and abs(costs[1]/costs[0]-4)<1e-6
 ratios[types[kind]]=dict(L4_base_cost=costs[0],L16_base_cost=costs[1],L16_over_L4=costs[1]/costs[0])
for i in [4,5,6,7]:assert indexed[i][3]==indexed[i][4]
for p in [O/'indexed.tsv',O/'native.log',O/'startup.json']:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,exit_status=status,metadata_process_seconds=elapsed,indexed_rows=list(indexed.values()),segments=segments,ratios=ratios,all_904438_native_cost_index_type_segment_counts_match_original_XML=True,channel_base_equals_saved_before_fanout=True,scope='Initialized metadata before native routing. No fanout-adjusted table, connection criticality, dynamic congestion, actual route, causality or performance evidence.'),indent=2)+'\n')
print('NATIVE INDEXED COST DUMP PASS',ratios,flush=True)
