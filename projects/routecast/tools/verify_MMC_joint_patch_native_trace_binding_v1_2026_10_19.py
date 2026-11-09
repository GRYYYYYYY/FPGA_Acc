"""Independent all115572 model-to-native physical paths and actual pin-state delta."""
import pathlib,json,hashlib
from collections import defaultdict
from xml.parsers import expat
from native_route_ledger_import_compact import physical_paths
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_joint_patch_postroute_canonical_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 receipt=O/'receipt.json';c=json.loads(receipt.read_text());assert c['status']=='NATIVE_CANONICAL_SEMANTIC_FULL_STA_PHYSICAL_GATE_PASS'
 for p,h in {**c['bindings'],**c['files']}.items():assert sha(pathlib.Path(p))==h
 J=R/'experiments/mmc_branch_proposal_joint_bank_v1_2026-10-19';jp=J/'independent_verification_v1.json';j=json.loads(jp.read_text());assert j['status']=='ALL16_PROPOSAL_SUBSETS_AND_FULL115572_CONNECTION_RC_CAPACITY_STATE_VERIFIED';source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';assert sha(source)==j['bindings'][str(source)];frame=json.loads(source.read_text());patchp=J/'selected_connection_patch.json';assert sha(patchp)==j['bindings'][str(patchp)];patch={int(cid):x for cid,x in json.loads(patchp.read_text()).items()};geometry=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=pathlib.Path(geometry['previous_endpoint']);meta=json.loads(ep.read_text());graph=pathlib.Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];needed=set();target_sinks={q['sink'] for q in patch.values()}
 for q in frame['records']:needed.update(patch[q['connection_id']]['physical_edge_ids'] if q['connection_id'] in patch else q['answer']['physical_edge_ids'])
 edges={};count=0;stack=[];current_node=None;locations={}
 def start(tag,attrs):
  nonlocal count,current_node
  parent=stack[-1] if stack else None
  if tag=='node' and parent=='rr_nodes':current_node=int(attrs['id'])
  if tag=='loc' and parent=='node' and current_node in target_sinks:locations[current_node]=tuple(int(attrs.get(k,'0')) for k in ['xlow','ylow','layer','ptc'])
  if tag=='edge' and parent=='rr_edges':
   if count in needed:edges[count]=tuple(int(attrs[k]) for k in ['src_node','sink_node','switch_id'])
   count+=1
  stack.append(tag)
 def end(tag):
  nonlocal current_node
  if tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':current_node=None
  assert stack.pop()==tag
 parser=expat.ParserCreate(namespace_separator='\x1f');parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:parser.ParseFile(f)
 assert count==8097539 and set(edges)==needed and set(locations)==target_sinks;actual={};route=O/'canonical/design.route'
 for name,paths in physical_paths(route).items():
  for path in paths:
   key=(name,path[0][0],path[-1][0]);assert key not in actual;actual[key]=path
 expected=set();matched=0
 for q in frame['records']:
  cid=q['connection_id'];ids=patch[cid]['physical_edge_ids'] if cid in patch else q['answer']['physical_edge_ids'];path=[(q['source'],None)];u=q['source']
  for eid in ids:
   a,b,s=edges[eid];assert a==u;path.append((b,s));u=b
  assert u==q['sink'];key=(meta['net_names'][str(q['net_id'])],q['source'],q['sink']);assert key not in expected;expected.add(key);assert actual[key]==tuple(path);matched+=1
 assert set(actual)==expected and matched==115572
 old_identity=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/canonical/mmc/identity.jsonl';new_identity=O/'canonical/identity.jsonl';old={r['name']:r for r in map(json.loads,old_identity.read_text().splitlines())};new={r['name']:r for r in map(json.loads,new_identity.read_text().splitlines())};assert old.keys()==new.keys();inverse={name:int(n) for n,name in meta['net_names'].items()};changes=[]
 def groups(r):
  out=defaultdict(list)
  for pin in r['pins']:
   if pin['index']>0:out[tuple(pin[k] for k in ['x','y','layer','class'])].append(pin)
  return out
 for name,r in old.items():
  n=new[name];assert r['ignored']==n['ignored']
  if r['ignored']:continue
  a,b=groups(r),groups(n);assert a.keys()==b.keys()
  for key,ps in a.items():
   qs=b[key]
   if sorted(p['physical_pin'] for p in ps)!=sorted(p['physical_pin'] for p in qs):
    assert len(ps)==len(qs)==1;model_net=inverse[name];cids=[cid for cid,p in patch.items() if p['net_id']==model_net and locations[p['sink']]==key];assert len(cids)==1;changes.append(dict(connection_id=cids[0],model_NET_id=model_net,native_NET_before=r['net_id'],native_NET_after=n['net_id'],site_class=key,old_physical_pin=ps[0]['physical_pin'],new_physical_pin=qs[0]['physical_pin'],old_native_sink_index=ps[0]['index'],new_native_sink_index=qs[0]['index']))
 assert sorted(x['connection_id'] for x in changes)==[8728,41692];raw=R/'experiments/mmc_joint_patch_native_analysis_v2_2026-10-19/receipt.json';rawdata=json.loads(raw.read_text());arms={x['arm']:x for x in rawdata['rows']};assert arms['control']['wirelength']==661370 and arms['candidate']['wirelength']==c['wirelength']==j['new_full_unique_NET_CHAN_span']==661326;assert c['CPD_ns']<=arms['control']['CPD_ns']+1e-12
 bindings={str(p):sha(p) for p in [receipt,jp,patchp,source,ep,graph,route,old_identity,new_identity,raw,pathlib.Path(__file__).resolve()]}
 with (O/'independent_trace_and_pin_state_verification_v1.json').open('x') as f:json.dump(dict(status='ALL115572_NATIVE_PATHS_EXACT_SELECTED_MODEL_AND_TWO_EXPECTED_PIN_REBINDINGS',matched_connections=matched,NETs=55300,selected_patch_CIDs=sorted(patch),nonignored_equivalent_class_pin_changes=changes,old_native_wirelength=661370,new_native_wirelength=661326,old_native_CPD_ns=arms['control']['CPD_ns'],new_native_CPD_ns=c['CPD_ns'],canonical_ignored_pin_mismatches=c['mismatches'],canonical_ignored_trace_fixups=c['fixups'],original_zero_counter_gate_pass=c['original_zero_counter_gate_pass'],bindings=bindings,scope='Old-source placement, exact selected model paths and actual native post-route pin state. Canonical semantic pass does not erase first-import pin changes or original330 ignored-pin zero-counter failure. No new target placement, unseen-family, original predictor-quality or end-to-end gain.'),f,indent=2)
 print('ALL115572 TRACE MATCH; PIN REBINDINGS',changes,flush=True)
if __name__=='__main__':main()
