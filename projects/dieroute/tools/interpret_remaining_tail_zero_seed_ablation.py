"""Record terminal development-only seed-weight ablation conclusion."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/rr_remaining_tail_zero_seed_ablation_20261015'
def main():
 audit=json.loads((P/'independent_audit.json').read_text());comparison=json.loads((P/'comparison_audit.json').read_text())
 assert audit['status']=='three_zero_seed_ablation_runs_independently_reviewed' and len(audit['outcomes'])==3
 assert comparison['weight0_joint_passes']==1 and comparison['weight128_joint_passes']==2
 assert all(v['wirelength_delta']<0 for v in comparison['outcomes'])
 assert {v['case'] for v in audit['outcomes'] if v['joint_gate_pass']}=={'diffeq'}
 files=[P/'independent_audit.json',P/'comparison_audit.json',P/'protocol.json',P/'configuration_audit.json',Path(__file__).resolve()]
 result=dict(status='zero_seed_weight_three_development_runs_complete_one_of_three_joint_pass_no_adoption',outcomes=audit['outcomes'],joint_passes={'weight0':1,'weight128':2},parent_comparison=[dict(case=v['case'],wirelength_delta=v['wirelength_delta'],cpd_delta_ns=v['cpd_delta_ns']) for v in comparison['outcomes']],source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},interpretation='All three zero-weight routes native legal. Relative to completed weight128/costscale256 controls, wirelength decreases in all3, CPD improves only diffeq; ex5p and alu4 fail native baseline CPD. Zero seed timing initial cost does not remove the joint QoR failure. Do not select zero weight or open heldout based on these results.',scope='Predeclared fixed3developmentcases, one repeat, existing controls not fresh matched repetitions. No general causal tradeoff theorem, statistical confidence, physical SLL/board result or completed quality gate.',adopted=False,board_result=False,research_complete=False)
 with (P/'interpretation.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(result['status'])
if __name__=='__main__':main()
