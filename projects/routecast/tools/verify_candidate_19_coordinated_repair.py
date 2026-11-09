"""Verify coordinated release and independently inspect conflict ownership and delay."""
import json,re
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
from buffered_rc_node_classes import read,arc_delay
from immutable_xml_prediction_audit import ImmutableXMLAudit
root=Path(__file__).resolve().parents[1];out=root/'experiments/candidate_19_coordinated_repair_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_candidate_19_coordinated_repair.py')==r['source_sha256'];cmd=r['results'][0]['command'];graph=cmd[cmd.index('--read_rr_graph')+1];digest=sha(graph);ids,classes,switches,_=read(graph);original=ImmutableXMLAudit(graph,digest);results=[]
for row in r['results']:
 assert all(sha(p)==h for p,h in row['files_sha256'].items()) and sha(row['command'][0])==row['binary_sha256'];cwd=Path(row['cwd']);log=(cwd/'run.log').read_text();assert 'RouterOpts.check_route: FULL' in log and 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log;names=set(row['selected_names']);visits=set(re.findall(r'ROUTECAST_DIRTY_REPAIR net=\d+ name=(.*)',log));assert names<=visits;released=re.findall(r'ROUTECAST_PRERELEASE net=\d+ name=(.*)',log);assert len(released)==len(set(released));assert set(released)==(names if row['arm']=='expanded_prerelease' else set());assert 'new_n758' in names if row['arm']!='control' else 'new_n758' not in names
 cur=None;name=None;prev=None;switch=None;parents={};used=set();owners=set();target=[];members={};connections=0
 for line in (cwd/'output.route').read_text().splitlines():
  m=NET.match(line)
  if m:cur=int(m[1]);name=m[2];prev=None;parents={};members[cur]=set()
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2];members[cur].add(node)
  if node==11015:owners.add(name)
  if kind=='SOURCE':parents[node]=[(node,None)]
  elif kind=='SINK':
   pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);path=parents[prev]+[(node,switch)];connections+=1
   if name=='new_n761':
    rr=path[0][0];res,cap=classes[ids[rr]];delay=res*cap/2
    for rr,s in path[1:]:delay+=arc_delay(classes,switches,ids[rr],s)
    target.append({'pin':pin,'sink':node,'xml_delay_ns':float(delay)*1e9,'path':path})
  elif node not in parents:parents[node]=parents[prev]+[(node,switch)]
  prev=node;switch=int(m[3])
 from collections import Counter
 ledger=Counter(n for nodes in members.values() for n in nodes);assert all(v<=original.caps[n] for n,v in ledger.items());assert connections==516;results.append({'arm':row['arm'],'cpd_ns':row['cpd_ns'],'connections':connections,'node_11015_capacity':original.caps[11015],'node_11015_owners':sorted(owners),'new_n761':target,'search_counts':row['search_counts'],'selected_nets':len(names),'released_nets':len(released)})
(out/'verification.json').write_text(json.dumps({'results':results,'graph_sha256':digest,'receipt_sha256':sha(out/'receipt.json'),'scope':'Native FULL logs, all requested selections/prereleases and XML NET-union capacities checked; input trial separately audits physical arcs. Candidate-19 diagnosed blocker came from retrospective cold-route comparison. All arms have same CPD; releasing blocker/cohort is not sufficient for native timing improvement. No general repair benefit or optimality claim.'},indent=2)+'\n');print([(x['arm'],x['node_11015_owners'],x['released_nets'],[(y['sink'],y['xml_delay_ns']) for y in x['new_n761']]) for x in results])
