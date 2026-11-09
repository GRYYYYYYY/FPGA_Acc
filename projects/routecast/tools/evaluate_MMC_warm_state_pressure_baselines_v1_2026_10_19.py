"""Exposed temporal baseline, with tie-averaged mass capture and no training."""
import pathlib,json,hashlib,sys,math,xml.etree.ElementTree as ET
from collections import Counter
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pressure_prefix_feature_contract_v1 import load as feature_load
from prediction_metrics import spearman
from pressure_prefix_interval_contract_v1 import load as interval_load
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def histogram_rho(p,t):
 joint=Counter(zip(p,t));a=Counter(p);b=Counter(t);n=len(p)
 def ranks2(counts):
  offset=0;result={}
  for v,c in sorted(counts.items()):result[v]=2*offset+c-1;offset+=c
  return result
 x,y=ranks2(a),ranks2(b);mean=n-1;cov=sum(c*(x[u]-mean)*(y[v]-mean) for (u,v),c in joint.items());xx=sum(c*(x[v]-mean)**2 for v,c in a.items());yy=sum(c*(y[v]-mean)**2 for v,c in b.items());return cov/math.sqrt(xx*yy) if xx and yy else None

def main():
 out=R/'experiments/mmc_warm_state_pressure_baselines_v1_2026-10-19';protocol=out/'protocol.json';spec=json.loads(protocol.read_text());assert all(sha(p)==h for p,h in spec['bindings'].items());root=R/'experiments/mmc_prefix_future_pressure_split_v1_2026-10-18';split=json.loads((root/'verification.json').read_text());ep=json.loads(pathlib.Path(spec['endpoint']).read_text());graph=pathlib.Path(ep['inputs']['graph']['path']);domain=[];stack=[]
 for event,node in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(node);continue
  if node.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if node.get('type') in ['CHANX','CHANY'] and int(node.get('capacity'))>0:domain.append(int(node.get('id')))
   stack[-2].remove(node);node.clear()
  if node.tag=='rr_nodes':break
  stack.pop()
 assert len(domain)==len(set(domain))==258720;domain.sort();k=len(domain)//20;dp=out/'channel_domain.json';dp.write_text(json.dumps(domain)+'\n');rows=[];checked=0
 sourceproof=json.loads(pathlib.Path(spec['source_proof']).read_text());sourcepath=pathlib.Path(spec['source_frame']);assert sourceproof['all_native_paths_exact'] and sourceproof['all_uniqueNET_occupancy_matches_full_printed_audit'];assert sourceproof['bindings'][str(sourcepath)]==sha(sourcepath);assert any(h==ep['graph_sha256'] and name.endswith('rr_graph.xml') for name,h in sourceproof['bindings'].items());source_frame=json.loads(sourcepath.read_text());source_ledger={int(n):v for n,v in source_frame['ledger'].items()};source_scores=[source_ledger.get(n,0) for n in domain]
 for row in split['cases']:
  case,policy=row['case'],row['policy'];warmfile=R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained/initial.json';assert spec['bindings'][str(warmfile)]==sha(warmfile);warm=json.loads(warmfile.read_text());assert warm['graph_sha256']==ep['graph_sha256'] and warm['completed_connections']==warm['required_connections']==115572;warmledger={int(n):x for n,x in warm['ledger'].items()};warm_scores=[warmledger.get(n,0) for n in domain];folder=root/f'{case}_{policy}';first=feature_load(folder/'features.json',row['feature_sha256']);prediction=[first.get(n,0) for n in domain];mp=R/f'experiments/mmc_first_checkpoint_occupancy_bounds_v1_2026-10-19/{case}_{policy}/features.json';assert spec['bindings'][str(mp)]==sha(mp);caps,intervals=interval_load(mp,spec['bindings'][str(mp)]);assert all(caps[n]==1 for n in domain);lower=[intervals['lower_occupancy'][n] for n in domain];pp=out/f'{case}_{policy}_prediction.json';pp.write_text(json.dumps({'domain_sha256':sha(dp),'predictions':{'prefix_overflow':prediction,'capacity_lower_bound':lower,'previous_native_occupancy':source_scores,'warm_initial_sketch_demand':warm_scores}},separators=(',',':'))+'\n')
  # Only now read future target values.
  assert sha(folder/'targets.json')==row['target_sha256'];future=json.loads((folder/'targets.json').read_text());assert future['first_target_iteration']==2;summary={}
  for target,raw in future['targets'].items():
   truth={int(n):v for n,v in raw.items()};t=[truth.get(n,0) for n in domain];total=sum(t);assert total>0;summary[target]={}
   for method,p in [('warm_initial_sketch_demand',warm_scores),('capacity_lower_bound',lower),('prefix_overflow',prediction),('previous_native_occupancy',source_scores),('uniform_risk',[1]*len(domain))]:
    rho=spearman(p,t);ind=histogram_rho(p,t);assert rho==ind if rho is None else abs(rho-ind)<1e-12;checked+=1;order=sorted(range(len(domain)),key=lambda i:(-p[i],domain[i]));boundary=p[order[k-1]];above=[i for i,v in enumerate(p) if v>boundary];tie=[i for i,v in enumerate(p) if v==boundary];slots=k-len(above);base=sum(t[i] for i in above);tie_mass=sum(t[i] for i in tie);average=(Fraction(base)+Fraction(slots*tie_mass,len(tie)))/total;fixed=Fraction(sum(t[i] for i in order[:k]),total);expected=Fraction(k,len(domain));metric=dict(spearman=rho,k=k,tie_averaged_mass_capture=str(average),fixed_ID_mass_capture=str(fixed),uniform_expected_mass_capture=str(expected),enrichment_over_uniform=float(average/expected),prediction_boundary_tie_nodes=len(tie),selected_from_boundary_tie=slots,full_domain_target_mass=total,total_target_mass_all_RR=sum(truth.values()),positive_target_channels=sum(v>0 for v in t));summary[target][method]=metric
    if method=='uniform_risk':assert average==expected
  primary=summary['sum_checkpoint_overflow_units']['warm_initial_sketch_demand'];references=[summary['sum_checkpoint_overflow_units'][name] for name in ['prefix_overflow','previous_native_occupancy','capacity_lower_bound']];signal=all(Fraction(primary['tie_averaged_mass_capture'])>=Fraction(reference['tie_averaged_mass_capture']) and primary['spearman'] is not None and reference['spearman'] is not None and primary['spearman']>=reference['spearman']-1e-12 and (Fraction(primary['tie_averaged_mass_capture'])>Fraction(reference['tie_averaged_mass_capture']) or primary['spearman']>reference['spearman']+1e-12) for reference in references);rows.append(dict(case=case,policy=policy,metrics=summary,diagnostic_future_signal=signal,prediction_sha256=sha(pp)));print(case,policy,signal,primary['enrichment_over_uniform'],flush=True)
 assert all(sha(p)==h for p,h in spec['bindings'].items());result=dict(status='six_exposed_warm_state_future_baseline_cases_evaluated',protocol_sha256=sha(protocol),domain_sha256=sha(dp),cases=rows,independent_histogram_metric_vectors=checked,all6_diagnostic_signal=all(r['diagnostic_future_signal'] for r in rows),scope=spec['scope'],trained_model=False,accepted_gain=False,strict_unseen_admitted=False);(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
