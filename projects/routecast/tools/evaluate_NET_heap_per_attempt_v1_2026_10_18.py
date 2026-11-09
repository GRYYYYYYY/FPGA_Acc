"""Fixed development diagnostic separating invocation frequency and search work."""
import array,collections,json,math,sys
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from diagnose_NET_length_confounding_v1_2026_10_18 import rank,center,corr,grouped,dot

def main():
 E=R/'experiments';out=E/'mmc_NET_heap_per_attempt_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={};cache={}
 def receipt(p):
  p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
 source=E/'mmc_NET_pressure_exposure_v1_2026-10-18';plan=receipt(source/'protocol.json');sm=receipt(source/'vector_manifest.json');dom=receipt(source/'NET_domains.json');sp=receipt(E/'mmc_NET_pressure_inputs_verification_v1_2026-10-18/verification.json');work=receipt(E/'mmc_native_connection_work_replay_v1_2026-10-18/verification.json');wp=receipt(E/'mmc_native_connection_work_replay_v1_2026-10-18/independent_verification_v1.json');calls=receipt(E/'mmc_native_connection_CID_binding_v1_2026-10-18/verification.json');cp=receipt(E/'mmc_native_connection_CID_binding_v1_2026-10-18/independent_verification_v1.json');receipt(Path(__file__));receipt_path=R/'tools/diagnose_NET_length_confounding_v1_2026_10_18.py';bindings[str(receipt_path)]=sha(receipt_path)
 protocol=dict(status='fixed_before_computation',sources=plan['sources'],methods=plan['methods']+['manifest_fanout'],targets=['heap_pushes_per_attempt','heap_pops_per_attempt'],domains=['all_NETs_zero_for_no_attempt','attempted_NETs_only'],denominator='Sum of successful and failed explicit native sink calls over every CID in NET. Heap is sum over same attempts. Exact rational ranks. Zero-attempt NETs retain explicit zero placeholder only in full-domain view; their search difficulty is undefined.',controls='Report raw Spearman, exact-attempt-count-stratum demeaned rank correlation, then additionally remove source unique-node-count and fanout linear rank projections within the same strata.',scope='Post-exposure development diagnostic. Attempt count is outcome-derived conditioning, never a prospective input. No causal interpretation, gate replacement, independent family or elapsed-time claim.')
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2));rows=[];coverage=[]
 def read(desc,proof):
  p=desc['path'];assert proof['bindings'][p]==desc['sha256']
  if p not in cache:
   assert sha(p)==desc['sha256'];a=array.array(desc.get('typecode','d'));a.frombytes(Path(p).read_bytes());assert len(a)==desc['values'] and sys.byteorder=='little';cache[p]=a;bindings[p]=desc['sha256']
  return cache[p]
 def partial(x,y,l,f):
  x,y,l,f=map(center,(x,y,l,f));ll,ff,lf=dot(l,l),dot(f,f),dot(l,f);det=ll*ff-lf*lf
  if det<=0:return None
  def res(a):
   al,af=dot(a,l),dot(a,f);u=(al*ff-af*lf)/det;v=(af*ll-al*lf)/det;z=[a0-u*b-v*c for a0,b,c in zip(a,l,f)];return z if dot(z,z)>1e-20*dot(a,a) else None
  a,b=res(x),res(y);return corr(a,b) if a is not None and b is not None else None
 for case in plan['cases']:
  ep=receipt(E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json');ids=dom[case]['NET_ids'];members=collections.defaultdict(list)
  for q in ep['connections']:members[q['net_id']].append(q['connection_id'])
  assert ids==sorted(members) and sum(map(len,members.values()))==115572;fan=[len(members[n]) for n in ids]
  for policy in ['off','on']:
   c=next(r for r in calls['rows'] if r['case']==case and r['arm']==policy);w=next(r for r in work['rows'] if r['case']==case and r['arm']==policy);success=read(c['vectors']['successful_sink_operations'],cp);fail=read(c['vectors']['failed_sink_attempts'],cp);attempts=[sum(success[i]+fail[i] for i in members[n]) for n in ids];heap={}
   for name in ['heap_pushes','heap_pops']:
    a=read(w['vectors'][name],wp);heap[name]=[sum(a[i] for i in members[n]) for n in ids];assert sum(heap[name])==w['attributed_'+name];assert all(count or value==0 for count,value in zip(attempts,heap[name]))
   coverage.append(dict(case=case,policy=policy,all_NETs=len(ids),attempted_NETs=sum(n>0 for n in attempts),zero_attempt_NETs=sum(n==0 for n in attempts),successful_attempts=sum(success),failed_attempts=sum(fail),total_heap_pushes=sum(heap['heap_pushes']),total_heap_pops=sum(heap['heap_pops'])))
   for domain in protocol['domains']:
    selected=[i for i,n in enumerate(attempts) if domain.startswith('all_') or n>0];groups=[attempts[i] for i in selected];fr=rank([fan[i] for i in selected]);fg=grouped(fr,groups);targets={name:rank([Fraction(values[i],attempts[i]) if attempts[i] else Fraction(0) for i in selected]) for name,values in heap.items()}
    for source_name in plan['sources']:
     scores={m:read(sm[case+'__'+source_name+'__'+m],sp) for m in plan['methods']};scores['manifest_fanout']=fan;lr=rank([scores['unique_node_count'][i] for i in selected]);lg=grouped(lr,groups)
     for method,values in scores.items():
      xr=rank([values[i] for i in selected]);xg=grouped(xr,groups)
      for name,yr in targets.items():
       yg=grouped(yr,groups);rows.append(dict(case=case,policy=policy,domain=domain,source=source_name,method=method,target=name+'_per_attempt',NETs=len(selected),spearman=corr(xr,yr),within_exact_attempt_count_rank_correlation=corr(xg,yg),within_count_partial_rank_controlling_length_fanout=None if method in ['manifest_fanout','unique_node_count'] else partial(xg,yg,lg,fg)))
  print('PER ATTEMPT DIAGNOSTIC CASE',case,flush=True)
 assert len(rows)==864
 assert all(sha(p)==h for p,h in bindings.items())
 with (out/'results.json').open('x') as f:json.dump(dict(status='all864_exact_rational_heap_per_attempt_diagnostics_computed',bindings=bindings,coverage=coverage,rows=rows,scope=protocol['scope']),f,indent=2)
if __name__=='__main__':main()
