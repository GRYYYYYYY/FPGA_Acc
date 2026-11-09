"""Bounded target-using aggregate objective diagnostic, not an admitted forecast."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from coordinate_NET_aggregate_L1_v1 import select
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from verify_wbuart_map_priority_metrics_v1 import scores
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_joint_aggregate_L1_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_best_support_ranking_v1_2026-10-20/verification.json';contract=E/'coordinate_NET_aggregate_L1_contract_v1_2026-10-20/verification.json';assert all(sha(p)==h for p,h in read(contract)['bindings'].items());files=[Path(__file__),R/'tools/coordinate_NET_aggregate_L1_v1.py',source,source.parent/'independent_verification_v1.json',contract,E/'wbuart_recorded_pool_capacity_v1_2026-10-20/interpretation_v1.json'];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'status':'FROZEN_ALL72_BOUNDED_LABEL_DEPENDENT_JOINT_AGGREGATE_DIAGNOSTIC','objective':'Exact sum_CHANNEL |aggregate distinctNET count - fixed target count|. Same recorded complete candidate supports; deduplicate CHANNEL ownership with earliest origin. Start actual final model choices, visit NET IDs ascending, choose strictly lower exact aggregate loss; equal loss preserves current choice, equal strict minima keep first candidate. Stop after a zero-move sweep or16 sweeps.','scope':'Only retrospective diagnostic counts/witnesses. No global optimum, joint routing legality, original transaction/forecast admission or label-free implementation claim. Labels not model inputs; original gate failures unchanged. No new path, weight/category/threshold or tie tuning.','verification':'Independent400 full-ledger decision traces and known local2/global0 trap qualified. Real independent bitset greedy replay and216 rank vectors required.','bindings':bindings},indent=2)+'\n');rows=[];graphs={}
 for row in read(source)['rows']:
  out=Path(row['output']);ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];resources=[json.loads(x) for x in Path(row['resources']).read_text().splitlines()];channels={r['id'] for r in resources};binsfile=Path(row['resources']).parent/'spatial_bins.json';bins=read(binsfile);domain=read(row['domain_proof']);initial=defaultdict(list);final=defaultdict(list);pools=defaultdict(list);origins=defaultdict(list)
  def support(records):return frozenset(dest[e] for r in records for e in r['answer']['physical_edge_ids'] if dest[e] in channels)
  def offer(net,records,origin):
   s=support(records)
   if s not in pools[net]:pools[net].append(s);origins[net].append(origin)
  for r in read(out/'initial.json')['records']:initial[r['net_id']].append(r)
  for net,rs in sorted(initial.items()):offer(net,rs,{'stage':'initial'})
  for rnd in read(out/'receipt.json')['rounds']:
   for i,event in enumerate(rnd['events']):
    records=event.get('records',event.get('rejected_records'))
    if records is not None:offer(event['net_id'],records,{'round':rnd['round_index'],'event_index':i,'status':event['status']})
  for r in read(out/'round1.json')['records']:final[r['net_id']].append(r)
  start={net:pools[net].index(support(rs)) for net,rs in final.items()};truthcounts={int(n):v for n,v in read(row['truth_payload'])['node_occupancy'].items()};target={n:truthcounts.get(n,0) for n in channels};answer=select(pools,start,target,channels,16);d=D/row['case']/row['initializer']/row['timing_policy']/row['priority'];d.mkdir(parents=True);p=d/'label_joint_counts_trace.json';p.write_text(json.dumps({'label_dependent':True,'admitted_predictor':False,'initial_choices':start,'pool_origins':dict(origins),**answer},separators=(',',':'))+'\n');truth=scores(resources,bins,truthcounts);sourcecounts={int(n):v for n,v in read(row['source_frame'])['ledger'].items()};rawcounts={int(n):v for n,v in read(row['raw_control'])['ledger'].items()};metrics={name:measure(scores(resources,bins,counts),truth,domain) for name,counts in [('joint_label_diagnostic',answer['counts']),('previous_native',sourcecounts),('actual_raw_min',rawcounts)]};checks={name:numeric_comparison(metrics['joint_label_diagnostic'],metrics[name]) for name in ['previous_native','actual_raw_min']};result={key:row[key] for key in ['case','initializer','timing_policy','priority','output','endpoint','resources','domain_proof','truth_payload','source_frame','raw_control']};result.update(diagnostic_payload=str(p),metrics=metrics,numeric_diagnostic_comparisons=checks,both_numeric_comparisons=all(checks.values()),solver_status=answer['status'],initial_L1=answer['initial_L1'],final_L1=answer['final_L1'],moves=len(answer['moves']),sweeps=len(answer['sweeps']),admitted_predictor=False);rows.append(result);print(row['case'],row['initializer'],row['timing_policy'],row['priority'],answer['initial_L1'],answer['final_L1'],result['both_numeric_comparisons'],flush=True)
  for path in [p,out/'initial.json',out/'round1.json',out/'receipt.json',Path(row['endpoint']),Path(g),Path(row['resources']),binsfile,Path(row['domain_proof']),Path(row['truth_payload']),Path(row['source_frame']),Path(row['raw_control'])]:bindings[str(path)]=sha(path)
 assert len(rows)==72
 (D/'verification.json').write_text(json.dumps({'status':'ALL72_BOUNDED_JOINT_AGGREGATE_LABEL_DIAGNOSTICS_COMPUTED','rows':rows,'bindings':bindings,'independent_verification_pending':True,'candidate_promoted':False,'original_quality_gate_passes_unchanged':True},indent=2)+'\n')
if __name__=='__main__':main()
