"""Separate box, delay and foreign-occupancy effects on failed blocker493."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,struct
from sparse_delay_capped_search import search
R=Path(__file__).resolve().parents[1];D=R/'work/apex2_seed1_stage2_pooled_diagnostic_20261020'
def rows(f):
 with Path(f).open() as s:return list(csv.DictReader(s))
def main():
 p=json.loads((D/'protocol.json').read_text());m=json.loads((D/'manifest.json').read_text());arm=m['arms'][0];done={s['net']:{int(v):u for v,u in s['diagnostic_private_parent'].items()} for s in arm['steps'] if 'diagnostic_private_parent' in s};failed=arm['steps'][-1];net=failed['net'];taskid=failed['searches'][-1]['task'];tasks={int(t['id']):t for t in rows(p['connections'])};t=tasks[taskid];source=int(t['source']);sink=int(t['sink']);parents=collections.defaultdict(dict);sources={}
 for row in rows(p['candidate_tree']):n=int(row['net_id']);sources[n]=int(row['source']);parents[n][int(row['child'])]=int(row['parent'])
 oldnodes=set(parents[net])|set(parents[net].values())|{source};parents.update(done);owners=collections.defaultdict(set)
 for n,tree in parents.items():
  if n!=net:
   for v in set(tree)|set(tree.values())|{sources[n]}:owners[v].add(n)
 obs={int(v['task_id']):{k:int(x) for k,x in v.items()} for v in rows(p['native_parent_observations'])};delaycap=max(0,obs[taskid]['delay_ps']+p['baseline_cpd_ps']+obs[taskid]['slack_ps'])
 handles=[open(p[k],'rb') for k in ['nodes','edges','resources','boxes','node_die']];maps=[mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) for f in handles];nodes,edges,res,boxes,dies=maps
 def die(v):return struct.unpack_from('<H',dies,2*v)[0]
 a=struct.unpack_from('<4H',boxes,8*source);b=struct.unpack_from('<4H',boxes,8*sink);margin=p['box_margin'];window=(max(0,min(a[0],b[0])-margin),max(0,min(a[1],b[1])-margin),max(a[2],b[2])+margin,max(a[3],b[3])+margin)
 def adjacency(u):
  begin,count,_=struct.unpack_from('<IHH',nodes,8*u)
  for e in range(begin,begin+count):v,_,w=struct.unpack_from('<IHH',edges,8*e);yield v,w,int(die(u)!=die(v))
 results=[]
 for name,bounded,capped,respect in [('original',True,True,True),('remove_delay_cap',True,False,True),('remove_box',False,True,True),('ignore_foreign_occupancy',True,True,False)]:
  def allowed(v):
   x0,y0,x1,y1=struct.unpack_from('<4H',boxes,8*v);spatial=not bounded or v in oldnodes or v==source or (window[0]<=x0 and window[1]<=y0 and x1<=window[2] and y1<=window[3]);return spatial and (not respect or len(owners[v])<struct.unpack_from('<H',res,16*v+2)[0])
  answer=search(adjacency,allowed,source,sink,{},failed['crossing_cap'],p['maximum_expanded_per_sink'],delay_budget=delaycap if capped else None);r={'variant':name,**answer}
  if 'path_nodes' in answer:r['foreign_blocking_nets']=sorted({n for v in answer['path_nodes'] if len(owners[v])>=struct.unpack_from('<H',res,16*v+2)[0] for n in owners[v]})
  results.append(r)
 for x in maps:x.close()
 for f in handles:f.close()
 files=[D/'protocol.json',D/'manifest.json',Path(__file__).resolve(),R/'tools/sparse_delay_capped_search.py']
 a={'status':'blocker493_constraint_effects_diagnosed','task':taskid,'net':net,'delay_cap_ps':delaycap,'crossing_cap':failed['crossing_cap'],'variants':results,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'scope':'Privatefailedintermediate only;relaxedconstraintpathsnotvalidcandidates. No globalinfeasibility/nativequalityclaim.','research_complete':False}
 with (D/'constraint_diagnosis.json').open('x') as f:json.dump(a,f,indent=2);f.write('\n')
 print(json.dumps({'task':taskid,'delay_cap_ps':delaycap,'variants':[{k:v for k,v in r.items() if k!='path_nodes'} for r in results]}))
if __name__=='__main__':main()
