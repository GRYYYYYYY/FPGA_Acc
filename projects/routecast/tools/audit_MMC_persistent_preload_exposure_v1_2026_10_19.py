"""All6 native-checkpoint/preload-support overlap; no new routing or parameter sweep."""
import pathlib,json,hashlib,struct
from fractions import Fraction
from collections import Counter
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_persistent_preload_exposure_v1_2026-10-19';O.mkdir(exist_ok=False);T=R/'experiments/mmc_native_excess_trace_replay_v1_2026-10-19';vp=T/'verification.json';v=json.loads(vp.read_text());assert v['status']=='all6_excess_utility_native_traces_independently_replayed';E=R/'experiments/mmc_ensemble_excess_preload_v1_2026-10-19';ep=E/'verification.json';export=json.loads(ep.read_text());assert export['status']=='THREE_BOUND_GRAPH_EXCESS_PRELOAD_INPUTS_AND_ZERO_CONTROL_VERIFIED';bindings={str(p):sha(p) for p in [vp,ep,pathlib.Path(__file__).resolve(),R/'build/native_excess_preload_state_v2_2026-10-19/source/route.cpp',R/'build/native_owner_trace_cold_v1_2026-10-19/source/routecast_owner_trace_impl.h']};rows=[]
 for case in ['episode_01','episode_02','episode_03']:
  risk=E/(case+'.risk');assert export['bindings'][str(risk)]==sha(risk);lines=risk.read_text().splitlines();head=lines[0].split();weights={}
  for l in lines[1:]:
   n,bits=map(int,l.split());value=struct.unpack('<f',struct.pack('<I',bits))[0];assert value>0 and n not in weights;weights[n]=Fraction.from_float(value)
  S=set(weights);assert len(S)==int(head[3]);mass=sum(weights.values());arms={};bindings[str(risk)]=sha(risk)
  for arm in ['zero','forecast']:
   ap=T/(case+'_'+arm+'.json');assert v['bindings'][str(ap)]==sha(ap);a=json.loads(ap.read_text());trace=R/'experiments/mmc_native_excess_utility_v1_2026-10-19'/case/arm/'cold/owner_trace.tsv';expected=a['checkpoints'];index=0;active=None;seen=set();ever=set();later=set();units=Counter();rounds=[];h=hashlib.sha256()
   with trace.open('rb') as f:
    for line in f:
     h.update(line)
     if line.startswith(b'CP '):
      assert active is None;w=line.split();active=(w[1].decode(),int(w[2]));assert active==(expected[index]['phase'],expected[index]['iteration']);seen=set();round_units=0;round_total_units=0;count=0
     elif active and line.startswith(b'V '):
      _,n,occ,cap=line.split();n,occ,cap=int(n),int(occ),int(cap);assert occ>cap;count+=1;round_total_units+=occ-cap
      if n in S:
       assert n not in seen and cap==1;seen.add(n);round_units+=occ-cap
       if active[0]=='iteration_end_after_local_opins' and active[1]>=2:units[n]+=occ-cap
     elif line==b'CE\n':
      assert active is not None and count==expected[index]['overused_RR_nodes']
      if active[0]=='iteration_end_after_local_opins':
       ever.update(seen)
       if active[1]>=2:later.update(seen)
       rounds.append(dict(iteration=active[1],native_overused_RR_nodes=count,preloaded_overused_CHANNEL_nodes=len(seen),native_total_overuse_units=round_total_units,preloaded_overuse_units=round_units,preload_mass_on_currently_overused_CHANNELs=str(sum(weights[n] for n in seen))))
      active=None;index+=1
   assert active is None and index==len(expected) and h.hexdigest()==a['bindings'][str(trace)];assert len(rounds)==len(a['iteration_stats']) and rounds[-1]['native_overused_RR_nodes']==0
   arms[arm]=dict(iterations=len(rounds),ever=ever,later=later,never_overused_at_iteration_end=len(S-ever),never_overused_in_cost_charged_iterations=len(S-later),preload_mass_never_overused_in_cost_charged_iterations=str(sum(weights[n] for n in S-later)),native_cost_charged_overuse_units_on_preloaded_CHANNELs=sum(units.values()),rounds=rounds);bindings[str(ap)]=sha(ap);bindings[str(trace)]=h.hexdigest();print('PRELOAD_EXPOSURE',case,arm,'preloaded',len(S),'never_end_overused',len(S-ever),'never_cost_round_overused',len(S-later),flush=True)
  z,f=arms['zero']['ever'],arms['forecast']['ever'];parts={'overused_in_both':z&f,'zero_only':z-f,'forecast_only':f-z,'neither':S-(z|f)};assert sum(len(x) for x in parts.values())==len(S)
  partition={k:dict(CHANNEL_nodes=len(ns),initial_excess_mass=str(sum(weights[n] for n in ns))) for k,ns in parts.items()}
  for x in arms.values():x['ever_overused_CHANNEL_nodes']=len(x.pop('ever'));x['ever_overused_in_cost_charged_iterations_CHANNEL_nodes']=len(x.pop('later'))
  rows.append(dict(case=case,preloaded_CHANNEL_nodes=len(S),initial_float32_excess_mass=str(mass),arms=arms,observed_iteration_end_support_partition=partition))
 result=dict(status='ALL6_PRELOADED_SUPPORT_VS_COMPLETE_NATIVE_ITERATION_END_OVERUSE_AUDITED',cases=rows,bindings=bindings,new_native_jobs=0,scope='Posthoc complete iteration-end overlap only. Preload was a permanent initial acc_cost offset, not one-round advice; native iteration1 uses acc_fac0 and later rounds add nonnegative observed overuse. No exact final floating-point cost reconstruction. Zero-arm overlap is baseline behavior, not invariant truth; forecast-arm absence may be successful avoidance, not a false-positive proof. Intra-iteration overuse and causal perRR slowdown are not inferred. Original failed prediction/native utility gates unchanged; no tuned scale, decay, seed or outcome-dependent removal.')
 (O/'review.json').open('x').write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
