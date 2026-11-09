"""Exercise consumer -> current endpoint NET/CID and dynamic native BB joins."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
from load_prince_resident_observation_v1 import Consumer
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_consumer_endpoint_join_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);vp=E/'prince_resident_consumer_v1_2026-10-20/verification.json';v=json.loads(vp.read_text());consumer=Consumer();coords={};bindings={str(p):sha(p) for p in [vp,Path(__file__),R/'tools/load_prince_resident_observation_v1.py']};rows=[];checks=0
 for row in v['rows']:
  p=Path(row['manifest']);assert sha(p)==row['sha256'];m=json.loads(p.read_text());state=consumer.load(p,m['identity']);ep=E/'prince_native_cohort_v1_2026-10-20'/row['case']/'pre_route_endpoints.json';e=json.loads(ep.read_text());assert e['graph_sha256']==state['identity']['graph_sha256'] and e['inputs']['net']['sha256']==state['identity']['netlist_sha256'] and e['inputs']['place']['sha256']==state['identity']['placement_sha256'];graph=Path(e['inputs']['graph']['path']);gh=e['graph_sha256']
  if gh not in coords:
   locations={}
   for ev,x in ET.iterparse(graph):
    if x.tag=='node':
     loc=x.find('loc');locations[int(x.get('id'))]=(int(loc.get('xlow')),int(loc.get('xhigh')),int(loc.get('ylow')),int(loc.get('yhigh')),int(loc.get('layer','0')));x.clear()
    if x.tag=='edge':x.clear()
   coords[gh]=locations
  mapping={endpoint:(native,name,ignored) for native,endpoint,name,ignored in state['NET_mapping']};seen=set()
  for q in e['connections']:
   cid=q['connection_id'];net=q['net_id'];native,name,ignored=mapping[net];assert name==e['net_names'][str(net)] and not ignored;box=state['boxes'][net];assert box[0]==native;_,xmin,xmax,ymin,ymax,lmin,lmax=box
   for node in [q['source'],q['sink']]:
    xlow,xhigh,ylow,yhigh,layer=coords[gh][node];assert xmin<=xlow<=xhigh<=xmax and ymin<=ylow<=yhigh<=ymax and lmin<=layer<=lmax
   assert cid not in seen;seen.add(cid);checks+=1
  assert len(seen)==4802;rows.append(dict(case=row['case'],iteration=row['iteration'],CIDs=len(seen),native_endpoint_NET_name_and_roles_exact=True,all_current_endpoints_inside_native_BBs=True));bindings[str(ep)]=sha(ep);bindings[str(p)]=sha(p)
 assert checks==1090054 and len(rows)==227 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,checked_CID_phase_joins=checks,bindings=bindings,scope='Actual read-only consumer joins current endpoint CIDs via explicit nativeNET/name/role proof; each SOURCE/SINK span inside captured native dynamic BB. Geometry checks do not prove routing legality, timing/perpin criticality or forecast quality. No stop/restore or fullpaid gain.'),indent=2)+'\n');print('CONSUMER_ENDPOINT_JOIN_PASS',len(rows),checks)
if __name__=='__main__':main()
