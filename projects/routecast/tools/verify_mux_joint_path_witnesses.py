"""Exact XML path witnesses and joint-sum accounting; not lower-bound proof."""
import json,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_joint_path_floors_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json')and len(r['rows'])==12;rows=[];previous=None
for c,row in zip(p['cases'],r['rows']):
 w=c['width'];i=c['index'];assert all(sha(f)==h for f,h in c['inputs'].items());file=out/f'w{w}_m{i}.json';assert sha(file)==row['sha256'];data=json.loads(file.read_text());ep=json.loads(Path(c['target']).read_text());queries={q['connection_id']:q for q in ep['connections']}
 if w!=previous:
  xml=ET.parse(ep['inputs']['graph']['path']).getroot();nodes={int(n.get('id')):n for n in xml.find('rr_nodes')};edges=[(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id')))for e in xml.find('rr_edges')];switches={int(s.get('id')):s for s in xml.find('switches')};previous=w
 delays={}
 for cid,a in data['answers'].items():
  q=a['query'];assert q==queries[int(cid)];answer=a['answer'];node=q['source'];t=nodes[node].find('timing');value=Fraction(t.get('R'))*Fraction(t.get('C'))/2;seen={node}
  for eid in answer['physical_edge_ids']:
   u,v,s=edges[eid];assert u==node and v not in seen and int(nodes[v].get('capacity'))>0;seen.add(v);node=v;t=nodes[v].find('timing');st=switches[s].find('timing');assert switches[s].get('type')in('buffer','mux','tristate');value+=(Fraction(st.get('R','0'))+Fraction(t.get('R'))/2)*Fraction(t.get('C'))+Fraction(st.get('Tdel','0'))
  assert node==q['sink']and Fraction(answer['delay'],data['scale'])==value;delays[int(cid)]=value*10**9
 for path in data['paths']:
  total=sum(delays[c]for c in path['connection_ids']);assert total==Fraction(path['relaxed_floor_sum_ns']);assert path['violated']==(total>Fraction(path['old_rr_plus_headroom_ns']))
 rows.append(dict(width=w,index=i,path_witnesses=len(delays),violated_paths=row['violated_paths'],constructive_joint_sum_feasible=row['violated_paths']==0,independent_minimum_optimality_proved=False))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='2684 XML/Fraction independent realizedpathdelay checks and jointsum arithmetic; zero-violation vectors are constructive relaxed independentconnection witnesses. Violations need independentminimum proof; no sharedNETtree/capacity/nativeSTA guarantee.'),indent=2)+'\n');print(sum(x['path_witnesses']for x in rows),sum(x['constructive_joint_sum_feasible']for x in rows))
