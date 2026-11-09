"""Prefix-only occupancy intervals; never turn absent overflow into empty state."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET,sys
from array import array
from collections import Counter
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def main():
 assert sys.byteorder=='little';out=R/'experiments/mmc_first_checkpoint_occupancy_bounds_v1_2026-10-19';out.mkdir();splitroot=R/'experiments/mmc_prefix_future_pressure_split_v1_2026-10-18';split=json.loads((splitroot/'verification.json').read_text());epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';ep=json.loads(epfile.read_text());graph=pathlib.Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings={str(p):sha(p) for p in [pathlib.Path(__file__).resolve(),splitroot/'verification.json',splitroot/'feature_boundary_verification_v1.json',epfile,graph]};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cutoff_iteration=1,phase='iteration_end_after_local_opins',rule='Tracked tree occupancy is a lower bound. Printed overused RR has exact observed occupancy. An unprinted RR is only bounded above by capacity at this complete checkpoint; external nonNET occupancy is not assumed zero.',scope='Already exposed partial-seed prefix state. No future records read, pressure labels changed, complete occupancy claimed or predictor trained.'),indent=2)+'\n')
 caps=array('I');stack=[]
 for event,node in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(node);continue
  if node.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':assert int(node.get('id'))==len(caps);caps.append(int(node.get('capacity')));stack[-2].remove(node);node.clear()
  if node.tag=='rr_nodes':break
  stack.pop()
 cp=out/'capacities.u32';cp.write_bytes(caps.tobytes());rows=[]
 for row in split['cases']:
  case,policy=row['case'],row['policy'];trace=R/f'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18/{case}/{policy}/owner_trace.tsv';end=row['first_checkpoint_end_byte'];tracked=Counter();observed={};nets=set();active=False;ends=0;digest=hashlib.sha256()
  with trace.open('rb') as f:
   while f.tell()<end:
    line=f.readline();assert line and f.tell()<=end;digest.update(line);w=line.split()
    if w[:1]==[b'CP']:assert int(w[2])<=1;active=w[1:]==[b'iteration_end_after_local_opins',b'1']
    elif active and w[:1]==[b'T']:
     net,ignored,present,remaining,count=map(int,w[1:6]);ns=list(map(int,w[6:]));assert net not in nets and len(ns)==count and len(set(ns))==count and ns==sorted(ns);nets.add(net);assert all(0<=n<len(caps) for n in ns);tracked.update(ns)
    elif active and w[:1]==[b'V']:
     n,occ,cap=map(int,w[1:]);assert n not in observed and caps[n]==cap and occ>cap;observed[n]=occ
    elif active and w==[b'CE']:ends+=1;active=False
   assert f.tell()==end and ends==1 and nets
  feature=splitroot/f'{case}_{policy}/features.json';first=json.loads(feature.read_text());assert sha(feature)==row['feature_sha256'];assert {str(n):occ-caps[n] for n,occ in observed.items()}==first['overflow_units_by_rr'];lower=array('I');upper=array('I');tree=array('I');ambiguous=0
  for n,cap in enumerate(caps):
   known=tracked.get(n,0);tree.append(known)
   if n in observed:assert observed[n]>=known;lo=hi=observed[n]
   else:assert known<=cap;lo,hi=known,cap
   lower.append(lo);upper.append(hi);ambiguous+=lo!=hi
  folder=out/f'{case}_{policy}';folder.mkdir();files={}
  for name,data in [('tracked_NET_occupancy',tree),('lower_occupancy',lower),('upper_occupancy',upper)]:
   p=folder/(name+'.u32');p.write_bytes(data.tobytes());files[name]={'path':str(p),'sha256':sha(p),'values':len(caps),'dtype':'little_endian_uint32'}
  manifest=dict(schema='MMC_PREFIX_OCCUPANCY_INTERVALS_V1',case=case,policy=policy,graph_sha256=ep['graph_sha256'],cutoff_iteration=1,phase='iteration_end_after_local_opins',prefix_end_byte=end,prefix_sha256=digest.hexdigest(),capacities={'path':str(cp),'sha256':sha(cp)},arrays=files,external_occupancy_assumed_zero=False);(folder/'features.json').write_text(json.dumps(manifest,indent=2)+'\n');rows.append(dict(case=case,policy=policy,NET_snapshots=len(nets),RR_domain=len(caps),exact_interval_resources=len(caps)-ambiguous,ambiguous_interval_resources=ambiguous,observed_overused_resources=len(observed),manifest=str(folder/'features.json'),manifest_sha256=sha(folder/'features.json')));print(case,policy,ambiguous,flush=True)
 result=dict(status='six_prefix_occupancy_interval_features_extracted_verification_pending',bindings=bindings,cases=rows,scope='Lower/upper intervals only; no proof that unknown nonNET occupancy is zero. Full tree snapshots at the admitted prefix endpoint are used, without future route records.',accepted_gain=False,strict_unseen_admitted=False);(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
