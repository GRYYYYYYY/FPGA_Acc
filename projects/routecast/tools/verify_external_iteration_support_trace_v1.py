"""Validate exact trace coverage, original XML CHANNEL identities and endpoint sets."""
import json,sys
from pathlib import Path
from collections import Counter
from xml.parsers import expat
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from verify_external_initial_response_observer_source_v1 import trees
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_iteration_support_observer_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 m=read(D/'manifest.json');ep=read(m['cases'][0]['endpoint']);channels=set();parser=expat.ParserCreate();stack=[]
 def start(tag,a):
  if tag=='node' and stack and stack[-1]=='rr_nodes' and a['type'] in ['CHANX','CHANY']:channels.add(int(a['id']))
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 parser.StartElementHandler=start;parser.EndElementHandler=end
 with open(ep['inputs']['graph']['path'],'rb') as f:parser.ParseFile(f)
 cases=[m['cases'][0]]
 if (D/'targets_terminal.json').exists():cases+=read(D/'target_manifest.json')['cases']
 results=[];bindings={str(Path(__file__).resolve()):sha(__file__)}
 for c in cases:
  folder=Path(c['output']);audit=read(folder/'verification.json');assert audit['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and all(sha(p)==h for p,h in audit['bindings'].items());nets={q['net_id'] for q in read(c['endpoint'])['connections']};iteration=1;group={};first=None;count=0
  with (folder/'iteration_support.tsv').open() as stream:
   for line in stream:
    x=list(map(int,line.split()));it,net,n=x[:3];nodes=x[3:]
    if it!=iteration:
     assert it==iteration+1 and group.keys()==nets
     if first is None:first=group
     group={};iteration=it
    assert net in nets and net not in group and len(nodes)==n and nodes==sorted(set(nodes)) and set(nodes)<=channels;group[net]=set(nodes);count+=1
  assert group.keys()==nets and iteration==audit['iterations'];assert count==iteration*len(nets)
  if first is None:first=group
  def supports(path):return {n:{int(x.split()[1]) for x in rows if x.split()[2] in ['CHANX','CHANY']} for n,rows in trees(path).items() if n in nets}
  assert first==supports(folder/'first_iteration.route');final=supports(folder/'output.route');different=sum(group[n]!=final[n] for n in nets);results.append(dict(case=c['case'],iterations=iteration,NET_rows=count,first_snapshot_matches_printed_route=True,last_snapshot_vs_selected_final_changed_NETs=different))
  for p in [folder/'iteration_support.tsv',folder/'verification.json',folder/'first_iteration.route',folder/'output.route']:bindings[str(p)]=sha(p)
 name='all_case_trace_verification_v1.json' if len(cases)==4 else 'source_trace_verification_v1.json'
 with (D/name).open('x') as f:json.dump(dict(status='EXACT_TRACE_ITERATION_COVERAGE_XML_CHANNEL_IDENTITIES_AND_FIRST_SNAPSHOT_VERIFIED',rows=results,bindings=bindings,scope='Exact sorted sets, no digest collision assumption. Internal intermediate support sets are production observations; first snapshot independently parsed from physical route. Last iteration need not equal selected best final route.'),f,indent=2)
 print(json.dumps(results))
if __name__=='__main__':main()
