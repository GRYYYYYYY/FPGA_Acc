"""Posthoc authenticated work counts and NET channel sharing, no policy changes."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
from prediction_metrics import spearman
root=Path(__file__).resolve().parents[1];base=root/'experiments/mux_crossbar_soft_transfer_2026-10-06';p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');out=root/'experiments/mux_crossbar_search_diagnosis_2026-10-06';out.mkdir();cases=[]
for c,row in zip(p['cases'],r['rows']):
 w=c['data_width'];ch=c['channels'];candidate=base/f'gf2_d{w}_w{ch}_soft.json';route=root/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c{ch}/design.route';cases.append({'data_width':w,'channels':ch,'endpoint':c['endpoint_path'],'candidate':str(candidate),'native_route':str(route),'bindings':{str(f):sha(f) for f in (Path(c['endpoint_path']),candidate,route)},'search_s':row['search_s']})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'source_sha256':sha(Path(__file__)),'scope':'Posthoc operationcounts/NETsharing diagnosepreviousfrozenoutcomes. expanded means Dijkstra nonstalepops,notlabelcap. Ledgercopyentryvisits reconstructed from priorNETunion occupancy,not timedprofile. Native32routefailedattempt,64/128legal; no causaloptimization/speedclaim.'},indent=2)+'\n');rows=[]
for c in cases:
 q=json.loads(Path(c['candidate']).read_text());ep=json.loads(Path(c['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];x=ET.parse(graph).getroot();kinds={int(n.get('id')):n.get('type') for n in x.find('rr_nodes')};edges=[(int(e.get('src_node')),int(e.get('sink_node'))) for e in x.find('rr_edges')];unions=defaultdict(set);channel_path_counts=Counter();stats={};ledger=Counter();copy_visits=0
 assert len(q['records'])==len(q['events'])==q['required_connections']
 for rec,event in zip(q['records'],q['events']):
  assert event['committed'] and all(rec[k]==v for k,v in event['query'].items());net=rec['net_id'];copy_visits+=len(ledger);used={rec['source']};node=rec['source']
  for eid in rec['answer']['physical_edge_ids']:
   source,node2=edges[eid];assert source==node and node2 not in used;node=node2;used.add(node)
  assert node==rec['sink'];channels={n for n in used if kinds[n] in ('CHANX','CHANY')};channel_path_counts[net]+=len(channels);ledger.update(used-unions[net]);unions[net].update(used);s=stats.setdefault(net,{'name':ep['net_names'][str(net)],'connections':0,'expanded':0});s['connections']+=1;s['expanded']+=event['expanded']
 assert dict(ledger)=={int(n):v for n,v in q['ledger'].items()}
 native=physical_paths(c['native_route']);native_union={name:{n for path in paths for n,switch in path if kinds[n] in ('CHANX','CHANY')} for name,paths in native.items()};native_sinks={name:len(paths) for name,paths in native.items()}
 for net,s in stats.items():
  assert native_sinks[s['name']]==s['connections'];s['predicted_unique_channels']=sum(kinds[n] in ('CHANX','CHANY') for n in unions[net]);s['predicted_channel_path_sum']=channel_path_counts[net];s['native_unique_channels']=len(native_union[s['name']]);s['channel_path_sum_minus_union']=s['predicted_channel_path_sum']-s['predicted_unique_channels']
 total=sum(s['expanded'] for s in stats.values());ordered=sorted(stats.values(),key=lambda s:(-s['expanded'],s['name']));detail=out/f"mux_w{c['data_width']}_c{c['channels']}_NETs.json";detail.write_text(json.dumps(ordered,indent=2)+'\n');row={'data_width':c['data_width'],'channels':c['channels'],'connections':len(q['records']),'NETs':len(stats),'RR_nodes':len(kinds),'RR_edges':len(edges),'expanded_nodes':total,'expanded_per_connection':total/len(q['records']),'ledger_copy_entry_visits':copy_visits,'search_s':c['search_s'],'fanout_vs_total_expansion_spearman':spearman([s['connections'] for s in stats.values()],[s['expanded'] for s in stats.values()]),'top10_NET_expansion_share':sum(s['expanded'] for s in ordered[:10])/total,'predicted_NET_unique_channel_sum':sum(s['predicted_unique_channels'] for s in stats.values()),'native_NET_unique_channel_sum':sum(s['native_unique_channels'] for s in stats.values()),'predicted_channel_path_sum':sum(s['predicted_channel_path_sum'] for s in stats.values()),'detail_sha256':sha(detail)};rows.append(row);assert all(sha(f)==h for f,h in c['bindings'].items());print(c['data_width'],c['channels'],'expanded',total,'copy',copy_visits,'channels',row['predicted_NET_unique_channel_sum'],row['native_NET_unique_channel_sum'],flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'scope':json.loads((out/'protocol.json').read_text())['scope']},indent=2)+'\n')
