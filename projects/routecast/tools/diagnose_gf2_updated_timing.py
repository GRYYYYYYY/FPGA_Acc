"""Posthoc descriptive timing diagnosis; never supplies frozen predictor inputs."""
import json,re
from decimal import Decimal
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1]
out=root/'experiments/gf2_recurrence_updated_timing_diagnosis_2026-10-06';out.mkdir()
quality=root/'experiments/gf2_recurrence_updated_quality_2026-10-06/verification.json'
inputs={str(quality):sha(quality)}
for w in (32,64,128):
 for suffix in ('updated_native_import','swapped_place_cold'):
  p=root/f'work/gf2_d{w}_{suffix}_2026-10-06/report_timing.setup.rpt';inputs[str(p)]=sha(p)
 for p in (root/f'experiments/gf2_d{w}_placement_swap_2026-10-06/endpoints.json',root/f'experiments/gf2_recurrence_placement_updates_2026-10-06/gf2_d{w}/receipt.json'):
  inputs[str(p)]=sha(p)
protocol={'inputs_sha256':inputs,'source_sha256':sha(Path(__file__)),'scope':'Posthoc diagnosis of reported worst32 setup paths, rounded to .001ns. Classify LUT output increments versus interconnect input/output-pad increments; pair only identical full ordered point sequences, never claim complete path population. Net membership from prior driver atom name with unique output in BLIF. No feedback to frozen transfer/search or causal ablation claim.'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
point=re.compile(r'^(\S+) \((\.\w+)\)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$')
def parse(path,external,affected,drivers):
 text=path.read_text();assert '# Unit scale: 1e-09 seconds' in text and '# Output precision: 3' in text
 paths=[]
 for chunk in re.split(r'^#Path ',text,flags=re.M)[1:]:
  rank=int(chunk.splitlines()[0]);start=re.search(r'^Startpoint: (.*?) \(',chunk,re.M)[1];end=re.search(r'^Endpoint\s*: (.*?) \(',chunk,re.M)[1]
  arrival=Decimal(re.search(r'^data arrival time\s+([0-9.]+)',chunk,re.M)[1]);pts=[];logic=Decimal(0);wire=Decimal(0);groups={k:Decimal(0) for k in ('affected_external','retained_external','not_external')};previous=None
  for line in chunk.splitlines():
   m=point.match(line)
   if not m:continue
   name,kind,inc,cum=m.groups();inc=Decimal(inc)
   if kind=='.input':assert inc==0;category='launch'
   elif kind=='.names' and '.out[' in name:category='logic';logic+=inc
   elif (kind=='.names' and '.in[' in name) or kind=='.output':
    category='interconnect';wire+=inc;assert previous is not None
    driver=previous.rsplit('.',1)[0];assert driver in drivers
    net=drivers[driver];group='affected_external' if net in affected else 'retained_external' if net in external else 'not_external';groups[group]+=inc
   else:raise AssertionError((name,kind))
   pts.append({'point':name,'kind':kind,'increment_ns':str(inc),'cumulative_ns':cum,'category':category,**({'driver_net':net,'net_group':group} if category=='interconnect' else {})});previous=name
  assert pts and pts[0]['point']==start and pts[-1]['point']==end
  assert abs(logic+wire-arrival)<=Decimal('0.0005')*(len(pts)+1)
  assert sum(groups.values())==wire
  paths.append({'rank':rank,'startpoint':start,'endpoint':end,'arrival_ns':str(arrival),'logic_ns':str(logic),'interconnect_ns':str(wire),'interconnect_group_ns':{k:str(v) for k,v in groups.items()},'points':pts})
 assert len(paths)==32 and [p['rank'] for p in paths]==list(range(1,33));return paths
rows=[]
for decision in json.loads(quality.read_text())['rows']:
 w=decision['width'];ep=json.loads((root/f'experiments/gf2_d{w}_placement_swap_2026-10-06/endpoints.json').read_text());update=json.loads((root/f'experiments/gf2_recurrence_placement_updates_2026-10-06/gf2_d{w}/receipt.json').read_text());external=set(ep['net_names'].values());affected={ep['net_names'][str(n)] for n in update['affected']['affected_net_ids']}
 blif=root/f'work/gf2_d{w}_updated_native_import_2026-10-06/design.blif';drivers={}
 for line in blif.read_text().replace('\\\n',' ').splitlines():
  if line.startswith('.inputs '):
   for n in line.split()[1:]:drivers[n]=n
  elif line.startswith('.names '):n=line.split()[-1];assert n not in drivers;drivers[n]=n
 # This mapped ABC BLIF uses single-output .names atom names identical to their output nets.
 cand=parse(root/f'work/gf2_d{w}_updated_native_import_2026-10-06/report_timing.setup.rpt',external,affected,drivers);ref=parse(root/f'work/gf2_d{w}_swapped_place_cold_2026-10-06/report_timing.setup.rpt',external,affected,drivers)
 for paths,cpd in ((cand,decision['candidate_cpd_ns']),(ref,decision['same_placement_reference_cpd_ns'])):assert abs(Decimal(paths[0]['arrival_ns'])-Decimal(str(cpd)))<=Decimal('.0005')
 def key(p):return tuple((v['point'],v['kind']) for v in p['points'])
 index={key(p):p for p in ref};assert len(index)==len(ref)
 pairs=[]
 for p in cand:
  if key(p) in index:
   q=index[key(p)];pairs.append({'candidate_rank':p['rank'],'reference_rank':q['rank'],'arrival_delta_ns':str(Decimal(p['arrival_ns'])-Decimal(q['arrival_ns'])),'logic_delta_ns':str(Decimal(p['logic_ns'])-Decimal(q['logic_ns'])),'interconnect_delta_ns':str(Decimal(p['interconnect_ns'])-Decimal(q['interconnect_ns'])),'edge_deltas':[{'point':x['point'],'driver_net':x['driver_net'],'net_group':x['net_group'],'delta_ns':str(Decimal(x['increment_ns'])-Decimal(y['increment_ns']))} for x,y in zip(p['points'],q['points']) if x['category']=='interconnect']})
 detail={'width':w,'candidate_paths':cand,'reference_paths':ref,'identical_ordered_point_sequence_pairs':pairs,'blif_sha256':sha(blif)};(out/f'gf2_d{w}.json').write_text(json.dumps(detail,indent=2)+'\n')
 row={'width':w,'candidate_top1':{k:v for k,v in cand[0].items() if k!='points'},'reference_top1':{k:v for k,v in ref[0].items() if k!='points'},'top1_same_ordered_point_sequence':key(cand[0])==key(ref[0]),'matched_reported_sequences':len(pairs),'detail_sha256':sha(out/f'gf2_d{w}.json')};rows.append(row);print(json.dumps(row),flush=True)
assert all(sha(p)==h for p,h in inputs.items())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'scope':protocol['scope']},indent=2)+'\n')
