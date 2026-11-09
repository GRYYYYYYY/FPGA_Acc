"""Create separately named model using explicit authenticated design inputs."""
import ast,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1]
source=R/'tools/run_criticality_retained_tree_full_schedule_v1.py'
target=R/'tools/run_design_scoped_retained_tree_v1.py'
s=source.read_text()
changes=[
("from load_structural_node_base_v1 import load as load_node_base\nfrom load_structural_node_base_v1 import PROOF as NODE_BASE_PROOF", "from load_design_routing_inputs_v1 import load as load_design_inputs"),
("from load_initial_connection_criticalities_v1 import load as load_criticalities\n", ""),
("def predict(endpoint,output,retain_context=False):", "def predict(endpoint,output,node_base_proof,criticality_directory,retain_context=False):"),
("node_base,base_bindings=load_node_base(len(f['capacities']),rc.scale)","node_base_proof=Path(node_base_proof).resolve();criticality_directory=Path(criticality_directory).resolve();node_base,criticalities,base_bindings=load_design_inputs(endpoint,node_base_proof,criticality_directory,len(f['capacities']),rc.scale)"),
(" criticality_directory=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10';criticalities=load_criticalities(criticality_directory);criticality_proof=criticality_directory/'verification.json';bindings.update(json.loads(criticality_proof.read_text())['bindings']);bindings[str(criticality_proof)]=sha(criticality_proof)"," criticality_proof=criticality_directory/'verification.json'"),
("structural_node_base_proof=str(NODE_BASE_PROOF)","structural_node_base_proof=str(node_base_proof)"),
("if __name__=='__main__':print(json.dumps(predict(*sys.argv[1:])),flush=True)","if __name__=='__main__':\n import argparse\n parser=argparse.ArgumentParser(description='Retained-tree model with explicit authenticated design inputs')\n for name in ['endpoint','output','node_base_proof','criticality_directory']:parser.add_argument(name)\n args=parser.parse_args()\n print(json.dumps(predict(args.endpoint,args.output,args.node_base_proof,args.criticality_directory)),flush=True)")]
for old,new in changes:
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
ast.parse(s)
# Verify entire numerical/transaction core is unchanged, including protocol text except proof path.
a=source.read_text().split(' for q in queries:\n',1)[1].split("if __name__=='__main__':",1)[0]
b=s.split(' for q in queries:\n',1)[1].split("if __name__=='__main__':",1)[0]
assert a.replace('str(NODE_BASE_PROOF)','str(node_base_proof)')==b
with target.open('x') as f:f.write(s)
bindings=closure([Path(__file__),source,target])
out=R/'experiments/retained_tree_cross_design_readiness_v1_2026-10-13/model_derivation_v1.json'
with out.open('x') as f:json.dump(dict(bindings=bindings,explicit_replacements=changes,full_numerical_and_transaction_core_text_equal=True,scope='Whitelisted input/CLI refactor plus exact core text equality. Not a second-design/full-model execution or hardware evidence.'),f,indent=2)
print('PASS seven explicit replacements and complete numerical/transaction core equality')
