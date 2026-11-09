"""Prepare all12 fixed unseeded native commands; no route execution."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
import canonical_reload_pin_index_expat_v3 as canonical
R=Path(__file__).resolve().parents[1]
def main():
    bundle=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json'
    metric=R/'experiments/prospective_external_family_quality_domains_v2_2026-10-19/research_decision_v1.json'
    source=R/'experiments/prospective_external_family_development_place_v1_2026-10-19/design.blif'
    arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
    binary=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';bp=binary.parent/'receipt.json';b=json.loads(bp.read_text())
    if sha(binary)!=b['binary_sha256']:raise ValueError('binary changed')
    runner=R/'tools/run_external_native_route_case_v1.py'
    bindings={**closure([Path(__file__),runner]),**b['source_sha256'],**b['shared_inputs_sha256']}
    for p in [bundle,metric,source,arch,binary,bp,canonical.binary,canonical.identity]:bindings[str(p)]=sha(p)
    cases=[];out=R/'experiments/prospective_external_family_native_case_manifest_v1_2026-10-19';out.mkdir(exist_ok=False)
    for row in json.loads(bundle.read_text())['rows']:
        ep=Path(row['endpoint']);meta=json.loads(ep.read_text());bindings[str(ep)]=sha(ep)
        for entry in meta['inputs'].values():
            p,h=entry['path'],entry['sha256']
            if p in bindings and bindings[p]!=h:raise ValueError('binding conflict')
            bindings[p]=h
        cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',meta['inputs']['graph']['path'],'--route_chan_width',str(row['width']),'--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
        cases.append(dict(case=row['case'],width=row['width'],frame=row['frame'],role='source_conditioning' if row['frame']=='source' else 'target_cold_primary_label',endpoint=str(ep),graph_sha256=row['graph_sha256'],inputs=dict(blif=str(source),net=meta['inputs']['net']['path'],place=meta['inputs']['place']['path']),output=str(out/'runs'/row['case']),command=cmd))
    if not all(sha(p)==h for p,h in bindings.items()):raise ValueError('dependency changed')
    m=dict(schema='ROUTECAST_EXTERNAL_NATIVE_CASE_MANIFEST_V1',full_workflow_admitted=False,bindings=bindings,cases=cases,native_order=[r['case'] for r in cases],native_policy='Unseeded, width fixed96/128/160, seed1, workers1, maxiterations100, FULL. Sanitize all ROUTECAST_ environment. 32GiB child address-space limit, no time cancellation. No substitution on failure.',failure_policy='Retain all12 outcomes; unavailable source blocks associated warm predictions and fails full-cohort availability, never replace width/layout.',timing_scope='Runner case timer includes staging/native/physical/canonical including inventory, excludes final verification serialization. Not complete matched workflow timing.',remaining_before_execution=['Executable forecasting comparison evaluator and controls','Native utility/feedback on-off matched commands','Complete upstream/shared/per-case timing accounting and workflow admission'],scope='Executable native component draft only. Independent fixed nine-target labels and three source roles explicit; no routing launched, no strict-unseen or complete-flow gain.')
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('ALL12_NATIVE_COMMANDS_PREPARED',out/'manifest.json')
if __name__=='__main__':main()
