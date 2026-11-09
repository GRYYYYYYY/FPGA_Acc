"""Align freshly reproduced native setup paths by endpoint and exact printed arc."""
import hashlib,json,re
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb_ex5p_native_STA_path_alignment_20261015'
def parse(text):
 assert '# Unit scale: 1e-09 seconds' in text and '# Output precision: 3' in text
 expected=int(re.search(r'#Timing report of worst (\d+) path',text).group(1));paths=[]
 for match in re.finditer(r'^#Path\s+(\d+)[ \t]*\n(.*?)(?=^#Path\s|\Z)',text,re.M|re.S):
  number=int(match[1]);block=match[2];start=re.search(r'^Startpoint:\s*(.*?)\s+\(',block,re.M).group(1);end=re.search(r'^Endpoint\s*:\s*(.*?)\s+\(',block,re.M).group(1)
  arrival=Decimal(re.search(r'^data arrival time\s+(-?\d+\.\d+)\s*$',block,re.M).group(1));rows=[]
  for line in block.split('data arrival time',1)[0].splitlines():
   row=re.match(r'^(.*?)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',line)
   if row and re.search(r'\(\.[^)]+\)$',row[1].strip()):rows.append(dict(point=row[1].strip(),increment_ns=row[2],path_ns=row[3]))
  assert rows and rows[0]['point'].split(' (',1)[0]==start and rows[-1]['point'].split(' (',1)[0]==end and Decimal(rows[-1]['path_ns'])==arrival
  arcs=[];previous='<external>'
  for row in rows:arcs.append(dict(source=previous,target=row['point'],increment_ns=row['increment_ns']));previous=row['point']
  assert len({(a['source'],a['target']) for a in arcs})==len(arcs)
  residual=arrival-sum((Decimal(a['increment_ns']) for a in arcs),Decimal(0));assert abs(residual)<=Decimal('0.0005')*(len(arcs)+1)
  paths.append(dict(index=number,startpoint=start,endpoint=end,arrival_ns=str(arrival),increment_sum_rounding_residual_ns=str(residual),arcs=arcs))
 assert len(paths)==expected and [v['index'] for v in paths]==list(range(1,expected+1)) and len({v['endpoint'] for v in paths})==len(paths)
 return paths

def main():
 refs={}
 def sha(f):
  p=Path(f);key=str(p)
  if key not in refs:
   h=hashlib.sha256()
   with p.open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 x=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='three_native_route_STA_reanalyses_terminal_requires_path_review' and len(m['steps'])==3
 for obj in [x,json.loads((P/'launch_protocol.json').read_text()),*m['steps']]:
  for f,h in obj['source_sha256'].items():assert sha(f)==h,f
 cases={};worst={}
 for c,receipt in zip(x['cases'],m['steps']):
  assert c['label']==receipt['label'] and receipt['returncode']==0 and receipt['previous_report_byte_equal']
  d=Path(c['cwd']);text=(d/'analysis.stdout').read_text();cpd=Decimal(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1]);assert cpd==Decimal(str(c['expected_native_cpd_ns']))
  rpt=d/'report_timing.setup.rpt';assert rpt.read_bytes()==Path(c['previous_report']).read_bytes();paths=parse(rpt.read_text());assert len(paths)==63
  assert abs(Decimal(paths[0]['arrival_ns'])-cpd)<=Decimal('0.0005') and max(Decimal(v['arrival_ns']) for v in paths)==Decimal(paths[0]['arrival_ns'])
  cases[c['label']]=paths;worst[c['label']]=dict(native_cpd_ns=str(cpd),printed_arrival_ns=paths[0]['arrival_ns'],startpoint=paths[0]['startpoint'],endpoint=paths[0]['endpoint']);sha(rpt)
 baseline={v['endpoint']:v for v in cases['baseline']};comparisons=[]
 for label in ['weight128','weight0']:
  assert {v['endpoint'] for v in cases[label]}==set(baseline);rows=[]
  for new in cases[label]:
   old=baseline[new['endpoint']];before={(a['source'],a['target']):Decimal(a['increment_ns']) for a in old['arcs']};after={(a['source'],a['target']):Decimal(a['increment_ns']) for a in new['arcs']};common=set(before)&set(after)
   common_rows=[dict(source=k[0],target=k[1],baseline_ns=str(before[k]),candidate_ns=str(after[k]),delta_ns=str(after[k]-before[k])) for k in sorted(common)];common_rows.sort(key=lambda v:Decimal(v['delta_ns']),reverse=True)
   removed=[dict(source=k[0],target=k[1],increment_ns=str(before[k])) for k in sorted(set(before)-common)];added=[dict(source=k[0],target=k[1],increment_ns=str(after[k])) for k in sorted(set(after)-common)]
   delta=Decimal(new['arrival_ns'])-Decimal(old['arrival_ns']);common_sum=sum((after[k]-before[k] for k in common),Decimal(0));residual_delta=Decimal(new['increment_sum_rounding_residual_ns'])-Decimal(old['increment_sum_rounding_residual_ns']);accounted=common_sum+sum((Decimal(a['increment_ns']) for a in added),Decimal(0))-sum((Decimal(a['increment_ns']) for a in removed),Decimal(0))+residual_delta;assert accounted==delta
   rows.append(dict(endpoint=new['endpoint'],baseline_startpoint=old['startpoint'],candidate_startpoint=new['startpoint'],startpoint_changed=old['startpoint']!=new['startpoint'],baseline_printed_arrival_ns=old['arrival_ns'],candidate_printed_arrival_ns=new['arrival_ns'],printed_arrival_delta_ns=str(delta),common_arc_delta_sum_ns=str(common_sum),rounding_residual_delta_ns=str(residual_delta),common_arcs=common_rows,baseline_only_arcs=removed,candidate_only_arcs=added))
  critical=next(v for v in rows if v['endpoint']==worst[label]['endpoint']);comparisons.append(dict(candidate=label,higher_printed_arrival_endpoints=sum(Decimal(v['printed_arrival_delta_ns'])>0 for v in rows),lower_printed_arrival_endpoints=sum(Decimal(v['printed_arrival_delta_ns'])<0 for v in rows),equal_printed_arrival_endpoints=sum(Decimal(v['printed_arrival_delta_ns'])==0 for v in rows),candidate_critical_endpoint=critical,endpoints=rows))
 # Unit and missing-arrival failures must not silently produce a partial alignment.
 sample=(P/'baseline/report_timing.setup.rpt').read_text();negative=[]
 for bad in [sample.replace('# Unit scale: 1e-09 seconds','# Unit scale: 1e-12 seconds',1),sample.replace('data arrival time','missing arrival summary',1)]:
  try:parse(bad)
  except (AssertionError,AttributeError):negative.append(True)
 assert len(negative)==2
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='three_ex5p_native_STA_reports_reproduced_and63endpoints_aligned',worst_paths=worst,comparisons=comparisons,paths=cases,parser_negative_controls_rejected=2,printed_resolution_ns='0.001',source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Read-only reanalysis of three fixed legal ex5p routes with same source-bound VPR/input command. Exact nativeCPD and all old setup-report bytes reproduce. One selected worst path per endpoint, not all start/end paths. Exact printed-arc pairs compared; unmatched path portions and rounding residuals separately retained. Rounded descriptive timing-arc changes, not additive causal CPD attribution, rerouting counterfactual, physical U280 timing, quality adoption or tolerance relaxation.')
 with (P/'independent_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps(dict(worst_paths=worst,comparisons=[dict(candidate=v['candidate'],higher=v['higher_printed_arrival_endpoints'],lower=v['lower_printed_arrival_endpoints'],critical_endpoint=v['candidate_critical_endpoint']['endpoint'],critical_printed_delta_ns=v['candidate_critical_endpoint']['printed_arrival_delta_ns'],top_common_arc_deltas=v['candidate_critical_endpoint']['common_arcs'][:3]) for v in comparisons])))
if __name__=='__main__':main()
