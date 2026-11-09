"""Reuse admitted immutable control/label vectors; project new exact ledger delta."""
import sys,json,array,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from prediction_metrics import compare

def main():
 E=R/'experiments';source=E/'mmc_joint_channel_diamond_v1_2026-10-18';vp=source/'independent_full_frame_v1.json';proof=json.loads(vp.read_text());assert len(proof['rows'])==3;plan=json.loads((E/'mmc_channel_diamond_Pareto_v1_2026-10-18/protocol.json').read_text());out=E/'mmc_joint_channel_quality_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/prediction_metrics.py',vp]};frames={};needed=set()
 for case,inputs in plan['inputs'].items():
  p=source/case/'candidate.json';assert sha(p)==proof['bindings'][str(p)];new=json.loads(p.read_text());oldp=Path(inputs['frame']);assert sha(oldp)==proof['bindings'][str(oldp)];old=json.loads(oldp.read_text());a={int(n):v for n,v in old['ledger'].items()};b={int(n):v for n,v in new['ledger'].items()};delta={n:b.get(n,0)-a.get(n,0) for n in a.keys()|b.keys() if a.get(n,0)!=b.get(n,0)};assert len(delta)==16;needed.update(delta);frames[case]=(a,b,delta);bindings[str(p)]=sha(p);bindings[str(oldp)]=sha(oldp)
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,primary_controls=['native_retained_on','raw_min_on','previous_native'],domains='Complete original258720positive channels and17160spanbins; concrete top floor(N/20), spatial top20; same tie ordering andrho tolerance1e-12.',scope='Already exposed development labels, existing controls unchanged and transferred only with exact admitted vector/comparison hashes. Original cold gate against previous_native/raw_min_on retained; source-on and supplemental-label comparisons remain explicit. No native/heldout or net-time gain.'),indent=2))
 ep=json.loads(Path(plan['inputs']['case_01']['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);geometry={};stack=[]
 for event,node in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(node);continue
  parent=stack[-2] if len(stack)>1 else None
  if node.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   n=int(node.get('id'))
   if n in needed:
    assert node.get('type') in ['CHANX','CHANY'] and int(node.get('capacity'))==1;loc=node.find('loc');seg=node.find('segment');geometry[n]=[(int(loc.get('layer','0')),x,y,node.get('type'),int(seg.get('segment_id')) if seg is not None else -1) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)]
   parent.remove(node);node.clear()
   if len(geometry)==len(needed):break
  stack.pop()
 assert set(geometry)==needed;results=[]
 for case,(old,new,delta) in frames.items():
  legacy=E/'mmc_terminal_batch_quality_v1_2026-10-18'/case;ap=legacy/'verification.json';admitted=json.loads(ap.read_text());assert admitted['status']=='pass';vectorp=legacy/'vectors.json';controlp=legacy/'comparison.json';assert sha(vectorp)==admitted['bindings'][str(vectorp)] and sha(controlp)==admitted['bindings'][str(controlp)];bindings[str(ap)]=sha(ap);bindings[str(vectorp)]=sha(vectorp);bindings[str(controlp)]=sha(controlp);v=json.loads(vectorp.read_text());baseline=json.loads(controlp.read_text());channels=v['channels'];bins=v['bins'];assert len(channels)==258720 and len(bins)==17160;assert all(c['predictions']['native_retained_on']==old.get(c['node'],0) for c in channels);channel_values=array.array('d',[new.get(c['node'],0)/c['capacity'] for c in channels]);binmass={tuple(b['key']):b['predictions']['native_retained_on'] for b in bins}
  for n,change in delta.items():
   for key in geometry[n]:assert key in binmass;binmass[key]+=change
  assert all(x>=0 for x in binmass.values());bin_values=array.array('d',[binmass[tuple(b['key'])]/b['capacity'] for b in bins]);folder=out/case;folder.mkdir();(folder/'channels.f64').write_bytes(channel_values.tobytes());(folder/'spatial.f64').write_bytes(bin_values.tobytes());metrics={};checks=[]
  for label in channels[0]['labels']:
   metrics[label]={}
   for domain,data,values,k in [('concrete',channels,channel_values,len(channels)//20),('spatial',bins,bin_values,20)]:
    ids=[c['node'] for c in data] if domain=='concrete' else [tuple(b['key']) for b in data];pred=dict(zip(ids,values));truth={i:r['labels'][label]/r['capacity'] for i,r in zip(ids,data)};metrics[label][domain]=compare(pred,truth,k)
   for control in ['native_retained_on','raw_min_on','previous_native']:
    comparisons=[]
    for domain in ['concrete','spatial']:
     for name in ['spearman','precision_at_k']:
      a=metrics[label][domain][name];b=baseline['metrics'][label][control][domain][name];eps=1e-12 if name=='spearman' else 0;comparisons.append(dict(domain=domain,metric=name,candidate=a,control=b,nonregression=a is not None and b is not None and a>=b-eps,strict_improvement=a is not None and b is not None and a>b+eps))
    checks.append(dict(label=label,control=control,comparisons=comparisons,passed=all(v['nonregression'] for v in comparisons) and any(v['strict_improvement'] for v in comparisons)))
  cold=[x for x in checks if x['label']=='cold' and x['control'] in ['raw_min_on','previous_native']];assert len(cold)==2;result=dict(case=case,metrics=metrics,checks=checks,original_cold_gate=all(x['passed'] for x in cold),extended_three_control_all_label_gate=all(x['passed'] for x in checks),files={str(p):sha(p) for p in folder.iterdir()});(folder/'comparison.json').write_text(json.dumps(result,indent=2));results.append(result);print('JOINT QUALITY CASE',case,'cold_gate',result['original_cold_gate'],flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='all_three_complete_joint_candidate_quality_matrices_computed',bindings=bindings,geometry={str(n):keys for n,keys in geometry.items()},rows=results,scope='Independent full-domain/projection/metric audit pending. Original cold gates unchanged; source objective reduction is not prediction or native utility success.'),f,indent=2)
if __name__=='__main__':main()
