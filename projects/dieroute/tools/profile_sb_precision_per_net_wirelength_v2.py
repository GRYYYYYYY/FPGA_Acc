"""Describe six completed SB3 development routes; do not reroute or select a winner."""
import csv,hashlib,json,re,subprocess,xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb_precision_per_net_wirelength_v2_20261015';D=R/'work/rr_remaining_tail_precision_development_v2_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(f):
  f=Path(f).resolve();key=str(f)
  if key not in refs:
   h=hashlib.sha256()
   with f.open('rb') as s:
    for b in iter(lambda:s.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 protocol=json.loads((D/'protocol.json').read_text());prior=json.loads((D/'independent_audit.json').read_text());assert len(prior['outcomes'])==6
 def nodes(f):
  result={};net=None
  for line in f.read_text().splitlines():
   m=re.match(r'^Net\s+(\d+)\s+\(',line)
   if m:net=int(m[1]);assert net not in result;result[net]=set()
   m=re.match(r'^\s*Node:\s*(\d+)\s+',line)
   if m:assert net is not None;result[net].add(int(m[1]))
  assert result;return result
 rows=[]
 for case in protocol['cases']:
  label=case['label'];assert label in ['ex5p','diffeq','alu4'];base=Path(case['native_case']);rr=base/'rr_graph.xml';route=base/'circuit.route';connections=Path(case['connections'])
  for f in [rr,route]:assert sha(f)==protocol['source_sha256'][str(f)],f
  spans={};kind={}
  for _,el in E.iterparse(rr,events=('end',)):
   if el.tag=='node':
    i=int(el.attrib['id']);t=el.attrib['type'];loc=el.find('loc');axis='x' if t=='CHANX' else 'y';spans[i]=int(loc.attrib[axis+'high'])-int(loc.attrib[axis+'low'])+1 if t in ['CHANX','CHANY'] else 0;kind[i]=t;el.clear()
   elif el.tag=='edge':el.clear()
  baseline=nodes(route);fanout=Counter()
  extraction_root=connections.parent.parent;extractor=extraction_root/'tools/vpr_route_connections.py';binding=extraction_root/'protocol.json';bound=json.loads(binding.read_text());assert sha(extractor)==bound['inputs'][str(extractor)]
  regenerated=P/(label+'_regenerated_connections.csv')
  with (P/(label+'_regeneration.log')).open('w') as out:subprocess.run(['python3',str(extractor),str(route),str(regenerated),'--criticality-q','32768','--max-hops','65535'],stdout=out,stderr=subprocess.STDOUT,check=True)
  assert sha(regenerated)==sha(connections),'frozen route connection regeneration mismatch';sha(binding)
  with connections.open() as f:
   for record in csv.DictReader(f):fanout[int(record['net_id'])]+=1
  before={net:sum(spans[n] for n in ns) for net,ns in baseline.items()};assert sum(before.values())==case['baseline_wirelength']
  for arm in protocol['arms']:
   arm=arm['label'];directory=D/'native_runs'/f'{label}_{arm}_0';candidate_path=directory/'native.route';vfile=directory/'native_validation/validation.json';validation=json.loads(vfile.read_text());assert validation['legal'] and validation['inputs']['route_sha256']==sha(candidate_path) and validation['inputs']['rr_graph_sha256']==sha(rr)
   candidate=nodes(candidate_path);assert candidate.keys()==baseline.keys();delta_rows=[];bins=Counter()
   for net,ns in candidate.items():
    after=sum(spans[n] for n in ns);delta_rows.append(dict(net_id=net,connections=fanout[net],baseline_wirelength=before[net],candidate_wirelength=after,delta=after-before[net]))
    for sign,changed in [(1,ns-baseline[net]),(-1,baseline[net]-ns)]:
     for n in changed:
      if spans[n]:bins[f'{kind[n]}_span{spans[n]}']+=sign*spans[n]
   delta_rows.sort(key=lambda row:(-row['delta'],row['net_id']));total=sum(row['candidate_wirelength'] for row in delta_rows);difference=total-sum(before.values());expected=next(v for v in prior['outcomes'] if v['case']==label and v['arm']==arm)
   assert total==validation['total_wirelength']==expected['wirelength'];assert difference==sum(row['delta'] for row in delta_rows)==sum(bins.values())
   outcome=dict(case=label,arm=arm,nets=len(delta_rows),baseline_wirelength=sum(before.values()),candidate_wirelength=total,net_delta=difference,gross_increase=sum(max(0,v['delta']) for v in delta_rows),gross_decrease=sum(min(0,v['delta']) for v in delta_rows),worse_nets=sum(v['delta']>0 for v in delta_rows),better_nets=sum(v['delta']<0 for v in delta_rows),equal_nets=sum(v['delta']==0 for v in delta_rows),exact_span_contributions=dict(sorted(bins.items())),net_deltas=delta_rows,original_joint_gate_pass=expected['joint_gate_pass'])
   rows.append(outcome);sha(vfile)
 for f in [D/'protocol.json',D/'independent_audit.json',Path(__file__).resolve()]:sha(f)
 result=dict(status='six_native_validated_SB3_precision_routes_per_net_wirelength_decomposed',outcomes=rows,source_sha256=refs,scope='Read-only complete native routes and exactRR CHANX/CHANY geometric span per unique net node. Baseline/candidate sums match all6native validation metrics. Connections additionally regenerate byte-exact using frozen roundtrip extractors; not claimed directly bound by original precision protocol. Gross and span-type changes are descriptive, not additive CPD attribution, causal effect, new routing, winner selection, heldout evidence or quality adoption.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps([{k:v for k,v in row.items() if k not in ['net_deltas','exact_span_contributions']} for row in rows]))
if __name__=='__main__':main()
