"""Audit serial cross-circuit capacity-closure native probes, retaining failures."""
from pathlib import Path
import array,collections,csv,hashlib,json,mmap,struct,sys
from capacity_restore_closure import restore_closure
R=Path(__file__).resolve().parents[1];D=R/'work/capacity_closure_crosscase_20261020'
def trees(path):
 result=collections.defaultdict(dict);sources={}
 with Path(path).open() as f:
  for row in csv.DictReader(f):
   n,s,u,v=(int(row[k]) for k in ['net_id','source','parent','child'])
   assert v not in result[n];result[n][v]=u;assert sources.setdefault(n,s)==s
 return result,sources
def nodes(t,src):return {n:set(parent)|set(parent.values())|{src[n]} for n,parent in t.items()}
def main():
 refs={}
 def sha(p):
  p=Path(p)
  if str(p) not in refs:
   h=hashlib.sha256()
   with p.open('rb') as f:
    for b in iter(lambda:f.read(1048576),b''):h.update(b)
   refs[str(p)]=h.hexdigest()
  return refs[str(p)]
 protocol=json.loads((D/'protocol.json').read_text());batch=json.loads((D/'manifest.json').read_text());assert batch['status']=='all_three_native_probes_terminal_require_independent_review';results=[]
 for case in protocol['cases']:
  label=case['label'];folder=D/label;p=json.loads((folder/'protocol.json').read_text());state=json.loads((folder/'manifest.json').read_text());assert state['status']=='all_three_restore_probes_terminal_requires_independent_review'
  for f,h in p['source_sha256'].items():assert sha(f)==h,f
  base,bs=trees(p['baseline_tree']);parent,ps=trees(p['candidate_tree']);actual,src=trees(folder/'closure/route.route_trees.csv');assert bs==ps==src
  changed=[n for n in base if base[n]!=parent[n]];seed=min(changed,key=lambda n:(-len(set(base[n].items())^set(parent[n].items())),n));assert seed==p['selected_seed']
  bn=nodes(base,bs);pn=nodes(parent,ps);an=nodes(actual,src);res=R/'work/width_coverage_native_costs_20261018'/label/'input.resources';used=set().union(*bn.values(),*pn.values())
  with res.open('rb') as f:
   m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);cap={n:struct.unpack_from('<H',m,16*n+2)[0] for n in used};m.close()
  restored,waves=restore_closure(bn,pn,cap,{seed});assert sorted(restored)==p['arms'][0]['nets'] and waves==p['closure_waves']
  assert all(actual[n]==(base[n] if n in restored else parent[n]) for n in base)
  occupancy=collections.Counter(v for values in an.values() for v in values);over=sum(c>cap[v] for v,c in occupancy.items());assert over==0
  topo=R/'work/width_coverage_roundtrip_20261017'/label/'topology.node_die';dies=array.array('H');dies.frombytes(topo.read_bytes())
  if sys.byteorder!='little':dies.byteswap()
  def crossing(t):return sum(dies[v]!=dies[u] for net in t.values() for v,u in net.items())
  qfile=folder/'closure/native_validation/validation.json';q=json.loads(qfile.read_text());sha(qfile)
  for name,key in [('vpr_analysis.stdout','stdout_sha256'),('vpr_analysis.stderr','stderr_sha256')]:assert sha(qfile.parent/name)==q[key]
  assert sha(folder/'closure/native.route')==q['inputs']['route_sha256']
  checks={'native_legal':q['legal'],'capacity':over==0,'wirelength':q['total_wirelength']<=q['baseline_wirelength'],'CPD':q['critical_path_delay_ns']<=q['baseline_cpd_ns'],'modeled_layer_transitions':crossing(actual)<=crossing(base)}
  results.append({'label':label,'seed':seed,'restored_nets':len(restored),'retained_changed_nets':len(set(changed)-restored),'native_legal':q['legal'],'wirelength':q['total_wirelength'],'baseline_wirelength':q['baseline_wirelength'],'cpd_ns':q['critical_path_delay_ns'],'baseline_cpd_ns':q['baseline_cpd_ns'],'model_crossings':crossing(actual),'baseline_model_crossings':crossing(base),'checks':checks,'joint_pass':all(checks.values()),'probe_wall_ns':state['results'][0]['wall_ns']})
  for f in [folder/'protocol.json',folder/'manifest.json',folder/'closure/route.route_trees.csv',res,topo]:sha(f)
 for f in [D/'protocol.json',D/'manifest.json',Path(__file__).resolve(),R/'tools/capacity_restore_closure.py']:sha(f)
 result={'status':'three_circuit_capacity_closure_native_probes_reviewed','cases':results,'joint_passes':sum(c['joint_pass'] for c in results),'native_legal_count':sum(c['native_legal'] for c in results),'source_sha256':refs,'scope':'Three posterior fixed-seed stress probes of capacity-safe restoration. Quality failures retained. Does not establish targeted repair,generalization,minimal restoration,FPGA acceleration or replace original12case cohort. No adoption.','research_complete':False,'adopted':False}
 with (D/'independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
