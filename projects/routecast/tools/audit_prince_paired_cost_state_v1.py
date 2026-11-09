"""Independent byte readers, ownership coherence,roles,plans and phase-transition audit."""
import json,struct
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_paired_cost_state_v1_2026-10-20';S=E/'prince_cost_advance_ablation_trial_v1_2026-10-20';MASK=dict(native=0,hold_pres=1,hold_acc=2,hold_both=3)
def load(p):return json.loads(Path(p).read_text())
def number(w):return struct.unpack('<f',int(w).to_bytes(4,'little'))[0]
def word(x):return int.from_bytes(struct.pack('<f',x),'little')
def rr(path,phase):
 raw=path.read_bytes();assert raw[:8]==b'RCBND001' and int.from_bytes(raw[8:16],'little')==phase;n=int.from_bytes(raw[16:24],'little');assert len(raw)==24+n*24;rows={}
 for j in range(n):
  p=24+j*24;node=int.from_bytes(raw[p:p+8],'little');kind=int.from_bytes(raw[p+8:p+12],'little');occ=int.from_bytes(raw[p+12:p+16],'little',signed=True);cap=int.from_bytes(raw[p+16:p+20],'little',signed=True);acc=int.from_bytes(raw[p+20:p+24],'little');assert node not in rows;rows[node]=(kind,occ,cap,acc)
 return rows

def owners(path,phase,mapping,domain):
 raw=path.read_bytes();assert raw[:8]==b'RCOWN001' and int.from_bytes(raw[8:16],'little')==phase;count=int.from_bytes(raw[16:24],'little');p=24;groups={};counts=Counter()
 for _ in range(count):
  net=int.from_bytes(raw[p:p+8],'little');endpoint=int.from_bytes(raw[p+8:p+16],'little');n=int.from_bytes(raw[p+16:p+24],'little');p+=24;assert net not in groups and mapping[net][0]==endpoint and not mapping[net][1];nodes=[int.from_bytes(raw[p+8*j:p+8*j+8],'little') for j in range(n)];p+=8*n;assert len(set(nodes))==n and set(nodes)<=domain;groups[net]=set(nodes);counts.update(nodes)
 assert p==len(raw) and set(groups)=={net for net,(endpoint,ignored) in mapping.items() if not ignored};return counts,groups

def cfg(path):
 lines=path.read_text().splitlines();assert lines[0]=='ROUTECAST_NATIVE_RESOLVED_CONFIGURATION_V1';return {a[0]:int(a[2]) for a in (line.split('\t') for line in lines[1:]) if a[1]=='f32'}
def main():
 inputs=load(D/'frozen_inputs.json');dataset=load(D/'dataset_manifest.json');assert sha(D/'frozen_inputs.json')==dataset['input_manifest_sha256'];assert all(sha(p)==h for p,h in dataset['bindings'].items());assert all(sha(p)==h for p,h in inputs['bindings'].items());by={r['case']:r for r in inputs['rows']};requests={(r['case'],r['mode'],r['horizon']):r for r in inputs['requests']};ready={};domains={};mapping={};readychecks=targetchecks=overcap=maximum=0;planchecks=0;labelvectors={};rows=[];source_bindings={}
 for case,row in by.items():
  if row['status']=='NO_READY_EVENT':continue
  t=row['ready_iteration'];files=row['input_files'];source=S/case/'native';mp={}
  for line in Path(files['NET_mapping']).open():
   n,e,ignored,name=line.rstrip('\n').split('\t',3);mp[int(n)]=(int(e),bool(int(ignored)))
  mapping[case]=mp;state=rr(Path(files['full_ready_RR']),t);projection={x['id']:x for x in map(json.loads,Path(files['ready_CHANNEL_features']).open())};domain={n for n,(kind,occ,cap,acc) in state.items() if kind in [4,5] and cap>0};assert set(projection)==domain and len(domain)==row['resources'];counts,_=owners(Path(files['ready_NET_owners']),t,mp,domain)
  for n,x in projection.items():
   kind,occ,cap,acc=state[n];assert x==dict(id=n,capacity=cap,occupancy=occ,acc_bits=acc);assert cap==1 and occ==counts[n] and occ>=0;readychecks+=1
  raw=Path(files['ready_NET_boxes']).read_bytes();assert raw[:8]==b'RCBOX001' and int.from_bytes(raw[8:16],'little')==t;ids={int.from_bytes(raw[24+32*j:32+32*j],'little') for j in range(int.from_bytes(raw[16:24],'little'))};assert ids==set(mp)
  callbacks=[line.split() for line in (source/'callback.tsv').open()];expected=''.join('\t'.join(a[k] for k in [0,1,2,3,4,5,6,9,10])+'\n' for a in callbacks if int(a[0])<=t);assert Path(files['prefix_summary']).read_text()==expected;pres=int(next(a[3] for a in callbacks if int(a[0])==t));assert pres==row['ready_pres_bits'];conf=cfg(Path(files['router_configuration']));ready[case]=state;domains[case]=domain
  for mode,mask in MASK.items():
   p=pres;pp=[]
   for _ in range(2):
    p=word(min(number(p) if mask&1 else number(word(number(p)*number(conf['t_router_opts.pres_fac_mult']))),number(conf['t_router_opts.max_pres_fac'])));pp.append(p)
   for h in [1,2]:
    q=requests[case,mode,h];assert q['input_file']==row['feature_file'] and q['input_sha256']==row['feature_sha256']==sha(row['feature_file']);assert q['ready_iteration']==t and q['target_iteration']==t+h;assert q['planned_search_pres_bits']==pp[:h];assert q['planned_alpha_after_search_bits']==([0 if mask&2 else conf['t_router_opts.acc_fac']]*h);planchecks+=1
  source_bindings[str(source/'callback.tsv')]=sha(source/'callback.tsv')
 for target in dataset['rows']:
  key=target['case'],target['mode'],target['horizon'];q=requests[key]
  if target['status']=='NO_READY_INPUT_UNAVAILABLE':assert by[target['case']]['status']=='NO_READY_EVENT' and q['status']=='NO_READY_INPUT_UNAVAILABLE';continue
  case,mode,h=key;t=by[case]['ready_iteration'];phase=t+h;domain=domains[case];assert target['input_file']==by[case]['feature_file'] and target['input_sha256']==by[case]['feature_sha256'];assert target['target_iteration']==phase and target['ready_iteration']==t;current=rr(Path(target['source_future_RR']),phase);previous=rr(Path(target['source_previous_RR_label_only']),phase-1);counts,groups=owners(Path(target['source_future_NET_owners']),phase,mapping[case],domain);records={x['id']:x for x in map(json.loads,Path(target['target_file']).open())};assert set(records)==domain;factor=number(q['planned_alpha_after_search_bits'][-1]);stats=Counter();maxo=0;labelvectors[key]={}
  for n,x in records.items():
   k,occ,cap,acc=current[n];before=previous[n][3];assert cap==1 and occ==counts[n];excess=occ-1 if occ>1 else 0;assert x==dict(id=n,occupancy=occ,positive_occupancy=int(occ>0),excess=excess,acc_before_global_bits=before,acc_after_global_bits=acc);expected=word(number(before)+number(word(excess*factor))) if excess and factor else before;assert acc==expected;targetchecks+=1;overcap+=occ>cap;maxo=max(maxo,occ);maximum=max(maximum,occ);stats['resources']+=1;stats['occupied']+=occ>0;stats['owner_incidents']+=occ;stats['overcapacity_resources']+=occ>cap;stats['excess_units']+=excess;labelvectors[key][n]=(occ,acc)
  assert dict(stats)==target['statistics'] and maxo==target['maximum_occupancy'];src=S/case/mode;receipt=load(src/'receipt.json');cp=src/'callback.tsv';assert sha(cp)==receipt['files'][str(cp)];p_actual=next(int(a[3]) for a in (line.split() for line in cp.open()) if int(a[0])==phase);assert p_actual==q['planned_search_pres_bits'][-1];alpha_actual=next(int(a[6]) for a in (line.split() for line in (src/'queries.tsv.cost_advances.tsv').open()) if int(a[0])==1 and int(a[1])==phase);assert alpha_actual==q['planned_alpha_after_search_bits'][-1];source_bindings[str(cp)]=sha(cp);source_bindings[str(src/'queries.tsv.cost_advances.tsv')]=sha(src/'queries.tsv.cost_advances.tsv');rows.append(dict(case=case,mode=mode,horizon=h,resources=len(records),excess_units=stats['excess_units'],maximum_occupancy=maxo));print('PAIRED_RESPONSE_LABEL_PASS',case,mode,h,stats['excess_units'],flush=True)
 for case in ready:
  for left,right in [('native','hold_acc'),('hold_pres','hold_both')]:assert {n:a[0] for n,a in labelvectors[case,left,1].items()}=={n:a[0] for n,a in labelvectors[case,right,1].items()}
 folds=load(D/'grouped_folds.json')['folds'];availability=[]
 for fold in folds:
  episode=fold['heldout_episode'];train=[c for c in by if c.split('/')[1]!=episode];test=[c for c in by if c.split('/')[1]==episode];assert set(train).isdisjoint(test) and set(train)|set(test)==set(by);assert set(fold['train_ready_cases'])=={c for c in train if c in ready} and set(fold['test_ready_cases'])=={c for c in test if c in ready};assert len(fold['train_requests'])==32 and len(fold['test_requests'])==16;assert set(fold['train_requests']).isdisjoint(fold['test_requests'])
  for group,indices in [('train',fold['train_requests']),('test',fold['test_requests'])]:
   cases=set(train if group=='train' else test);assert all(inputs['requests'][i]['case'] in cases and inputs['requests'][i]['status']=='READY_PLAN_FROZEN' for i in indices)
  availability.append(dict(heldout_episode=episode,train_original_cases=train,test_original_cases=test,train_unavailable=[c for c in train if c not in ready],test_unavailable=[c for c in test if c not in ready]))
 assert readychecks==89280 and targetchecks==714240 and planchecks==48 and len(by)==9 and len(requests)==72 and len(rows)==48 and sum(r['status']=='NO_READY_INPUT_UNAVAILABLE' for r in dataset['rows'])==24
 out=dict(status='ALL_READY_INPUTS_AND48_POLICY_HORIZON_TARGETS_INDEPENDENTLY_RECONCILED',ready_feature_rows=readychecks,target_resource_rows=targetchecks,transient_overcapacity_rows=overcap,maximum_target_occupancy=maximum,rows=rows,grouped_availability=availability,bindings={**source_bindings,**{str(p):sha(p) for p in [D/'frozen_inputs.json',D/'dataset_manifest.json',D/'grouped_folds.json',Path(__file__)]}},scope='Independent per-field byte decoders/native endpoint mapping/uniqueNET counts. Bit-exact global CHANNEL recurrence,known plans versus future logs,shared ready-only input hashes and complete episode grouping checked. Phase labels not query demand or final legal truth;no Markov sufficiency/model/native utility admission.')
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print('PAIRED_RESPONSE_DATASET_AUDIT_PASS',readychecks,targetchecks,overcap,maximum)
if __name__=='__main__':main()
