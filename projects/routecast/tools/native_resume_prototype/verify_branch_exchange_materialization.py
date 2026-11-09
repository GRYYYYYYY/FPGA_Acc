"""Verify normalized native results and both quality references without discarding wire failures."""
import json,re,sys
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_branch_exchange_comparison_2026-10-07';out.mkdir(exist_ok=False);control=ROOT/'experiments/native_resume_singlepass_floor_controls_2026-10-07/verification.json';cv=json.loads(control.read_text());ordinary=ROOT/'experiments/native_resume_ungated_controls_2026-10-07/verification.json';ov=json.loads(ordinary.read_text());bindings={str(control):sha(control),str(ordinary):sha(ordinary)}
for v in (cv,ov):assert all(sha(f)==h for f,h in v['bindings'].items())
rows=[]
for w,i in ((16,1),(32,3)):
 base=ROOT/f'experiments/native_resume_branch_exchange_materialized_w{w}_m{i}_2026-10-07';rp=base/'receipt.json';r=json.loads(rp.read_text());p=json.loads((base/'protocol.json').read_text());assert r['protocol_sha256']==sha(base/'protocol.json')
 for mapping in (r['files'],p['inputs'],p['sources'],r['canonical']['files']):assert all(sha(f)==h for f,h in mapping.items());bindings.update(mapping)
 canon=r['canonical'];assert r['exit_code']==0 and canon['exit_code']==0 and canon['mismatches']==canon['fixups']==0 and F(str(canon['cpd_ns']))==F(r['cpd_ns']);assert r['all_endpoints_match'] and r['physical_audit']['overflow_units']==0
 log=(base/'canonical/reload.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;assert int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1])==r['wirelength']
 norm=lambda f:{n:Counter(ps) for n,ps in physical_paths(f).items() if ps}
 assert norm(base/'design.route')==norm(base/'canonical/design.route')
 original=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_workflow_2026-10-07/canonical/design.route';a,b=norm(original),norm(base/'canonical/design.route');selected=set(p['selected_net_names']);assert set(a)==set(b) and all(a[n]==b[n] for n in a if n not in selected)
 ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';meta=json.loads(ep.read_text());actual=Counter((n,path[0][0],path[-1][0]) for n,ps in b.items() for path,count in ps.items() for _ in range(count));expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in meta['connections']);assert actual==expected
 c=next(x for x in cv['rows'] if x['width']==w);o=next(x for x in ov['rows'] if x['width']==w);wire=r['wirelength'];cp=F(r['cpd_ns'])
 rows.append(dict(width=w,connections=len(meta['connections']),selected_net_names=p['selected_net_names'],initial_mismatches=r['mismatches'],initial_fixups=r['fixups'],final_mismatches=0,final_fixups=0,cpd_ns=r['cpd_ns'],wirelength=wire,original_candidate_cpd=c['cpd_pair'][0],original_candidate_wire=c['wire_pair'][0],candidate_cpd_improves=cp<F(c['cpd_pair'][0]),candidate_wire_change=wire-c['wire_pair'][0],joint_vs_matched_cold=cp<=F(c['cpd_pair'][1]) and wire<=c['wire_pair'][1],matched_cold_cpd=c['cpd_pair'][1],matched_cold_wire=c['wire_pair'][1],joint_vs_unfloored_cold=cp<=F(o['cpd_pair'][1]) and wire<=o['wire_pair'][1],unfloored_cold_cpd=o['cpd_pair'][1],unfloored_cold_wire=o['wire_pair'][1],materialization_analysis_proof_seconds=r['total_materialization_analysis_proof_seconds']))
 bindings[str(rp)]=sha(rp)
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,verifier_sha256=sha(Path(__file__)),scope='Full original-native normalized zero-fixup routing/STA and complete physical/endpoint proof. Initial synchronization fixups retained as provenance, not zero-fixup evidence. Both CPD gains and wire failures retained. Staged materialization cost excludes previous candidate and conditioned-search acquisition; no full-net-gain/heldout claim.'),indent=2)+'\n');print(rows)
