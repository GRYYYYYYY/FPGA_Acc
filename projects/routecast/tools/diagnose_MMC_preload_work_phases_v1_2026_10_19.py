"""Closed-study exact iteration1/later work decomposition; no retuning."""
import pathlib,json,hashlib,re
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 T=R/'experiments/mmc_native_excess_trace_replay_v1_2026-10-19';vp=T/'verification.json';v=json.loads(vp.read_text());assert v['status']=='all6_excess_utility_native_traces_independently_replayed';decision=R/'experiments/mmc_native_excess_utility_review_v1_2026-10-19/research_decision_v1.json';assert not json.loads(decision.read_text())['all3_primary_native_component_gate_pass'];O=R/'experiments/mmc_preload_work_phase_diagnosis_v1_2026-10-19';O.mkdir();bindings={str(p):sha(p) for p in [vp,decision,pathlib.Path(__file__).resolve()]};rows=[];keys=['NET_operations','connection_operations','heap_pushes','heap_pops']
 for case in [f'episode_{i:02d}' for i in range(1,4)]:
  arms={}
  for arm in ['zero','forecast']:
   p=T/(case+'_'+arm+'.json');assert v['bindings'][str(p)]==sha(p);a=json.loads(p.read_text());stats=a['iteration_stats'];first={k:stats[0][k] for k in keys};later={k:sum(x[k] for x in stats[1:]) for k in keys};total={k:sum(x[k] for x in stats) for k in keys};lp=R/'experiments/mmc_native_excess_utility_v1_2026-10-19'/case/arm/'cold/native.log';assert a['bindings'][str(lp)]==sha(lp);log=lp.read_text();raw=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',log);assert len(raw)==1 and list(total.values())==list(map(int,raw[0]));assert first['NET_operations']==55300 and first['connection_operations']==115572;assert all(first[k]+later[k]==total[k] for k in keys);cp=[x for x in a['checkpoints'] if x['phase']=='iteration_end_after_local_opins'];assert len(cp)==len(stats)
   arms[arm]=dict(iterations=len(stats),first=first,later=later,total=total,first_overused_RR_nodes=cp[0]['overused_RR_nodes'],later_overused_RR_node_checkpoint_sum=sum(x['overused_RR_nodes'] for x in cp[1:]),later_heap_pushes_per_connection_operation=str(Fraction(later['heap_pushes'],later['connection_operations'])));bindings[str(p)]=sha(p);bindings[str(lp)]=sha(lp)
  z,f=arms['zero'],arms['forecast'];extra=f['total']['heap_pushes']-z['total']['heap_pushes'];extra_later=f['later']['heap_pushes']-z['later']['heap_pushes'];assert extra>0;row=dict(case=case,arms=arms,first_work_change_fractions={k:str(Fraction(f['first'][k],z['first'][k])-1) for k in keys},later_work_change_fractions={k:str(Fraction(f['later'][k],z['later'][k])-1) for k in keys},fraction_extra_heap_pushes_after_iteration1=str(Fraction(extra_later,extra)),later_heap_pushes_per_connection_ratio=str(Fraction(f['later']['heap_pushes'],f['later']['connection_operations'])/Fraction(z['later']['heap_pushes'],z['later']['connection_operations'])));rows.append(row);print(case,'extra_pushes_later_fraction',float(Fraction(row['fraction_extra_heap_pushes_after_iteration1'])),'later_per_connection_ratio',float(Fraction(row['later_heap_pushes_per_connection_ratio'])),flush=True)
 with (O/'verification.json').open('x') as f:json.dump(dict(status='ALL6_FIRST_AND_LATER_WORK_SPLITS_MATCH_RAW_NATIVE_TOTALS',bindings=bindings,cases=rows,new_native_jobs=0,original_native_utility_gate_still_failed=True,scope='Posthoc phase attribution of measured operation counts, not elapsed-time split, perRR causal blame or proof a new preload mapping works. First/later checkpoints follow native localOPIN phase; exact native operations stay distinct from congestion units. Different termination rounds retained. No scale/round/seed sweep or native rerun.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
