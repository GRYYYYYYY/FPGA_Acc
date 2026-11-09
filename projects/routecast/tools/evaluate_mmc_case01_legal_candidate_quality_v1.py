"""Score a frozen full-capacity candidate on the unchanged exposed cold domain."""
import json,time,xml.parsers.expat as X
from pathlib import Path
from array import array
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
from prediction_metrics import compare
from verify_MMC_complete_static_criticality_metrics_v2_2026_10_19 import verify_metric
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_case01_legal_candidate_quality_v1_2026-10-21';D.mkdir(exist_ok=False);M=R/'experiments/mmc_expanded40_joint_CBS_v1_2026-10-21/case01_full_candidate_verification_v1.json';m=json.loads(M.read_text());assert all(sha(p)==h for p,h in m['bindings'].items());assert m['overused_CHANNELs']==0 and m['all_selected_paths_original_budget_qualified'];P=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(P.read_text());item=next(r for r in plan['cases'] if r['case']=='case_01');graph=Path(json.loads(Path(item['endpoint']).read_text())['inputs']['graph']['path']);bindings={str(p):sha(p) for p in [M,P,graph,Path(__file__),R/'tools/prediction_metrics.py',R/'tools/verify_MMC_complete_static_criticality_metrics_v2_2026_10_19.py']}
(D/'protocol.json').write_text(json.dumps({'candidate_manifest':str(M),'candidate_sha256':sha(M),'cases':['case_01'],'metrics':['concrete_spearman','concrete_precision_at12936','spatial_spearman','spatial_precision_at20'],'controls':['previous_native','raw_min_on'],'decision':'All four nonregress and at least one strict versus each control, same existing full-domain zeros/ties convention. This is one exposed-case necessary diagnostic, not original full9 acceptance or all3 success. No label-based candidate adjustment.','bindings':bindings},indent=2)+'\n')
start=time.perf_counter();stack=[];channels={};bins=Counter();dest=array('I');current=None;loc=None;segment=-1

def begin(tag,a):
 global current,loc,segment
 parent=stack[-1] if stack else None;stack.append(tag)
 if tag=='node' and parent=='rr_nodes':current=dict(a);loc=None;segment=-1
 elif tag=='loc' and parent=='node':loc=dict(a)
 elif tag=='segment' and parent=='node':segment=int(a['segment_id'])
 elif tag=='edge' and parent=='rr_edges':dest.append(int(a['sink_node']))
def end(tag):
 if tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes' and current['type'] in ['CHANX','CHANY'] and int(current['capacity'])>0:
  cap=int(current['capacity']);keys=[(int(loc.get('layer',0)),x,y,current['type'],segment) for x in range(int(loc['xlow']),int(loc['xhigh'])+1) for y in range(int(loc['ylow']),int(loc['yhigh'])+1)];channels[int(current['id'])]=(cap,keys)
  for k in keys:bins[k]+=cap
 assert stack.pop()==tag
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while b:=f.read(8*1024*1024):parser.Parse(b,False)
parser.Parse(b'',True);assert len(channels)==258720 and len(bins)==17160
bankpath=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/case_01/banks.jsonl';frozenpath=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';frozen=json.loads(frozenpath.read_text());assert sha(bankpath)==frozen['bindings'][str(bankpath)];pickB=set(m['unextended_pick_B_NETs']);extended={int(n):p for n,p in m['extended_tree_paths'].items()};ledger=Counter()
for bank in map(json.loads,bankpath.open()):
 if bank['net_id'] not in extended:ledger.update(bank['B'] if bank['net_id'] in pickB else bank['A'])
for net,path in extended.items():
 r=json.loads(Path(path).read_text());owned={n for q in r['connections'] for n in [q['source'],*(dest[e] for e in q['physical_edge_ids'])]};ledger.update(owned)
assert all(ledger[n]<=cap for n,(cap,keys) in channels.items());lp=D/'frozen_candidate_ledger.json';lp.write_text(json.dumps(dict(ledger),separators=(',',':'))+'\n');bindings.update({str(p):sha(p) for p in [bankpath,frozenpath,lp]})
# Target label access starts only after manifest, protocol and prediction ledger freeze.
label=Path(item['native_label']);labeldoc=json.loads(label.read_text());truth={int(n):v for n,v in labeldoc['node_occupancy'].items()};quality=Path(item['quality_reference_protocol']).with_name('comparison.json');qv=quality.with_name('verification.json');proof=json.loads(qv.read_text());assert proof['status']=='pass' and proof['bindings'][str(quality)]==sha(quality);prior=json.loads(quality.read_text());assert prior['bindings'][str(label)]==sha(label)
sp,st=Counter(),Counter()
for n,(cap,keys) in channels.items():
 assert truth.get(n,0)<=cap
 for k in keys:sp[k]+=ledger[n];st[k]+=truth.get(n,0)
vectors={'concrete':({n:Fraction(ledger[n],cap) for n,(cap,keys) in channels.items()},{n:Fraction(truth.get(n,0),cap) for n,(cap,keys) in channels.items()},12936),'spatial':({k:Fraction(sp[k],cap) for k,cap in bins.items()},{k:Fraction(st[k],cap) for k,cap in bins.items()},20)};metrics={}
for scope,(prediction,target,k) in vectors.items():metrics[scope]=compare(prediction,target,k);verify_metric(prediction,target,k,metrics[scope])
comparisons={}
for control in ['previous_native','raw_min_on']:
 checks=[]
 for scope in vectors:
  for metric in ['spearman','precision_at_k']:
   candidate=metrics[scope][metric];reference=prior['metrics']['cold'][control][scope][metric];eps=1e-12 if metric=='spearman' else 0;checks.append({'scope':scope,'metric':metric,'candidate':candidate,'reference':reference,'nonregression':candidate is not None and reference is not None and candidate>=reference-eps,'strict':candidate is not None and reference is not None and candidate>reference+eps})
 comparisons[control]={'checks':checks,'necessary_comparison_pass':all(c['nonregression'] for c in checks) and any(c['strict'] for c in checks)}
bindings.update({str(p):sha(p) for p in [label,quality,qv,D/'protocol.json']});assert all(sha(p)==h for p,h in bindings.items());out={'status':'FROZEN_CASE01_FULL_CHANNEL_CAPACITY_CANDIDATE_COLD_QUALITY_SCORED','metrics':metrics,'comparisons':comparisons,'necessary_case01_gate_pass':all(c['necessary_comparison_pass'] for c in comparisons.values()),'original_full9_gate_pass':False,'all3_capacity_pass':False,'strict_unseen':0,'seconds':time.perf_counter()-start,'independent_numerical_crosscheck':'Histogram ranks, exact topK and MAE routine verified both metric vectors in evaluator; independent physical full-design verification inherited from frozen manifest.','bindings':bindings,'scope':'One already exposed case, cold label, unchanged full concrete/spatial universes. Neither full9/all3 prediction acceptance, native utility, cost acceptance nor unseen evidence.'};(D/'results.json').write_text(json.dumps(out,indent=2,default=lambda x:str(x) if isinstance(x,Fraction) else None)+'\n');print(json.dumps(comparisons,indent=2),flush=True)
