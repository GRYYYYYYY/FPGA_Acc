"""Stratify authenticated NET resource errors by fanout; posthoc diagnosis."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from prediction_metrics import spearman
root=Path(__file__).resolve().parents[1];base=root/'experiments/mux_crossbar_search_diagnosis_2026-10-06'
p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert r['protocol_sha256']==sha(base/'protocol.json');assert v['receipt_sha256']==sha(base/'receipt.json')
out=root/'experiments/mux_fanout_error_2026-10-06';out.mkdir();cases=[]
for c,row in zip(p['cases'],r['rows']):
 f=base/f"mux_w{c['data_width']}_c{c['channels']}_NETs.json";assert sha(f)==row['detail_sha256'];cases.append({'data_width':c['data_width'],'channels':c['channels'],'detail':str(f),'detail_sha256':sha(f)})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'source_sha256':sha(Path(__file__)),'scope':'Posthoc fanout strata fixed1,2-3,4-7,8+. Signed NET unique-channel error is not node-location pressure accuracy. Native32 failed attempt; legal64/128. No feedback choice or retuning.'},indent=2)+'\n');rows=[]
for c in cases:
 ss=json.loads(Path(c['detail']).read_text());groups=defaultdict(list)
 for s in ss:
  f=s['connections'];label='1' if f==1 else '2-3' if f<4 else '4-7' if f<8 else '8+'
  groups[label].append(s)
 bins={}
 for label,items in groups.items():
  pred=sum(s['predicted_unique_channels'] for s in items);native=sum(s['native_unique_channels'] for s in items)
  bins[label]={'NETs':len(items),'connections':sum(s['connections'] for s in items),'predicted_unique_channels':pred,'native_unique_channels':native,'signed_error':pred-native,'absolute_NET_error':sum(abs(s['predicted_unique_channels']-s['native_unique_channels']) for s in items),'path_sum':sum(s['predicted_channel_path_sum'] for s in items)}
 total=sum(b['absolute_NET_error'] for b in bins.values());ranked=sorted(ss,key=lambda s:(-abs(s['predicted_unique_channels']-s['native_unique_channels']),s['name']))
 row={**c,'strata':bins,'absolute_NET_error':total,'top10_absolute_error_share':sum(abs(s['predicted_unique_channels']-s['native_unique_channels']) for s in ranked[:10])/total if total else None,'fanout_vs_absolute_error_spearman':spearman([s['connections'] for s in ss],[abs(s['predicted_unique_channels']-s['native_unique_channels']) for s in ss]),'top10_NETs':[{'name':s['name'],'fanout':s['connections'],'predicted':s['predicted_unique_channels'],'native':s['native_unique_channels']} for s in ranked[:10]]}
 # Independently partition-index crosschecks against full cohort sums.
 assert sum(b['NETs'] for b in bins.values())==len(ss)
 assert sum(b['signed_error'] for b in bins.values())==sum(s['predicted_unique_channels']-s['native_unique_channels'] for s in ss)
 assert total==sum(abs(s['predicted_unique_channels']-s['native_unique_channels']) for s in ss)
 rows.append(row);print({'width':c['data_width'],'channels':c['channels'],'rho':row['fanout_vs_absolute_error_spearman'],'strata':bins},flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'scope':'Resource volume error only; does not diagnose spatial hotspots or prove causal fanout effects.'},indent=2)+'\n')
