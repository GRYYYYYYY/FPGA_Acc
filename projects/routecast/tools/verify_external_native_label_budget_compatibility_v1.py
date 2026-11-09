"""Independent original switch timing scan and printed-branch cumulative delays."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from xml.parsers import expat
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';D=E/'prospective_external_family_native_label_budget_compatibility_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 receipt=read(D/'verification.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());spec=read(P/'specifications/w160/episode_01/comparison_spec.json');ep=read(spec['endpoint']);graph=ep['inputs']['graph']['path'];stack=[];switch=None;weights={};parser=expat.ParserCreate()
 def start(tag,a):
  nonlocal switch
  if tag=='switch' and stack and stack[-1]=='switches':switch=int(a['id'])
  if tag=='timing' and stack and stack[-1]=='switch':
   assert switch is not None;assert all(F(a.get(k,'0'))==0 for k in ['R','Cin','Cout','Cinternal']);value=F(a.get('Tdel','0'))*10**18;assert value.denominator==1;weights[switch]=value.numerator
  if tag=='timing' and stack and stack[-1]=='node':assert F(a.get('R','0'))==F(a.get('C','0'))==0
  stack.append(tag)
 def end(tag):
  nonlocal switch
  assert stack.pop()==tag
  if tag=='switch':switch=None
 parser.StartElementHandler=start;parser.EndElementHandler=end
 with open(graph,'rb') as f:parser.ParseFile(f)
 results=[]
 for r in receipt['rows']:
  case=r['case'];route=P/'native'/case/'output.route';net=None;parent_delay={};previous=None;previous_switch=None;source=None;paths={}
  for line in route.open():
   words=line.split()
   if words and words[0]=='Net':net=int(words[1]);parent_delay={};previous=None;source=None
   elif words and words[0]=='Node:':
    node=int(words[1]);kind=words[2];sw=int(words[words.index('Switch:')+1])
    if kind=='SOURCE':source=node;parent_delay[node]=0
    elif kind=='SINK':
     key=(net,source,node);assert key not in paths;paths[key]=parent_delay[previous]+weights[previous_switch]
    elif node not in parent_delay:parent_delay[node]=parent_delay[previous]+weights[previous_switch]
    previous=node;previous_switch=sw
  spec=read(P/'specifications'/case/'comparison_spec.json');ep=read(spec['endpoint']);forecast=read(P/'predictions'/case/'native_retained_on/initial.json');budgets={q['connection_id']:q['budget_integer'] for q in forecast['records']};table=read(D/case/'all_CIDs.json');assert len(table)==len(ep['connections'])==len(paths);seen=set();over=0;NETs=set();maximum=0
  for q,row in zip(ep['connections'],table):
   assert row['connection_id']==q['connection_id'] and row['connection_id'] not in seen;seen.add(q['connection_id']);raw=paths[q['net_id'],q['source'],q['sink']];budget=budgets[q['connection_id']];assert raw==row['native_raw_delay_integer'] and budget==row['forecast_budget_integer'];assert (raw>budget)==row['over_budget'] and max(0,raw-budget)==row['excess_integer']
   if raw>budget:over+=1;NETs.add(q['net_id']);maximum=max(maximum,raw-budget)
  assert over==r['native_CIDs_over_forecast_budget'] and len(NETs)==r['NETs_with_native_over_budget'] and maximum==r['max_excess_integer'];results.append(dict(case=case,connections=len(table),native_over_budget=over))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL46848_NATIVE_RAW_DELAYS_AND_ORIGINAL_FORECAST_BUDGET_COMPARISONS_VERIFIED',rows=results,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Independent timing scan and branch cumulative delays. No budget/label/gate modification or ranking-impossibility claim.'),f,indent=2)
 print('ALL46848_NATIVE_BUDGET_COMPATIBILITY_ROWS_VERIFIED')
if __name__=='__main__':main()
