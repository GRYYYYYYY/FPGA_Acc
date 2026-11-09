"""Independently derive delta footprints/edge visits from frozen whole-case tables."""
import json,statistics,math
from pathlib import Path
from collections import Counter
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_incremental_endpoint_signals_v1_2026-10-20';S=E/'wbuart_endpoint_graph_signals_v1_2026-10-20';H=E/'wbuart_preroute_heterograph_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def main():
 p=D/'verification.json';v=read(p);assert len(v['rows'])==18 and not v['target_labels_read'];assert all(sha(name)==h for name,h in v['bindings'].items());signal=read(S/'verification.json');tables={};graphs={};rows=[]
 for r in signal['rows']:tables[r['case']]={item['RR']:item['values'] for item in lines(r['feature_file'])}
 for row in v['rows']:
  width=row['width'];a=width+'/'+row['source_episode'];b=width+'/'+row['target_episode'];source,target=tables[a],tables[b];info=next(r for r in signal['rows'] if r['case']==a)
  if width not in graphs:
   gd=H/'graphs'/info['graph_sha256'];incoming=Counter();outgoing=Counter();edges=lines(gd/'physical_edges.jsonl')
   for edge in edges:outgoing[edge['source']]+=1;incoming[edge['sink']]+=1
   channels={item['id'] for item in lines(gd/'RR_nodes.jsonl') if item['type'] in ['CHANX','CHANY']};graphs[width]=(incoming,outgoing,len(edges),channels)
  incoming,outgoing,edges,channels=graphs[width];changed={n for n in source if source[n]!=target[n]};visits=sum(outgoing[n] for n in source if source[n][:3]!=target[n][:3])+sum(outgoing[n] for n in source if source[n][5:8]!=target[n][5:8])+sum(incoming[n] for n in source if source[n][3:5]!=target[n][3:5])+sum(incoming[n] for n in source if source[n][11:13]!=target[n][11:13]);assert row['changed_RRs']==len(changed) and row['changed_CHANNELs']==len(changed&channels) and row['all_CHANNELs']==len(channels) and row['delta_edge_visits']==visits and row['full_edge_visits']==4*edges
  assert row['all_integer_features_equal'] and row['all_frozen_probabilities_bit_equal'];times=row['feature_ABBA_timings'];assert [r['mode'] for r in times]==['incremental','full','full','incremental']*2 and all(math.isfinite(r['seconds']) and r['seconds']>0 for r in times);inc=statistics.median(r['seconds'] for r in times if r['mode']=='incremental');full=statistics.median(r['seconds'] for r in times if r['mode']=='full');assert inc==row['incremental_feature_median_seconds'] and full==row['full_feature_median_seconds'];rows.append({'width':width,'source_episode':row['source_episode'],'target_episode':row['target_episode'],'changed_CHANNEL_fraction':row['changed_CHANNELs']/len(channels),'edge_visit_fraction':visits/(4*edges),'full_over_incremental_feature_median':full/inc,'incremental_feature_faster':inc<full})
 assert len({(r['width'],r['source_episode'],r['target_episode']) for r in rows})==18
 out=D/'independent_review_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL18_DELTA_FOOTPRINTS_EDGE_VISITS_AND_ABBA_STATISTICS_VERIFIED','rows':rows,'faster_component_transitions':sum(r['incremental_feature_faster'] for r in rows),'feature_full_over_incremental_median_range':[min(r['full_over_incremental_feature_median'] for r in rows),max(r['full_over_incremental_feature_median'] for r in rows)],'changed_CHANNEL_fraction_range':[min(r['changed_CHANNEL_fraction'] for r in rows),max(r['changed_CHANNEL_fraction'] for r in rows)],'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__),str(S/'verification.json'):sha(S/'verification.json')},'scope':'Independent frozen-table delta support and linear-frontier edge accounting; actual state transitions also checked against independently qualified whole-case tables and bit-identical frozen inference. Repeated timings measure resident feature component only; exclude cache acquisition/input parsing/NET diff. No end-to-end, native, quality or unseen-family gain.'},indent=2)+'\n');print('INCREMENTAL_COMPONENT_REVIEW',sum(r['incremental_feature_faster'] for r in rows),len(rows))
if __name__=='__main__':main()
