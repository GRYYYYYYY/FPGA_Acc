"""Count final net-deduplicated layer transitions; no physical SLL inference."""
import array,csv,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'work/width_first_four_crossing_review_20261018'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tree_count(p,dies):
 tree={}
 with p.open() as f:
  for row in csv.DictReader(f):
   n,s,u,v=map(lambda k:int(row[k]),['net_id','source','parent','child'])
   assert 0<=u<len(dies) and 0<=v<len(dies)
   key=(n,v);assert key not in tree,('duplicate tree child',p,key)
   tree[key]=(u,s)
 return sum(dies[v]!=dies[u] for (n,v),(u,s) in tree.items()),len(tree)
def main():
 refs={str(Path(__file__).resolve()):sha(Path(__file__).resolve())};rows=[]
 for ordinal in ['first','second','third','fourth']:
  evidence=R/f'work/width_coverage_{ordinal}_parent_evidence_20261018/audit.json';a=json.loads(evidence.read_text());label=a['label'];assert a['native_legal']
  base=R/'work/width_coverage_roundtrip_20261017'/label
  parent=R/'work/width_coverage_parents_20261018/parents'/label
  baseline_audit=base/'audit.json';b=json.loads(baseline_audit.read_text())
  paths=[base/'topology.node_die',base/'native_tree.csv',parent/'route.route_trees.csv']
  for p in paths:
   h=sha(p); known=a['source_sha256'].get(str(p),b['source_sha256'].get(str(p)))
   if known is not None:assert h==known,p
   refs[str(p)]=h
  dies=array.array('H');dies.frombytes(paths[0].read_bytes())
  if sys.byteorder!='little':dies.byteswap()
  assert len(dies)==b['nodes'] and set(dies)=={0,1,2}
  before,nb=tree_count(paths[1],dies);after,na=tree_count(paths[2],dies);assert nb==b['tree_edges']
  rows.append({'label':label,'baseline_layer_transitions':before,'candidate_layer_transitions':after,'crossing_nonincrease':after<=before,'WL_CPD_crossing_joint_observed':after<=before and a['wirelength_delta_percent']<=0 and a['cpd_delta_percent']<=0,'baseline_tree_edges':nb,'candidate_tree_edges':na})
  for p in [evidence,baseline_audit]:refs[str(p)]=sha(p)
 result={'status':'first_four_final_tree_layer_transitions_reconstructed','rows':rows,'source_sha256':refs,'scope':'Final directed parent-child layer transitions, each net-child counted once, using frozen single-die node membership; cumulative committed_crossings is not used. Not physical SLL usage, representative statistical robustness or board performance. Only four of12 posterior configurations reviewed.','research_complete':False}
 O.mkdir(exist_ok=False);(O/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
