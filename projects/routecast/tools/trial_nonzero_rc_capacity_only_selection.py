"""Relaxed parent constraint diagnostic on the unchanged finite candidate pool."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_candidate_joint_selection_2026-10-06';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==v['receipt_sha256'];import xml.etree.ElementTree as ET
xml=ET.parse(root/'work/nonzero_rc_fanout_observable64_2026-10-06/rr_graph.xml').getroot();caps={int(n.get('id')):int(n.get('capacity')) for n in xml.find('rr_nodes')};paths={tuple(c['key']):c['paths'] for c in r['candidates']};refs=Counter();demand=Counter();chosen={};states=0;limited=False

def valid(key,p):return all(refs[(key[0],n)] or demand[n]<caps[n] for n in p['nodes'])
def adjust(key,p,sign):
 for n in p['nodes']:
  old=refs[(key[0],n)];refs[(key[0],n)]+=sign
  if old==0 and sign==1:demand[n]+=1
  if refs[(key[0],n)]==0 and sign==-1:demand[n]-=1

def solve():
 global states,limited
 if len(chosen)==len(paths):return True
 if states>=10000:limited=True;return False
 states+=1;options={k:[i for i,p in enumerate(ps) if valid(k,p)] for k,ps in paths.items() if k not in chosen};key=min(options,key=lambda k:(len(options[k]),k))
 for i in options[key]:
  chosen[key]=i;adjust(key,paths[key][i],1)
  if solve():return True
  del chosen[key];adjust(key,paths[key][i],-1)
  if limited:return False
 return False
success=solve();parents=defaultdict(set)
for key,i in chosen.items():
 for n,u,eid in paths[key][i]['parents']:parents[(key[0],n)].add((u,eid))
bad=[{'net':net,'node':n,'parents':sorted(p)} for (net,n),p in parents.items() if len(p)>1];out=root/'experiments/nonzero_rc_capacity_only_selection_2026-10-06';out.mkdir();(out/'receipt.json').write_text(json.dumps({'status':'CAPACITY_ONLY_DIAGNOSTIC' if success else 'LIMIT' if limited else 'NO_SELECTION','choices':[{'key':list(k),'candidate':i} for k,i in sorted(chosen.items())],'multi_parent_nodes':bad,'selection_states':states,'candidate_verification_sha256':sha(parent/'verification.json'),'source_sha256':sha(Path(__file__)),'scope':'Unchanged226-path pool, capacity-only relaxation, same10000-state bound. Any multi-parent forest is forbidden as native seed; not a full legal-route success.'},indent=2)+'\n');print(success,states,'choices',len(chosen),'multi-parents',len(bad))
