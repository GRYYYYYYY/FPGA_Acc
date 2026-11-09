"""Fresh-stage coverage, independent geometry/selection and native gate audit."""
import json,re,time
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha,placements
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'xtea_fresh_paired_workflow_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def sequences(path):
 out={};name=None
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:name=m[2];assert name not in out;out[name]=[]
  n=NODE.match(line)
  if n:out[name].append((int(n[1]),n[2],int(n[3])))
 return out

def native_checks(folder,result):
 checks=[]
 for row in result['rows']:
  cid=row['candidate_id'];src=folder/f'candidate_{cid:02d}';canonical=folder/f'candidate_{cid:02d}_canonical';log=(src/'native.log').read_text();reload=(canonical/'reload.log').read_text()
  assert 'VPR succeeded' in log and 'VPR succeeded' in reload and 'Completed routing consistency check successfully.' in reload
  wl=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);reload_cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',reload)[-1]);assert wl==row['wirelength'] and cpd==reload_cpd==row['diagnostic_cpd_ns'];assert load(src/'physical_audit.json')['overflow_units']==0
  assert sequences(src/'output.route')==sequences(canonical/'design.route');assert (canonical/'design.net').read_bytes()==(canonical/'design.net.post_routing').read_bytes()
  table=list(map(json.loads,(canonical/'identity.jsonl').open()));allowed=Counter()
  for net in table:
   if net['ignored']:
    for pin in net['pins']:
     if pin['index']>0:allowed[net['name'],pin['block'],pin['x'],pin['y'],pin['layer'],pin['port'],pin['bit']]+=1
  pattern=re.compile(r"Fixed up net '([^']*)' mapping mismatch at clustered block '(.*)' pin 'grid\[(\d+)\]\[(\d+)\]\.([^.]*)\.([^\[]*)\[(\d+)\] - layer (\d+)' \(was net '([^']*)'\)");observed=Counter()
  for m in pattern.finditer(reload):
   routed,block,x,y,tile,port,bit,layer,old=m.groups();assert routed=='unmapped';observed[old,block,int(x),int(y),int(layer),port,int(bit)]+=1
  mis=re.search(r'Found (\d+) mismatches',reload);fix=re.search(r'Fixed (\d+) routing traces',reload);assert not observed-allowed and sum(observed.values())==int(mis[1])==int(fix[1]);checks.append(dict(candidate_id=cid,wirelength=wl,diagnostic_cpd_ns=cpd,ignored_only_counter=int(mis[1]),sequences_and_packed_bytes_identical=True))
 baseline=result['rows'][0];trial=result['rows'][-1];accepted=result['selected_candidate']!=0 and trial['wirelength']<baseline['wirelength'] and trial['diagnostic_cpd_ns']<=baseline['diagnostic_cpd_ns'];assert accepted==result['accepted'];assert result['final_candidate']==(result['selected_candidate'] if accepted else 0)
 return checks

def main():
 start=time.perf_counter();protocol=load(D/'protocol.json');results=load(D/'results.json')['results'];assert [r['arm'] for r in results]==['off','on'];bindings=dict(protocol['bindings']);checks=[]
 def proof(path):
  p=load(path)
  for f,h in p.get('bindings',{}).items():assert f not in bindings or bindings[f]==h;bindings[f]=h
  bindings[str(path)]=sha(path);return p
 old=load(E/'xtea_placement_feedback_cohort_v2_2026-10-13/protocol.json')
 for result in results:
  arm=result['arm'];out=D/arm;stages=load(out/'stages.json');assert all(s['exit_code']==0 for s in stages);assert abs(sum(s['seconds'] for s in stages)-result['stage_seconds_sum'])<1e-9;assert result['total_driver_seconds']>=result['stage_seconds_sum'];cv=proof(out/'cohort/verification.json');cp=load(out/'cohort/protocol.json');assert cp['selected']==old['selected'];assert [r['candidate_id'] for r in cv['rows']]==list(range(1,9));decision=load(out/'decision.json');base_ep=load(Path(cp['baseline_endpoint']));original_place=placements(base_ep['inputs']['place']['path'],base_ep['inputs']['net']['sha256']);mapping=load(Path(base_ep['inputs']['net']['path']).parent/'mapping.json');included={q['net_id'] for q in base_ep['connections']};members=defaultdict(set)
  for pin in mapping['pin_details']:
   if pin['net_id'] in included:members[pin['net_id']].add(pin['block'])
  def hpwl(pos):return sum(max(pos[n][0] for n in names)-min(pos[n][0] for n in names)+max(pos[n][1] for n in names)-min(pos[n][1] for n in names) for names in members.values())
  assert hpwl(original_place)==cp['baseline_hpwl'];byid={r['candidate_id']:r for r in decision['candidates']};expected_stages={'cohort','selected_native_and_gate'}
  for row,frozen in zip(cv['rows'],cp['selected']):
   cid=row['candidate_id'];ep=load(Path(row['endpoint']));pos=placements(ep['inputs']['place']['path'],ep['inputs']['net']['sha256']);a,b=frozen['pair'];assert {n for n in pos if pos[n]!=original_place[n]}=={a,b};assert pos[a][:4]==original_place[b][:4] and pos[b][:4]==original_place[a][:4];assert hpwl(pos)==row['hpwl']==byid[cid]['hpwl']
   if arm=='on':
    model=out/f'candidate_{cid:02d}/model';prior=E/f'xtea_placement_feedback_decisions_v1_2026-10-13/candidate_{cid:02d}/model'
    for n in ['initial.json','sketch.json']:assert load(model/n)==load(prior/n)
    for n in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:assert proof(model/n)['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
    assert byid[cid]['sketch_overflow']==load(model/'sketch.json')['overflow_units'];expected_stages|={f'candidate_{cid:02d}_{suffix}' for suffix in ['prepare','model','initial_audit','sketch_audit','event_audit']};warm=proof(out/f'candidate_{cid:02d}/prepared/warm/verification.json');assert Path(warm['previous_model'])==out/'prior'
  if arm=='on':
   expected_stages|={'prior_model','prior_initial_audit','prior_sketch_audit','prior_event_audit'}
   for n in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:assert proof(out/'prior'/n)['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
   admissible=[r for r in byid.values() if r['sketch_overflow']<=byid[0]['sketch_overflow']]
  else:admissible=list(byid.values())
  assert {s['stage'] for s in stages}==expected_stages and len(stages)==len(expected_stages);selection=min(admissible,key=lambda r:(r['hpwl'],r['candidate_id']))['candidate_id'];assert selection==decision['selected_candidate']==result['selected_candidate']==(1 if arm=='off' else 8);native=load(out/'native/result.json');assert native['selected_candidate']==selection and native['accepted']==result['accepted'];native_rows=native_checks(out/'native',native);checks.append(dict(arm=arm,stages=len(stages),selection=selection,native=native_rows,total_driver_seconds=result['total_driver_seconds']))
 for p,h in bindings.items():assert sha(p)==h,p
 off,on=results;ratio=on['total_driver_seconds']/off['total_driver_seconds'];out=dict(status='FRESH_PAIRED_BOUNDARY_STAGES_GEOMETRY_PRIOR_AUDITS_AND_NATIVE_GATES_VERIFIED',checks=checks,on_over_off_time_ratio=ratio,observed_positive_time_gain=ratio<1,upstream_capture_unpaid=True,original_full9_gate=False,independent_audit_seconds=time.perf_counter()-start,scope='One sequential developmentpair,not statistical or fullfromHDL evidence. Parent/child RSS fields are cumulative highwater and not independent perarm memorycomparison. Nonzero ignored-only canonical counters retained;originalzero gate not claimed.',bindings={**bindings,str(D/'results.json'):sha(D/'results.json'),str(Path(__file__)):sha(__file__)})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'],ratio)
if __name__=='__main__':main()
