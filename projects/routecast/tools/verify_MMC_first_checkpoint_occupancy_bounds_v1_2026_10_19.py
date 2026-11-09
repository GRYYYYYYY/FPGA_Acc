"""Independent prefix snapshot replay, XML capacities and interval validation."""
import pathlib,json,hashlib,sys,xml.etree.ElementTree as ET
from array import array
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def main():
 assert sys.byteorder=='little';root=R/'experiments/mmc_first_checkpoint_occupancy_bounds_v1_2026-10-19';receipt=root/'receipt.json';r=json.loads(receipt.read_text());splitroot=R/'experiments/mmc_prefix_future_pressure_split_v1_2026-10-18';split=json.loads((splitroot/'verification.json').read_text());lookup={(x['case'],x['policy']):x for x in split['cases']};nativeproof=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18/cohort_verification.json';np=json.loads(nativeproof.read_text());assert np['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass'];epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';ep=json.loads(epfile.read_text());graph=pathlib.Path(ep['inputs']['graph']['path']);assert r['bindings'][str(graph)]==sha(graph)==ep['graph_sha256'];bindings={str(p):sha(p) for p in [pathlib.Path(__file__).resolve(),receipt,splitroot/'verification.json',nativeproof,epfile,graph]};capacities=[];stack=[]
 for action,elem in ET.iterparse(graph,events=('start','end')):
  if action=='start':stack.append(elem);continue
  if elem.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   assert int(elem.attrib['id'])==len(capacities);capacities.append(int(elem.attrib['capacity']));stack[-2].remove(elem);elem.clear()
  if elem.tag=='rr_nodes':break
  stack.pop()
 rows=[]
 for entry in r['cases']:
  case,policy=entry['case'],entry['policy'];manifest=pathlib.Path(entry['manifest']);assert sha(manifest)==entry['manifest_sha256'];m=json.loads(manifest.read_text());source=R/f'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18/{case}/{policy}/owner_trace.tsv';expected=lookup[case,policy];assert sha(source)==expected['source_trace_sha256']==np['bindings'][str(source)];counts=[0]*len(capacities);observed={};nets=set();active=False;digest=hashlib.sha256()
  with source.open('rb') as f:
   while True:
    line=f.readline();assert line;digest.update(line);words=line.split()
    if words[:1]==[b'CP']:
     assert int(words[2])<=1;active=words[1:]==[b'iteration_end_after_local_opins',b'1']
    elif active and words[:1]==[b'T']:
     net=int(words[1]);assert net not in nets;nets.add(net);nodes=[int(x) for x in words[6:]];assert len(nodes)==int(words[5])==len(set(nodes))
     for n in nodes:counts[n]+=1
    elif active and words[:1]==[b'V']:
     n,occ,cap=map(int,words[1:]);assert n not in observed and cap==capacities[n] and occ>cap;observed[n]=occ
    elif active and words==[b'CE']:assert f.tell()==expected['first_checkpoint_end_byte']==m['prefix_end_byte'];break
  assert digest.hexdigest()==m['prefix_sha256'];arrays={}
  for key,meta in m['arrays'].items():
   assert sha(meta['path'])==meta['sha256'];a=array('I');a.frombytes(pathlib.Path(meta['path']).read_bytes());assert len(a)==meta['values']==len(capacities);arrays[key]=a;bindings[meta['path']]=meta['sha256']
  assert list(arrays['tracked_NET_occupancy'])==counts;assert len(nets)==entry['NET_snapshots'];ambiguous=0
  for n,cap in enumerate(capacities):
   low,high=arrays['lower_occupancy'][n],arrays['upper_occupancy'][n]
   if n in observed:assert low==high==observed[n]>=counts[n]
   else:assert low==counts[n]<=high==cap
   ambiguous+=low!=high
  assert ambiguous==entry['ambiguous_interval_resources'];bindings[str(manifest)]=sha(manifest);bindings[str(source)]=expected['source_trace_sha256'];rows.append({'case':case,'policy':policy,'RR_intervals_verified':len(capacities),'ambiguous':ambiguous});print(case,policy,len(capacities),flush=True)
 result=dict(status='all6_prefix_tree_occupancies_and_full_XML_capacity_intervals_verified',bindings=bindings,cases=rows,scope='Exact tracked tree counts, observed overused occupancy and conservative bounds elsewhere at checkpoint1 only. NonNET occupancy in unobserved intervals remains unknown. No future record read by feature extraction, no pressure model trained, unseen admission or utility claim.',accepted_gain=False,strict_unseen_admitted=False)
 (root/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
