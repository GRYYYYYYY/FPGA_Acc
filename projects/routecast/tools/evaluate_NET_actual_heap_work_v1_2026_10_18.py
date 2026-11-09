"""Frozen descriptive source-score matrix on measured native heap work."""
import sys,json,array,math,collections,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from verify_mmc_pressure_risk_v2_2026_10_18 import rank_info

def main():
 E=R/'experiments';source=E/'mmc_NET_pressure_exposure_v1_2026-10-18';sp=source/'protocol.json';plan=json.loads(sp.read_text());smp=source/'vector_manifest.json';sm=json.loads(smp.read_text());dp=source/'NET_domains.json';domains=json.loads(dp.read_text());srcproofp=E/'mmc_NET_pressure_inputs_verification_v1_2026-10-18/verification.json';srcproof=json.loads(srcproofp.read_text());labels=E/'mmc_native_connection_work_replay_v1_2026-10-18';lp=labels/'verification.json';label=json.loads(lp.read_text());proofp=labels/'independent_verification_v1.json';proof=json.loads(proofp.read_text());assert len(proof['rows'])==6;out=E/'mmc_NET_actual_heap_work_v1_2026-10-18';out.mkdir(exist_ok=False);(out/'targets').mkdir();bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/verify_mmc_pressure_risk_v2_2026_10_18.py',sp,smp,dp,srcproofp,lp,proofp]};methods=plan['methods']+['manifest_fanout'];assert len(methods)==6
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,primary_source=plan['primary_source'],primary_method=plan['primary_score'],sources=plan['sources'],methods=methods,targets=['heap_pushes','heap_pops'],controls='Original5methods plus complete manifest fanout. Conditional rank association removes both source unique_node_count and manifest fanout ranks; exact rank variance degeneracy stays undefined.',selection='Full55300NET domain, top5percent deterministic NET-ID ties, full truth-tie hit bounds; report actual heap-work capture and selected mean heap work.',scope='Measured heap operations aggregated by NET across already exposed development observations. Not elapsed time, causal benefit, a new primary gate or unseen-family evidence.'),indent=2));rows=[];target_manifest={}
 def read(desc,typecode):
  assert sha(desc['path'])==desc['sha256'];bindings[desc['path']]=desc['sha256'];a=array.array(typecode);a.frombytes(Path(desc['path']).read_bytes());assert len(a)==desc['values'] and sys.byteorder=='little';return a
 def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
 def correlation(a,b):
  den=math.sqrt(dot(a,a)*dot(b,b));return dot(a,b)/den if den else None
 for case in plan['cases']:
  epfile=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';ep=json.loads(epfile.read_text());bindings[str(epfile)]=sha(epfile);netids=domains[case]['NET_ids'];assert netids==sorted(set(q['net_id'] for q in ep['connections'])) and len(netids)==55300;fanout=collections.Counter(q['net_id'] for q in ep['connections']);fan=array.array('Q',[fanout[n] for n in netids]);N=len(netids);K=N//20;fr=rank_info(fan,K);targets={}
  for policy in ['off','on']:
   values=[]
   for name in ['heap_pushes','heap_pops']:
    spec=next(x for x in label['rows'] if x['case']==case and x['arm']==policy)['vectors'][name];assert proof['bindings'][spec['path']]==spec['sha256'];cidwork=read(spec,'Q');assert len(cidwork)==115572;totals=collections.Counter()
    for q in ep['connections']:totals[q['net_id']]+=cidwork[q['connection_id']]
    data=array.array('Q',[totals[n] for n in netids]);assert sum(data)==sum(cidwork);values.append(data)
    p=out/'targets'/(case+'__'+policy+'__'+name+'.u64');p.write_bytes(data.tobytes());target_manifest[case+'__'+policy+'__'+name]=dict(path=str(p),sha256=sha(p),values=N,typecode='Q',byteorder=sys.byteorder)
   targets[policy]=values
  fp=out/'targets'/(case+'__fanout.u64');fp.write_bytes(fan.tobytes());target_manifest[case+'__fanout']=dict(path=str(fp),sha256=sha(fp),values=N,typecode='Q',byteorder=sys.byteorder)
  for source_method in plan['sources']:
   scores={}
   for method in plan['methods']:
    desc=sm[case+'__'+source_method+'__'+method];assert srcproof['bindings'][desc['path']]==desc['sha256'];scores[method]=read(desc,'d')
   scores['manifest_fanout']=fan;lr=rank_info(scores['unique_node_count'],K)['center'];fc=fr['center'];ll=dot(lr,lr);ff=dot(fc,fc);lf=dot(lr,fc);det=ll*ff-lf*lf
   def residual(rank):
    if not det:return None
    x=rank['center'];xl,xf=dot(x,lr),dot(x,fc);a=(xl*ff-xf*lf)/det;b=(xf*ll-xl*lf)/det;result=[v-a*l-b*f for v,l,f in zip(x,lr,fc)]
    return None if dot(result,result)<=1e-20*rank['variance'] else result
   ranked={m:rank_info(v,K) for m,v in scores.items()}
   for policy,(count,fraction) in targets.items():
    for target,y in [('heap_pushes',count),('heap_pops',fraction)]:
     yr=rank_info(y,K);yres=residual(yr)
     for method,x in scores.items():
      xr=ranked[method];rho=correlation(xr['center'],yr['center']);xres=None if method in ['manifest_fanout','unique_node_count'] else residual(xr);partial=correlation(xres,yres) if xres is not None and yres is not None else None;selected=xr['selected'];truth_selected=yr['selected'];boundary=yr['boundary'];above={i for i,v in enumerate(y) if v>boundary};equal={i for i,v in enumerate(y) if v==boundary};slots=K-len(above);base=len(selected&above);overlap=len(selected&equal);lower=base+max(0,slots-len(equal-selected));upper=base+min(slots,overlap);hits=len(selected&truth_selected);assert lower<=hits<=upper
      rows.append(dict(case=case,source=source_method,policy=policy,target=target,method=method,NETs=N,K=K,spearman=rho,partial_rank_correlation_controlling_length_and_fanout=partial,deterministic_precision_at_K=hits/K,truth_tie_hit_bounds=[lower,upper],heap_work_capture=sum(y[i] for i in selected)/sum(y),selected_NET_mean_heap_work=sum(y[i] for i in selected)/K))
  print('DISTINCT CID MATRIX CASE',case,flush=True)
 assert len(rows)==432
 (out/'target_manifest.json').write_text(json.dumps(target_manifest,indent=2))
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='all432_actual_heap_NET_diagnostic_cells_computed',bindings=bindings,rows=rows,scope='Independent aggregation/rank/control verification pending; no old primary/cold/native gates changed.'),f,indent=2)
 print('ALL432 DISTINCT CID NET CELLS COMPLETE',flush=True)
if __name__=='__main__':main()
