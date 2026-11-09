"""Matched source-frame to two-score-file pipeline costs; no native flow claim."""
import gc,hashlib,json,sys,time,xml.etree.ElementTree as ET
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from joint_full_score_state_v1 import Joint
from net_group_collision_risk_v1 import unit_group_expectation

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/full_score_pipeline_benchmark_v1_2026-10-18');out.mkdir(exist_ok=False)
 prep=time.perf_counter();root=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18');gp=root/'groups.json';proofpath=Path('experiments/real_joint_full_score_v2_2026-10-18/verification.json');proof=json.loads(proofpath.read_text());assert proof['status']=='pass'
 for p,h in proof['bindings'].items():assert sha(p)==h
 ip=proofpath.parent/'graph_index.json';index=json.loads(ip.read_text());assert index['byteorder']==sys.byteorder
 for item in index['arrays'].values():assert sha(item['path'])==item['sha256']
 config=json.loads((root/'protocol.json').read_text());manifest=json.loads((root/'vector_manifest.json').read_text())
 g=json.loads(gp.read_text());ids=g['positive_RR_ids'];groups={i:v['members'] for i,v in enumerate(g['groups'])};group_of={n:gid for gid,ns in groups.items() for n in ns};sinkgroups={v['sink_RR']:i for i,v in enumerate(g['groups']) if v['kind']=='direct_sink_IPIN'};sources={int(n) for n,r in g['fallback_reasons'].items() if r=='fixed_or_unsupported_type_SOURCE'}
 bindings={**proof['bindings'],str(proofpath.resolve()):sha(proofpath),str(Path(__file__).resolve()):sha(__file__),str(Path('tools/prepare_mmc_typed_collision_risk_v1_2026_10_18.py').resolve()):sha('tools/prepare_mmc_typed_collision_risk_v1_2026_10_18.py')}
 authentication_setup_seconds=time.perf_counter()-prep
 protocol=dict(bindings=bindings,cases=['case_01','case_02','case_03'],repeats=4,source='native_retained_off',target='native_retained_on',order='alternate incremental-first/full-rebuild-first',baseline='Direct source producer logic: union nodes per NET, node ledger and group k histogram, exact expectations, two full vectors. No constructor of redundant cache indices.',included='Read and hash complete target frame; JSON decode; XML-index path/endpoint checks and node projection; full diff for incremental arm; scoring; two full f64 files write+close+hash; target parsed/projected inputs and old-view reference release.',excluded='Producing target paths, native routing, fixed graph setup, initial old-state build, explicit gc.collect and OS fsync durability',setup='Measure one original XML parse and authenticated warm index load separately; filesystem cache is uncontrolled. Metadata/index remain shared by both arms.',cache='One resident old cache common to arms; reverse reset outside timing after each incremental arm, no saved predecessor view across arms.',scope='Offline score-file pipeline only, exposed cohort, shared host without CPU isolation. Not total RouteCast or native routing speedup.')
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 graph=Path(json.loads(Path(config['inputs']['case_01']['endpoint']).read_text())['inputs']['graph']['path'])
 t=time.perf_counter();xs=array('I');xd=array('I');xc=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2] if len(stack)>1 else None
  if e.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   if int(e.get('capacity'))>0:xc.append(int(e.get('capacity')))
   parent.remove(e);e.clear()
  elif e.tag=='edge' and parent is not None and parent.tag=='rr_edges':xs.append(int(e.get('src_node')));xd.append(int(e.get('sink_node')));parent.remove(e);e.clear()
  stack.pop()
 original_XML_parse_seconds=time.perf_counter()-t
 for key,data in [('edge_source',xs),('edge_destination',xd),('positive_capacity',xc)]:assert hashlib.sha256(data.tobytes()).hexdigest()==index['arrays'][key]['sha256']
 del xs,xd,xc,stack;gc.collect()
 t=time.perf_counter();arrays={}
 for key,item in index['arrays'].items():
  data=array(item['typecode']);data.frombytes(Path(item['path']).read_bytes());assert data.itemsize==item['itemsize'] and len(data)==item['values'];arrays[key]=data
 warm_index_load_seconds=time.perf_counter()-t;starts=arrays['edge_source'];dest=arrays['edge_destination'];caps=dict(zip(ids,arrays['positive_capacity']))
 print('SETUP COMPLETE',original_XML_parse_seconds,warm_index_load_seconds,flush=True)
 def project(frame,endpoint):
  assert frame['graph_sha256']==g['graph_sha256'];rows=[];drivers={}
  for r in frame['records']:
   node=r['source'];nodes={node}
   for edge in r['answer']['physical_edge_ids']:
    assert type(edge) is int and 0<=edge<len(dest) and starts[edge]==node
    node=dest[edge];nodes.add(node)
   assert node==r['sink'] and nodes<=caps.keys()
   net=r['net_id'];assert net not in drivers or drivers[net]==r['source'];drivers[net]=r['source']
   rows.append({**{k:r[k] for k in ['connection_id','net_id','source','sink']},'nodes':sorted(nodes)})
  rows.sort(key=lambda r:r['connection_id']);assert len(rows)==115572 and len({r['connection_id'] for r in rows})==len(rows)
  assert [{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in rows]==endpoint
  return rows
 def rebuild(rows):
  nets=defaultdict(set)
  for r in rows:nets[r['net_id']].update(r['nodes'])
  ledger=Counter();hist=defaultdict(Counter)
  for owned in nets.values():
   ledger.update(owned);counts=Counter(group_of[n] for n in owned if n in group_of)
   for gid,k in counts.items():hist[gid][k]+=1
  expected={gid:unit_group_expectation(len(groups[gid]),h) for gid,h in hist.items()}
  vectors=[array('d'),array('d')]
  for n in ids:
   if n in group_of:
    e=expected.get(group_of[n]);values=(0.,0.) if e is None else (float(e['expected_occupancy']),float(e['expected_overflow']))
   else:
    value=max(0,ledger[n]-caps[n])/caps[n];values=(value,value)
   for k in range(2):vectors[k].append(values[k])
  return vectors
 records=[]
 for case in protocol['cases']:
  inputs=config['inputs'][case];endpoint=sorted(json.loads(Path(inputs['endpoint']).read_text())['connections'],key=lambda r:r['connection_id']);oldframe=json.loads(Path(inputs['predictions'][protocol['source']]).read_text());oldrows=project(oldframe,endpoint);del oldframe
  t=time.perf_counter();state=Joint(g['graph_sha256'],groups,sinkgroups,sources,caps,oldrows);initial=time.perf_counter()-t
  targetpath=Path(inputs['predictions'][protocol['target']]);expected_hashes=[manifest[case+'__'+protocol['target']+'__'+family]['sha256'] for family in ['typed_group_mean','typed_NET_collision']]
  for repeat in range(protocol['repeats']):
   for arm in (['incremental','rebuild'] if repeat%2==0 else ['rebuild','incremental']):
    gc.collect();start=time.perf_counter();stages={};t=time.perf_counter();raw=targetpath.read_bytes();assert hashlib.sha256(raw).hexdigest()==bindings[str(targetpath.resolve())];frame=json.loads(raw);stages['read_hash_decode']=time.perf_counter()-t
    t=time.perf_counter();rows=project(frame,endpoint);stages['projection_validation']=time.perf_counter()-t
    t=time.perf_counter()
    if arm=='incremental':
     delta=[dict(old=a,new=b) for a,b in zip(oldrows,rows) if a!=b];stages['difference_discovery']=time.perf_counter()-t
     previous=state.view();t=time.perf_counter();receipt=state.commit(state.prepare(g['graph_sha256'],previous.generation,delta));stages['score_update']=time.perf_counter()-t
     t=time.perf_counter();current=state.view();vectors=[array('d'),array('d')]
     for n in ids:
      value=current.score(n)
      for k in range(2):vectors[k].append(value[k])
     stages['full_vector_materialization']=time.perf_counter()-t
    else:
     stages['difference_discovery']=0.;t=time.perf_counter();vectors=rebuild(rows);stages['full_score_rebuild']=time.perf_counter()-t
    t=time.perf_counter();outputs=[]
    for k,values in enumerate(vectors):
     path=out/(case+'__'+str(repeat)+'__'+arm+'__'+str(k)+'.f64')
     with path.open('xb') as f:values.tofile(f)
     h=sha(path);assert h==expected_hashes[k];outputs.append(dict(path=str(path.resolve()),sha256=h,bytes=path.stat().st_size))
    stages['file_write_close_hash']=time.perf_counter()-t;t=time.perf_counter()
    if arm=='incremental':del previous,current,delta
    del raw,frame,rows,vectors,values
    stages['temporary_and_old_view_release']=time.perf_counter()-t;total=time.perf_counter()-start
    record=dict(case=case,repeat=repeat,arm=arm,total_seconds=total,stages=stages,outputs=outputs,initial_cache_setup_seconds_excluded=initial);records.append(record)
    with (out/'measurements.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
    print('PIPELINE ARM DONE',case,repeat,arm,total,flush=True)
    if arm=='incremental':
     # Return to source state without retaining any pre-measurement view.
     view=state.view();reverse=[dict(old=view.query(r['connection_id']),new=r) for r in oldrows if view.query(r['connection_id'])!=r]
     state.commit(state.prepare(g['graph_sha256'],view.generation,reverse));del view,reverse
  del state,oldrows
 import statistics
 summary=[dict(case=case,**{arm:statistics.median(r['total_seconds'] for r in records if r['case']==case and r['arm']==arm) for arm in ['incremental','rebuild']}) for case in protocol['cases']]
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,setup=dict(authentication_and_metadata_seconds=authentication_setup_seconds,original_XML_parse_seconds=original_XML_parse_seconds,warm_index_load_seconds=warm_index_load_seconds),records=records,median_pipeline_seconds=summary,scope=protocol['scope']),f,indent=2)
 print('PIPELINE BENCHMARK COMPLETE',json.dumps(summary),flush=True)
if __name__=='__main__':main()
