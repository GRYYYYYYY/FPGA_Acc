"""Frozen-path telescoping of concrete errors; intermediate states not legalized."""
import json,time,xml.parsers.expat as X
from pathlib import Path
from array import array
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
from prediction_metrics import compare
R=Path(__file__).resolve().parents[1];D=R/'experiments/joint_capacity_stage_attribution_v1_2026-10-21';D.mkdir(exist_ok=False);M=R/'experiments/mmc_expanded40_joint_CBS_v1_2026-10-21/case01_full_candidate_verification_v1.json';m=json.loads(M.read_text());assert all(sha(p)==h for p,h in m['bindings'].items());Q=R/'experiments/mmc_case01_legal_candidate_quality_v1_2026-10-21/results.json';q=json.loads(Q.read_text());P=R/'experiments/mmc_all_NET_feedback_quality_v1_2026-10-18/case_01/protocol.json';prior_protocol=json.loads(P.read_text());priorp=P.with_name('comparison.json');prior=json.loads(priorp.read_text());bankpath=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/case_01/banks.jsonl';frozenp=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';assert sha(bankpath)==json.loads(frozenp.read_text())['bindings'][str(bankpath)];S=R/'experiments/mmc_cover_plus151_residual_v1_2026-10-21';V=S/'verification.json';old=json.loads(V.read_text());graph=next(Path(p) for p in q['bindings'] if p.endswith('.xml'));bindings={str(p):sha(p) for p in [M,Q,P,priorp,bankpath,frozenp,V,graph,Path(__file__),R/'tools/prediction_metrics.py']}
(D/'protocol.json').write_text(json.dumps({'stages':['previous_native','all_A','final_unextended_AB_extended_A','initial37_C_plus_final_unextended_AB_new191_A','final_capacity_candidate'],'order':'Fixed construction history decomposition, not chosen by labels. Final unextended A/B choices frozen; all extended slots start at A, then original C, then final audited trees.','scope':'Concrete complete-domain diagnostic only, same zero/tie and K12936. Intermediates may overuse capacity. Telescoping differences depend on order, not causal single-NET effects or feasible interventions. No metric gate replacement or candidate adjustment.','bindings':bindings},indent=2)+'\n');start=time.perf_counter();dest=array('I');channels=set();stack=[]
def begin(tag,a):
 parent=stack[-1] if stack else None;stack.append(tag)
 if tag=='node' and parent=='rr_nodes' and a['type'] in ['CHANX','CHANY'] and int(a['capacity'])>0:assert int(a['capacity'])==1;channels.add(int(a['id']))
 elif tag=='edge' and parent=='rr_edges':dest.append(int(a['sink_node']))
def end(tag):assert stack.pop()==tag
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while b:=f.read(8*1024*1024):parser.Parse(b,False)
parser.Parse(b'',True);assert len(channels)==258720
banks={b['net_id']:(set(b['A'])&channels,set(b['B'])&channels) for b in map(json.loads,bankpath.open())};assert len(banks)==55300;extended={int(n):p for n,p in m['extended_tree_paths'].items()};pickB=set(m['unextended_pick_B_NETs']);a_ledger=Counter(n for aa,bb in banks.values() for n in aa);selected=Counter(n for net,(aa,bb) in banks.items() for n in (bb if net in pickB else aa));current=dict((net,bb if net in pickB else aa) for net,(aa,bb) in banks.items());root=selected.copy()
def support(r):
 assert r['all_connections_within_budget'];return {n for q in r['connections'] for n in [q['source'],*(dest[e] for e in q['physical_edge_ids'])]}&channels
for item in old['rows']:
 if item['case']!='case_01':continue
 p=Path(item['result']);assert sha(p)==old['files'][str(p)];bindings[str(p)]=sha(p);r=json.loads(p.read_text());net=r['net_id'];replacement=support(r);root.subtract(current[net]);root.update(replacement);current[net]=replacement
final=root.copy()
for net,path in extended.items():
 p=Path(path);assert sha(p)==m['bindings'][str(p)];r=json.loads(p.read_text());replacement=support(r);final.subtract(current[net]);final.update(replacement);current[net]=replacement
lp=R/'experiments/mmc_case01_legal_candidate_quality_v1_2026-10-21/frozen_candidate_ledger.json';expected={int(n):v for n,v in json.loads(lp.read_text()).items()};assert all(final[n]==expected.get(n,0) for n in channels);bindings[str(lp)]=sha(lp)
# Existing evaluation labels are used only after fixed intermediate construction.
oldp=Path(prior_protocol['predictions']['previous_native']);label=Path(prior_protocol['labels']['cold']);assert prior['bindings'][str(oldp)]==sha(oldp) and prior['bindings'][str(label)]==sha(label);previous={int(n):v for n,v in json.loads(oldp.read_text())['ledger'].items()};truth={int(n):v for n,v in json.loads(label.read_text())['node_occupancy'].items()};target={n:Fraction(truth.get(n,0)) for n in channels};rows=[];stages=[('previous_native',previous),('all_A',a_ledger),('final_unextended_AB_extended_A',selected),('initial37_C_plus_final_unextended_AB_new191_A',root),('final_capacity_candidate',final)]
for name,ledger in stages:
 assert all(ledger.get(n,0)>=0 for n in channels);pred={n:Fraction(ledger.get(n,0)) for n in channels};metric=compare(pred,target,12936);error=sum(abs(ledger.get(n,0)-truth.get(n,0)) for n in channels);rows.append({'stage':name,'concrete_metrics':metric,'L1_error_units':error,'owned_CHANNEL_units':sum(ledger.get(n,0) for n in channels),'overflow_CHANNEL_units':sum(max(0,ledger.get(n,0)-1) for n in channels),'L1_error_delta_from_preceding':error-rows[-1]['L1_error_units'] if rows else 0});print('STAGE',name,'error',error,'overflow',rows[-1]['overflow_CHANNEL_units'],flush=True)
for name,reference in [('previous_native',prior['metrics']['cold']['previous_native']['concrete']),('final_capacity_candidate',q['metrics']['concrete'])]:
 actual=next(r['concrete_metrics'] for r in rows if r['stage']==name);assert abs(actual['spearman']-reference['spearman'])<1e-12 and actual['precision_at_k']==reference['precision_at_k']
assert rows[-1]['L1_error_units']-rows[0]['L1_error_units']==199 and sum(r['L1_error_delta_from_preceding'] for r in rows)==199;bindings.update({str(p):sha(p) for p in [oldp,label,D/'protocol.json']});assert all(sha(p)==h for p,h in bindings.items());out={'status':'FIXED_CONSTRUCTION_ORDER_CONCRETE_ERROR_TELESCOPING_VERIFIED','rows':rows,'error_change_previous_to_final':199,'seconds':time.perf_counter()-start,'bindings':bindings,'scope':'Exposed case01, concrete resources. Exact frozen construction accounting only; intermediate overflow is shown and these are not feasible counterfactuals. No learned selector, label-based rerouting, full9 gate improvement, causal attribution or gain.'};(D/'results.json').write_text(json.dumps(out,indent=2,default=lambda x:str(x) if isinstance(x,Fraction) else None)+'\n')
