"""All6 native/canonical pass and complete route/initial/canonical byte parity."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_native_shared_sink_native_v1_2026-10-19';B=R/'experiments/prospective_external_family_native_delay_bound_index_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 v=read(D/'verification.json');assert all(sha(k)==h for k,h in v['bindings'].items());bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for i in (1,2,3):
  for arm in ('cold','seed'):
   case=f'w160/episode_{i:02d}/{arm}';a,b=D/case/'native',B/case/'native';av,bv=read(a/'verification.json'),read(b/'verification.json');assert av['status']==bv['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert av['canonical']['semantic_consistency_gate_pass'] and bv['canonical']['semantic_consistency_gate_pass'];assert all(av[k]==bv[k] for k in ('iterations','wirelength','diagnostic_cpd_ns'));same={}
   for name in ('output.route','initial_connections.tsv','first_iteration.route','design.net.post_routing','report_timing.setup.rpt','report_timing.hold.rpt'):
    same[name]=sha(a/name)==sha(b/name);assert same[name];bindings[str(a/name)]=sha(a/name);bindings[str(b/name)]=sha(b/name)
   for name in ('design.route','design.net.post_routing','report_timing.setup.rpt','report_timing.hold.rpt'):
    aa,bb=a.parent/'native_canonical'/name,b.parent/'native_canonical'/name;same['canonical/'+name]=sha(aa)==sha(bb);assert same['canonical/'+name];bindings[str(aa)]=sha(aa);bindings[str(bb)]=sha(bb)
   bindings[str(a/'verification.json')]=sha(a/'verification.json');bindings[str(b/'verification.json')]=sha(b/'verification.json');rows.append(dict(case=case,all_full_native_and_canonical_pass=True,metrics_exact=True,byte_parity=same))
 assert all(sha(k)==h for k,h in bindings.items());(D/'parity_verification_v1.json').write_text(json.dumps(dict(status='ALL6_FULL_NATIVE_GROUP_OR_CANDIDATE_EXACT_OWN_INDEX_BASELINE_PARITY',rows=rows,bindings=bindings,scope='All3 current alias-free cohort only. Alias behavior proven separately by synthetic actual native contract. Physical shared-SINK routing integration not covered by these designs. No new QoR/fullworkflow timing acceptance.'),indent=2)+'\n');print('ALL6_FULL_NATIVE_GROUP_OR_CANDIDATE_EXACT_OWN_INDEX_BASELINE_PARITY')
if __name__=='__main__':main()
