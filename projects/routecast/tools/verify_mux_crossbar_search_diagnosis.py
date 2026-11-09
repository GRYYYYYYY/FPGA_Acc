"""Independent first-seen accounting of copy work and NET union/event sums."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_crossbar_search_diagnosis_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert sha(out/'protocol.json')==r['protocol_sha256'] and sha(root/'tools/diagnose_mux_crossbar_search.py')==p['source_sha256'];rows=[]
for c,row in zip(p['cases'],r['rows']):
 assert all(sha(f)==h for f,h in c['bindings'].items());w=c['data_width'];ch=c['channels'];q=json.loads(Path(c['candidate']).read_text());ep=json.loads(Path(c['endpoint']).read_text());x=ET.parse(ep['inputs']['graph']['path']).getroot();edges=[int(e.get('sink_node')) for e in x.find('rr_edges')];channels={int(n.get('id')) for n in x.find('rr_nodes') if n.get('type') in ('CHANX','CHANY')};first_seen={};nets=defaultdict(set);pathsum=defaultdict(int);count=defaultdict(int);expanded=defaultdict(int)
 for i,rec in enumerate(q['records']):
  used={rec['source']}|{edges[eid] for eid in rec['answer']['physical_edge_ids']}
  for n in used:first_seen.setdefault(n,i)
  net=rec['net_id'];nets[net].update(used&channels);pathsum[net]+=len(used&channels);count[net]+=1
 for event in q['events']:expanded[event['query']['net_id']]+=event['expanded']
 visits=sum(len(q['records'])-1-index for index in first_seen.values());assert visits==row['ledger_copy_entry_visits'];assert sum(expanded.values())==row['expanded_nodes'];assert sum(map(len,nets.values()))==row['predicted_NET_unique_channel_sum'];assert sum(pathsum.values())==row['predicted_channel_path_sum'];detail=out/f'mux_w{w}_c{ch}_NETs.json';assert sha(detail)==row['detail_sha256'];entries=json.loads(detail.read_text());assert len(entries)==len(count)==row['NETs'];lookup={name:int(net) for net,name in ep['net_names'].items()}
 for s in entries:
  net=lookup[s['name']];assert s['connections']==count[net] and s['expanded']==expanded[net] and s['predicted_unique_channels']==len(nets[net]) and s['predicted_channel_path_sum']==pathsum[net] and s['channel_path_sum_minus_union']==pathsum[net]-len(nets[net])
 assert row['expanded_per_connection']==sum(expanded.values())/len(q['records']);assert row['top10_NET_expansion_share']==sum(sorted(expanded.values(),reverse=True)[:10])/sum(expanded.values());rows.append({'data_width':w,'channels':ch,'copy_work_verified_by_first_seen_identity':visits,'expanded_nodes_verified':sum(expanded.values()),'NETs_verified':len(entries)});print(w,ch,'workcount verified',flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'Alternativefirst-seenidentity certifies all ledgercopyentryvisits; events/NETchannelunion/sharing/work concentration authenticated. Counts notwalltimecausalprofile; nativeunioncomparison producer-originalXMLassertion only, earliernativeauditbindingsretained.'},indent=2)+'\n')
