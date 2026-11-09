"""Freeze shared ready inputs before extracting policy/horizon phase-response labels."""
import json,struct,shutil
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from verify_prince_ownership_ledger_v2 import owner_payload
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_cost_advance_ablation_trial_v1_2026-10-20';D=E/'prince_paired_cost_state_v1_2026-10-20';MODES=dict(native=0,hold_pres=1,hold_acc=2,hold_both=3)
def load(p):return json.loads(Path(p).read_text())
def word(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def value(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def snapshot(path,i):
 raw=path.read_bytes();assert raw[:8]==b'RCBND001';it,n=struct.unpack_from('<QQ',raw,8);assert it==i and len(raw)==24+n*24;return {node:(kind,occ,cap,acc) for node,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:])}
def config(path):
 rows=path.read_text().splitlines();assert rows[0]=='ROUTECAST_NATIVE_RESOLVED_CONFIGURATION_V1';return {a[0]:int(a[2]) for a in (line.split('\t') for line in rows[1:]) if a[1]=='f32'}
def main():
 D.mkdir(exist_ok=False);design=S/'paired_cost_state_response_design_v1.json';contract=S/'cost_response_quantity_contract_v1.json';proof=S/'policy_inference_verification_v2.json';pp=S/'protocol.json';p=load(pp);jobs={j['case']:j for j in p['jobs']};bindings={str(x):sha(x) for x in [design,contract,proof,pp,Path(__file__)]};(D/'protocol.json').write_text(json.dumps(dict(design=load(design),quantity_contract=str(contract),bindings=dict(bindings),roles='Ready full native RR/CH feature projection/NET owners and BB/config only are inputs. Same ready features shared by4policies and2horizons. All before/after future history fields are LABELS,not teacher-forced horizon2 inputs.',limits='This is not a complete serialized native state:timing criticalities,per-connection electrical state/queues and controller history are not all reconstructed. No exact continuation/sufficient Markov-state claim.'),indent=2)+'\n');inputs=[];requests=[];domains={}
 # Entire input manifest is committed before any ready+1/ready+2 file is read.
 for width in [96,128,160]:
  for episode in range(1,4):
   case=f'w{width:03d}/episode_{episode:02d}';src=S/case/'native';rp=src/'callback.tsv.ready.tsv';events=[]
   for line in rp.open():
    a=line.split()
    if int(a[4]):events.append(int(a[0]));break
   bindings[str(rp)]=sha(rp)
   if not events:
    inputs.append(dict(case=case,status='NO_READY_EVENT',episode=f'episode_{episode:02d}'))
    for mode in MODES:
     for h in [1,2]:requests.append(dict(case=case,mode=mode,horizon=h,status='NO_READY_INPUT_UNAVAILABLE'))
    continue
   t=events[0];assert t>=2;domain=E/'prince_quality_domains_v1_2026-10-20'/f'w{width:03d}'/'resources.jsonl';resources=list(map(json.loads,domain.open()));rrp=src/'boundary'/f'iteration_{t}.bin';rr=snapshot(rrp,t);op=src/'owners'/f'owners_{t}.bin';it,owners=owner_payload(op);assert it==t;counts=Counter(n for ns in owners.values() for n in ns);boxp=src/'boundary'/f'boxes_{t}.bin';cp=src/'callback.tsv.resolved.tsv';cfg=config(cp);identity=(src/'identity.txt').read_text().splitlines();graph=Path(jobs[case+'/native']['command'][jobs[case+'/native']['command'].index('--read_rr_graph')+1]);assert identity[:3]==[sha(graph),sha(src/'design.net'),sha(src/'design.place')];cb=next(list(map(int,line.split())) for line in (src/'callback.tsv').open() if int(line.split()[0])==t);pres=cb[3];folder=D/case;folder.mkdir(parents=True);features=folder/'ready_CHANNEL_features.jsonl'
   with features.open('x') as f:
    for r in resources:
     n=r['id'];kind,occ,cap,acc=rr[n];assert kind in [4,5] and cap==r['capacity']==1 and occ==counts[n] and occ>=0;f.write(json.dumps(dict(id=n,capacity=cap,occupancy=occ,acc_bits=acc),separators=(',',':'))+'\n')
   summary=folder/'ready_prefix_summary.tsv';summary.write_text(''.join('\t'.join(a[k] for k in [0,1,2,3,4,5,6,9,10])+'\n' for a in (line.split() for line in (src/'callback.tsv').open()) if int(a[0])<=t));feature_sha=sha(features);inputs.append(dict(case=case,status='READY_INPUTS_FROZEN',episode=f'episode_{episode:02d}',ready_iteration=t,feature_file=str(features),feature_sha256=feature_sha,resources=len(resources),ready_pres_bits=pres,input_files=dict(full_ready_RR=str(rrp),ready_CHANNEL_features=str(features),ready_NET_owners=str(op),ready_NET_boxes=str(boxp),NET_mapping=str(src/'NET_mapping.tsv'),router_configuration=str(cp),prefix_summary=str(summary),graph=str(graph),packed_net=str(src/'design.net'),placement=str(src/'design.place')),hash_and_identifiers='Provenance keys only;no numeric ID/case/width/hash/time learning features. Full available ready snapshots retained;future files forbidden as inputs.'));domains[case]=resources
   for mode,mask in MODES.items():
    step=pres;planned=[]
    for _ in range(2):step=word(min(value(step if mask&1 else word(value(step)*value(cfg['t_router_opts.pres_fac_mult']))),value(cfg['t_router_opts.max_pres_fac'])));planned.append(step)
    alpha=0 if mask&2 else cfg['t_router_opts.acc_fac']
    for h in [1,2]:requests.append(dict(case=case,mode=mode,horizon=h,status='READY_PLAN_FROZEN',ready_iteration=t,target_iteration=t+h,input_file=str(features),input_sha256=feature_sha,planned_search_pres_bits=planned[:h],planned_alpha_after_search_bits=[alpha]*h,epoch='alpha at each step acts after that step routing;horizon2 acc_before is label-only.'))
   for q in [domain,rrp,op,boxp,cp,src/'identity.txt',src/'NET_mapping.tsv',src/'design.net',src/'design.place',graph,features,summary]:bindings[str(q)]=sha(q)
   print('PAIRED_READY_INPUT_FROZEN',case,len(resources),flush=True)
 frozen=D/'frozen_inputs.json';frozen.write_text(json.dumps(dict(status='ALL9_INPUT_AVAILABILITY_AND72_POLICY_HORIZON_REQUESTS_FROZEN',rows=inputs,requests=requests,bindings=dict(bindings)),indent=2)+'\n');frozen_sha=sha(frozen);labels=[]
 for request in requests:
  if request['status']!='READY_PLAN_FROZEN':labels.append(dict(case=request['case'],mode=request['mode'],horizon=request['horizon'],status=request['status']));continue
  case,mode,h=request['case'],request['mode'],request['horizon'];i=request['target_iteration'];src=S/case/mode;t=request['ready_iteration'];curp=src/'boundary'/f'iteration_{i}.bin';prevp=src/'boundary'/f'iteration_{i-1}.bin';cur=snapshot(curp,i);prev=snapshot(prevp,i-1);ownerp=src/'owners'/f'owners_{i}.bin';it,owners=owner_payload(ownerp);assert it==i;counts=Counter(n for ns in owners.values() for n in ns);callback=next(list(map(int,line.split())) for line in (src/'callback.tsv').open() if int(line.split()[0])==i);assert callback[3]==request['planned_search_pres_bits'][-1];factor=value(request['planned_alpha_after_search_bits'][-1]);folder=D/case/mode;folder.mkdir(parents=True,exist_ok=True);target=folder/f'phase_response_h{h}.jsonl';stats=Counter();maximum=0
  with target.open('x') as f:
   for r in domains[case]:
    n=r['id'];kind,occ,cap,after=cur[n];before=prev[n][3];assert kind in [4,5] and cap==r['capacity']==1 and occ==counts[n];excess=max(0,occ-cap);expected=word(value(before)+value(word(excess*factor))) if excess and factor else before;assert after==expected;stats['resources']+=1;stats['occupied']+=occ>0;stats['owner_incidents']+=occ;stats['overcapacity_resources']+=excess>0;stats['excess_units']+=excess;maximum=max(maximum,occ);f.write(json.dumps(dict(id=n,occupancy=occ,positive_occupancy=int(occ>0),excess=excess,acc_before_global_bits=before,acc_after_global_bits=after),separators=(',',':'))+'\n')
  assert stats['excess_units']==stats['owner_incidents']-stats['occupied'];labels.append(dict(case=case,mode=mode,horizon=h,status='PHASE_LABELS_EXTRACTED',target_file=str(target),target_sha256=sha(target),input_file=request['input_file'],input_sha256=request['input_sha256'],ready_iteration=t,target_iteration=i,source_future_RR=str(curp),source_previous_RR_label_only=str(prevp),source_future_NET_owners=str(ownerp),source_future_NET_boxes=str(src/'boundary'/f'boxes_{i}.bin'),statistics=dict(stats),maximum_occupancy=maximum,target_scope='Transient phase counts may exceed capacity;not final legal occupancy or query other-owner demand.'))
  for q in [curp,prevp,ownerp,src/'boundary'/f'boxes_{i}.bin',target]:bindings[str(q)]=sha(q)
 folds=[]
 for episode in [f'episode_{i:02d}' for i in range(1,4)]:
  train=[r['case'] for r in inputs if r['status']=='READY_INPUTS_FROZEN' and r['episode']!=episode];test=[r['case'] for r in inputs if r['status']=='READY_INPUTS_FROZEN' and r['episode']==episode];assert len(train)==4 and len(test)==2;folds.append(dict(heldout_episode=episode,train_ready_cases=train,test_ready_cases=test,train_requests=[i for i,r in enumerate(requests) if r['case'] in train],test_requests=[i for i,r in enumerate(requests) if r['case'] in test],unavailable_cases=[r['case'] for r in inputs if r['status']=='NO_READY_EVENT']))
 foldp=D/'grouped_folds.json';foldp.write_text(json.dumps(dict(folds=folds,scope='All4 policy arms/horizons of an episode held out together;6unique ready contexts,not24independent inputs;all exposed development.'),indent=2)+'\n');bindings[str(foldp)]=sha(foldp);assert sha(frozen)==frozen_sha and len(inputs)==9 and len(requests)==len(labels)==72 and sum(r['status']=='PHASE_LABELS_EXTRACTED' for r in labels)==48;assert all(sha(p)==q for p,q in bindings.items())
 (D/'dataset_manifest.json').write_text(json.dumps(dict(status='PAIRED_PHASE_RESPONSE_EXTRACTED_INDEPENDENT_AUDIT_PENDING',rows=labels,input_manifest=str(frozen),input_manifest_sha256=frozen_sha,bindings=bindings,ready_input_resources=sum(r.get('resources',0) for r in inputs),target_resource_rows=sum(r.get('statistics',{}).get('resources',0) for r in labels),full9_gate=False,scope='Auxiliary response data only;original final/global/native/fullpaid/unseen/hardware goals unmet.'),indent=2)+'\n');print('PAIRED_PHASE_DATA_EXTRACTED',sum(r.get('statistics',{}).get('resources',0) for r in labels),flush=True)
if __name__=='__main__':main()
