"""Audit actual distinct-chain native route against parent and frozen baseline."""
from pathlib import Path
import array,csv,hashlib,json,sys
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[1]).resolve();ARM=sys.argv[2];N=D/'native_queue'/ARM;assert N.is_dir()
def main():
 refs={}
 def sha(p):
  p=Path(p);h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  refs[str(p)]=h.hexdigest();return refs[str(p)]
 def tree(p):
  with Path(p).open() as f:return sorted(tuple(int(row[k]) for k in ['net_id','source','parent','child']) for row in csv.DictReader(f))
 p=json.loads((N/'protocol.json').read_text());m=json.loads((N/'manifest.json').read_text());assert m['status']=='all_three_restore_probes_terminal_requires_independent_review'
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 arm=m['results'][0];folder=N/arm['name'];actual=folder/'route.route_trees.csv';assert sha(actual)==arm['tree_sha256'];assert tree(actual)==tree(p['candidate_tree'])
 qfile=folder/'native_validation/validation.json';q=json.loads(qfile.read_text());sha(qfile)
 assert sha(folder/'native.route')==q['inputs']['route_sha256']
 for name,key in [('vpr_analysis.stdout','stdout_sha256'),('vpr_analysis.stderr','stderr_sha256')]:assert sha(qfile.parent/name)==q[key]
 pre=json.loads((N/'independent_preflight.json').read_text());a=pre['candidate']
 original=json.loads((D/'protocol.json').read_text())['candidate_tree']
 before=set(tree(original));after=set(tree(actual));changed={v[0] for v in before^after}
 generation=json.loads((D/'manifest.json').read_text());generated=next(a for a in generation['arms'] if a['name']==ARM)
 root_protocol=json.loads((D/'protocol.json').read_text());config=next(a for a in root_protocol['arms'] if a['name']==ARM)
 with open(root_protocol['connections']) as f:target=next(int(t['net_id']) for t in csv.DictReader(f) if int(t['id'])==config['task'])
 allowed={target,*config['order']};assert changed<=allowed
 change={'source_sha256':{original:sha(original)}}
 for evidence in [pre,change]:
  for f,h in evidence['source_sha256'].items():assert sha(f)==h,f
 parentfile=Path(original).parent/'native_validation/validation.json';parent=json.loads(parentfile.read_text());sha(parentfile)
 dies=array.array('H');dies.frombytes(Path(p['node_die']).read_bytes())
 if sys.byteorder!='little':dies.byteswap()
 parent_crossings=sum(dies[v[2]]!=dies[v[3]] for v in before);sha(p['node_die'])
 checks={'native_legal':q['legal'],'capacity':a['overused_resources']==0,'wirelength':q['total_wirelength']<=q['baseline_wirelength'],'CPD':q['critical_path_delay_ns']<=q['baseline_cpd_ns'],'modeled_transitions':a['layer_transitions']<=pre['baseline']['layer_transitions']}
 for f in [N/'protocol.json',N/'manifest.json',N/'independent_preflight.json',D/'protocol.json',Path(__file__).resolve()]:sha(f)
 result={'arm':ARM,'changed_nets':sorted(changed),'target_changed':target in changed,'no_op':not changed,'permitted_nets':sorted(allowed),'changed_tree_records':len(before^after),'status':'local_exchange_native_joint_pass' if all(checks.values()) else 'local_exchange_native_joint_fail','checks':checks,'wirelength':q['total_wirelength'],'parent_wirelength':parent['total_wirelength'],'baseline_wirelength':q['baseline_wirelength'],'cpd_ns':q['critical_path_delay_ns'],'parent_cpd_ns':parent['critical_path_delay_ns'],'baseline_cpd_ns':q['baseline_cpd_ns'],'model_crossings':a['layer_transitions'],'parent_model_crossings':parent_crossings,'baseline_model_crossings':pre['baseline']['layer_transitions'],'validation_wall_ns':arm['wall_ns'],'source_sha256':refs,'scope':'One posterior criticalpath/blocker exchange; exact evaluated tree and allowed changednet set checked. Native legality,CPD,wirelength and modeledtransitions required jointly. Original cohorts retained; no generalization or FPGA acceleration claim.','research_complete':False,'adopted':False}
 with (N/'independent_native_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
