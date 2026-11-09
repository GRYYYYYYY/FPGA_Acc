"""All227 positives, wrong identity/phase epochs and malformed bound payload tests."""
import json,copy,hashlib
from pathlib import Path
from pre_route_endpoints import sha
from load_prince_resident_observation_v1 import Consumer
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_resident_consumer_contract_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);vp=E/'prince_resident_consumer_v1_2026-10-20/verification.json';v=json.loads(vp.read_text());consumer=Consumer();positive=negative=immutable=0;bindings={str(p):sha(p) for p in [vp,Path(__file__),R/'tools/load_prince_resident_observation_v1.py']};first=None
 def reject(path,identity):
  try:consumer.load(path,identity)
  except (ValueError,KeyError):return
  raise AssertionError('invalid observation admitted')
 for row in v['rows']:
  p=Path(row['manifest']);assert sha(p)==row['sha256'];d=json.loads(p.read_text());identity=d['identity'];state=consumer.load(p,identity);assert len(state['RR'])==d['node_count'] and len(state['boxes'])==d['NET_count'];positive+=1;bindings[str(p)]=sha(p)
  for key in identity:
   wrong=dict(identity);wrong[key]=identity[key]+1 if key=='iteration' else ('wrong_case' if key=='case' else ('wrong_phase' if key=='phase' else '0'*64));reject(p,wrong);negative+=1
  for obj,key in [(state,'overuse_units'),(state['identity'],'iteration'),(state['boxes'],0)]:
   try:obj[key]=None
   except TypeError:immutable+=1
   else:raise AssertionError('mutable consumer context')
  if first is None:first=(p,d)
 p,base=first;identity=base['identity'];fixtures=D/'negative_fixtures';fixtures.mkdir();count=0
 def attempt(name,d):
  nonlocal count
  q=fixtures/(name+'.json');q.write_text(json.dumps(d,indent=2)+'\n');reject(q,identity);count+=1
 def payload(name,field,raw):
  d=copy.deepcopy(base);q=fixtures/(name+'.bin');q.write_bytes(raw);d['paths'][field]=str(q);d['bindings'][str(q)]=sha(q);attempt(name,d)
 payload('truncated_RR','RR',Path(base['paths']['RR']).read_bytes()[:-1]);payload('truncated_boxes','boxes',Path(base['paths']['boxes']).read_bytes()[:-1]);nextmanifest=json.loads(Path(v['rows'][1]['manifest']).read_text());payload('wrong_RR_iteration','RR',Path(nextmanifest['paths']['RR']).read_bytes());payload('wrong_box_iteration','boxes',Path(nextmanifest['paths']['boxes']).read_bytes())
 d=copy.deepcopy(base);d['phase_row'][1]+=1;attempt('wrong_phase_row',d)
 d=copy.deepcopy(base);d['units']['timing']='nanoseconds';attempt('wrong_units',d)
 d=copy.deepcopy(base);d['bindings'][d['paths']['RR']]='0'*64;attempt('changed_payload_digest',d)
 d=copy.deepcopy(base);d['bindings']={p:h for p,h in d['bindings'].items() if not p.endswith('/NET_mapping_verification.json')};attempt('missing_NET_mapping_proof',d)
 mapping=json.loads(Path(base['paths']['NET_mapping']).read_text());mapping[0]['endpoint_NET_id']=mapping[1]['endpoint_NET_id'];payload('nonbijective_NET_mapping','NET_mapping',json.dumps(mapping).encode())
 assert positive==227 and negative==1589 and immutable==681 and count==9;assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL227_COHERENT_CONTEXTS_1589_IDENTITY_AND9_PAYLOAD_REJECTIONS_PASS',positive_contexts=positive,identity_rejections=negative,payload_rejections=count,immutable_mapping_rejections=immutable,bindings=bindings,scope='Offline read-only snapshot consumer over trusted producer-bound manifests. Explicit nativeNET-name mapping and immutable context; tests cover graph/place/netlist/binary/phase/iteration identities, truncated/mixed payloads and mapping proof. Not authenticated hostile-manifest security, full resident state export, in-process decision hook or stop/restore proof.'),indent=2)+'\n');print('RESIDENT_CONSUMER_PASS',positive,negative,count,immutable)
if __name__=='__main__':main()
