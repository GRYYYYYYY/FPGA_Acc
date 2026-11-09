"""All18 within-width layout transitions, exact feature/probability and ABBA checks."""
import json,time,math,statistics
from pathlib import Path
from collections import defaultdict
from array import array
from incremental_endpoint_graph_signals_v1 import State
from endpoint_graph_signals_v1 import extract
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_incremental_endpoint_signals_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def probability(row,model):
 z=model['weights'][0]+sum(model['weights'][j+1]*(x-model['mean'][j])/model['std'][j] for j,x in enumerate(row));return 1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z))
def main():
 D.mkdir(exist_ok=False);H=E/'wbuart_preroute_heterograph_v1_2026-10-20';S=E/'wbuart_endpoint_graph_signals_v1_2026-10-20';L=E/'wbuart_graph_signal_learning_v1_2026-10-20';contract=E/'incremental_endpoint_signals_contract_v1_2026-10-20/verification.json';proofs=[contract,S/'independent_verification_v1.json',L/'independent_verification_v1.json']
 for p in proofs:assert all(sha(name)==h for name,h in read(p)['bindings'].items())
 features=read(E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json');signals=read(S/'verification.json');bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/incremental_endpoint_graph_signals_v1.py',*proofs,S/'verification.json',E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json',L/'predictions_frozen.json']};(D/'protocol.json').write_text(json.dumps({'transitions':'All six ordered distinct episode pairs in each of three fixed widths,18 total; no labels loaded.','benchmark_order':['incremental','full','full','incremental']*2,'timing_scope':'Matched resident integer feature update/rebuild only. Graph/NET construction, input parsing, source native acquisition and feature/probability audits are separate. Incremental starts from cached source state and prepared changed-NET input. No whole routing/native/end-to-end gain claim.','inference':'Use existing target-episode frozen main model and its fixed train-only transform. Recompute only changed CHANNEL rows, keep remaining source scores; require bit-identical target full prediction. Fixed model is shared for both layouts, no refit.','bindings':bindings},indent=2)+'\n');outputs=[];predictions=read(L/'predictions_frozen.json')['rows']
 for width in ['w096','w128','w160']:
  info=next(r for r in signals['rows'] if r['case'].startswith(width+'/'));gd=H/'graphs'/info['graph_sha256'];ids=[r['id'] for r in lines(gd/'RR_nodes.jsonl')];edges=[(e['source'],e['sink']) for e in lines(gd/'physical_edges.jsonl')];cases={}
  for ep in ['episode_01','episode_02','episode_03']:
   case=width+'/'+ep;row=next(r for r in signals['rows'] if r['case']==case);nets={r['net_id']:r for r in lines(Path(row['directory'])/'NET_features.jsonl')};queries=lines(Path(row['directory'])/'NET_RR_incidence.jsonl');groups=defaultdict(list)
   for q in queries:groups[q['net_id']].append(q)
   feature=next(r for r in features['rows'] if r['case']==case);a=array('d');a.frombytes(Path(feature['matrix']).read_bytes());resource_ids=read(feature['resource_ids']);raw={n:list(a[i*26:(i+1)*26]) for i,n in enumerate(resource_ids)};expected={r['RR']:r['values'] for r in lines(row['feature_file'])};cases[ep]={'case':case,'NETs':nets,'queries':queries,'groups':groups,'raw':raw,'expected':expected,'resource_ids':resource_ids}
  for source_ep,source in cases.items():
   for target_ep,target in cases.items():
    if source_ep==target_ep:continue
    start=time.perf_counter();state=State(ids,edges,source['queries'],source['NETs']);setup=time.perf_counter()-start;assert state.values==source['expected'];changed=[n for n in target['NETs'] if target['NETs'][n]!=source['NETs'][n] or target['groups'][n]!=source['groups'][n]];upserts={n:{'queries':target['groups'][n],'feature':target['NETs'][n]} for n in changed};rollback={n:{'queries':source['groups'][n],'feature':source['NETs'][n]} for n in changed};times=[];last=None
    for mode in ['incremental','full','full','incremental']*2:
     if mode=='incremental':
      tick=time.perf_counter();last=state.update(upserts,[],state.epoch,state.epoch+1);seconds=time.perf_counter()-tick;assert state.values==target['expected'];state.update(rollback,[],state.epoch,state.epoch+1);assert state.values==source['expected']
     else:
      tick=time.perf_counter();reference=extract(ids,edges,target['queries'],target['NETs']);seconds=time.perf_counter()-tick;assert reference==target['expected']
     times.append({'mode':mode,'seconds':seconds})
    last=state.update(upserts,[],state.epoch,state.epoch+1);assert state.values==target['expected'];model_row=next(r for r in predictions if r['case']==target['case'] and r['mode']=='main');model=read(model_row['model']);cached={n:probability(row,model) for n,row in source['raw'].items()};expected=read(model_row['probabilities']);changed_channels=sorted(set(last['changed_RRs'])&set(cached));tick=time.perf_counter()
    for n in changed_channels:
     row=source['raw'][n][:11]+[math.log1p(v) for v in state.values[n]];cached[n]=probability(row,model)
    incremental_inference=time.perf_counter()-tick;assert all(source['raw'][n][:11]==target['raw'][n][:11] for n in cached);assert [cached[n] for n in target['resource_ids']]==expected
    tick=time.perf_counter();full_scores=[probability(target['raw'][n],model) for n in target['resource_ids']];full_inference=time.perf_counter()-tick;assert full_scores==expected
    row={'width':width,'source_episode':source_ep,'target_episode':target_ep,'changed_NETs':len(changed),'changed_RRs':len(last['changed_RRs']),'changed_CHANNELs':len(changed_channels),'all_CHANNELs':len(cached),'delta_edge_visits':last['edge_visits'],'full_edge_visits':4*len(edges),'source_cache_setup_seconds':setup,'feature_ABBA_timings':times,'incremental_feature_median_seconds':statistics.median(r['seconds'] for r in times if r['mode']=='incremental'),'full_feature_median_seconds':statistics.median(r['seconds'] for r in times if r['mode']=='full'),'incremental_inference_seconds':incremental_inference,'full_inference_seconds':full_inference,'all_integer_features_equal':True,'all_frozen_probabilities_bit_equal':True};outputs.append(row);print('INCREMENTAL_LAYOUT_VERIFIED',width,source_ep,target_ep,len(changed_channels),len(cached),flush=True)
    for p in [Path(model_row['model']),Path(model_row['probabilities'])]:bindings[str(p)]=sha(p)
 assert len(outputs)==18
 (D/'verification.json').write_text(json.dumps({'status':'ALL18_LAYOUT_DELTA_FEATURES_AND_FROZEN_PREDICTIONS_EXACT_WITH_ABBA_MEASUREMENTS','rows':outputs,'bindings':bindings,'target_labels_read':False,'quality_gate_passes_unchanged':0,'scope':'Cached fixed-graph resident feature/inference component experiment only. Upstream raw matrices already archived; cache acquisition, NET-diff detection, parsing and native costs are not in component timings. Inference single pairs not balanced performance evidence; only feature ABBA is repeated. No quality/native/fullpaid/family success.'},indent=2)+'\n')
if __name__=='__main__':main()
