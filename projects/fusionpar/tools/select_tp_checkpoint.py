#!/usr/bin/env python3
"""Select the best native-legal visited TP snapshot under FP's final QoR rule.

This postprocesses all executed trials, including TP rejections. It does not
claim to replay TP with a different acceptance policy or a smaller search budget.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path

from audit_development import require
from run_development import ROOT, sha
from validate_candidate import native


def binding(path):
    return {'path':str(Path(path).resolve()),'sha256':sha(path)}


def select():
    protocol_path=ROOT/'experiments/tp_checkpoint_reference_protocol_2026-10-13.json'
    protocol=json.loads(protocol_path.read_text())
    inventory=json.loads((ROOT/'experiments/strong_baseline_inventory_2026-10-13.json').read_text())
    previous=json.loads((ROOT/'experiments/controller_baselines_status_2026-10-13.json').read_text())
    cache={}
    def checked(entry):
        path=Path(entry['path']).resolve()
        if path not in cache:cache[path]=sha(path)
        require(cache[path]==entry['sha256'],'changed TP artifact: '+str(path))
        return path
    designs={}
    for design in protocol['designs']:
        root=ROOT/'work'/(design+'_frozen_tp_pr_v2')
        pipeline_path=root/'pipeline.json'
        prior=next(e for e in previous['designs'][design]['evidence'] if Path(e['path'])==pipeline_path)
        checked(prior)
        pipeline=json.loads(pipeline_path.read_text())
        require(pipeline['placer_implementation']==inventory['tileplace_frozen_implementation'],'wrong frozen TP version')
        report_path=(root/'placer/report.json').resolve()
        checked({'path':str(report_path),'sha256':pipeline['placer_artifacts'][str(report_path)]})
        report=json.loads(report_path.read_text())
        require(report['status']=='pass' and report['closure_calls']==24 and len(report['trials'])==24,'incomplete TP trial population')
        for entry in report['provenance']['inputs']:checked(entry)
        original=ROOT.parent/'tileplace/experiments/tileplace_new_cohort_2026-09-29'/design/'baseline'
        baseline_path=original/'baseline.json';baseline=json.loads(baseline_path.read_text())
        checked(next(e for e in pipeline['pipeline_inputs'] if Path(e['path'])==baseline_path))
        staged=ROOT/'work'/(design+'_sequential_retained_v1')
        checked(next(e for e in previous['designs'][design]['evidence'] if Path(e['path'])==staged/'audit.json'))
        staged_audit=json.loads((staged/'audit.json').read_text())
        checked({'path':str(staged/'bundle/manifest.json'),'sha256':staged_audit['artifacts']['bundle/manifest.json']})
        staged_manifest=json.loads((staged/'bundle/manifest.json').read_text())
        for kind in ('net','place','route'):
            require(checked(staged_manifest['inputs'][kind])==(original/f'{design}.{kind}').resolve(), 'baseline input identity differs')
        cert_path=ROOT/'work'/(design+'_sequential_retained_v1')/'interleaved_tree_reuse_0/validation_0/validation.json'
        checked({'path':str(cert_path),'sha256':staged_audit['artifacts'][str(cert_path.relative_to(staged))]})
        cert=json.loads(cert_path.read_text())
        require(cert['legal'] and all(cert[k]==baseline[k] for k in ('wirelength','cpd_ns')),'initial baseline certificate differs')
        checked({'path':str(cert_path.parent/'native.json'),'sha256':cert['native_report_sha256']})
        require('Placement_ID: SHA256:'+sha(original/f'{design}.place') in
                (original/f'{design}.route').read_text().splitlines()[0], 'baseline route/place identity mismatch')
        rows=[{'trial':0,'tp_accepted':None,'legal':True,'wirelength':baseline['wirelength'],
               'cpd_ns':baseline['cpd_ns'],'eligible':True,
               'artifacts':{kind:binding(original/f'{design}.{kind}') for kind in ('net','place','route')},
               'certificate':binding(cert_path)}]
        seen=set()
        for trial in report['trials']:
            number=trial['trial'];require(number not in seen and 1<=number<=24,'duplicate/out-of-range TP trial')
            seen.add(number)
            record=trial['closure'];path=checked({'path':record['report_path'],'sha256':record['report_sha256']})
            require(pipeline['placer_artifacts'][str(path)]==sha(path),'closure missing from reproduced archive')
            closure=json.loads(path.read_text())
            checked(trial['candidate_place'])
            for entry in closure['inputs'].values():
                if entry is not None:checked(entry)
            for entry in closure['outputs'].values():
                if entry is not None:checked(entry)
            for key in ('legal','wirelength','cpd_ns','returncode'):
                require(record[key]==closure[key],'trial summary disagrees with native closure')
            legal=closure['legal']
            row={'trial':number,'tp_accepted':trial['accepted'],'legal':legal,
                 'wirelength':closure['wirelength'],'cpd_ns':closure['cpd_ns'],
                 'closure':binding(path),'eligible':False}
            if legal:
                require(closure['returncode']==0 and closure['placement_validation']['legal'],'bad legal status')
                markers,wl,cpd=native.parse_vpr_output(checked(closure['outputs']['stdout']).read_text())
                require(all(markers[k] for k in ('routing_consistency','successfully_routed','vpr_succeeded')),
                        'native log lacks required legality markers')
                require(wl==row['wirelength'] and Decimal(str(cpd))==Decimal(str(row['cpd_ns'])),
                        'native log quality differs from recorded quality')
                artifacts={kind:closure['outputs'][key] for kind,key in
                    (('net','vpr_netlist_copy'),('place','vpr_place_copy'),('route','route'))}
                require(artifacts['net']['sha256']==rows[0]['artifacts']['net']['sha256'],'trial changed packed netlist')
                header=checked(artifacts['route']).read_text().splitlines()[0]
                require('Placement_ID: SHA256:'+artifacts['place']['sha256'] in header,'route/place identity mismatch')
                row['artifacts']=artifacts
                row['eligible']=wl*100<=baseline['wirelength']*102 and Decimal(str(cpd))<=Decimal(str(baseline['cpd_ns']))*Decimal('1.02')
            rows.append(row)
        require(seen==set(range(1,25)),'missing TP trial')
        selected=min((r for r in rows if r['eligible']),key=lambda r:(r['wirelength'],Decimal(str(r['cpd_ns'])),r['trial']))
        designs[design]={'original_quality':{k:baseline[k] for k in ('wirelength','cpd_ns')},
            'TP_reported_final_quality':pipeline['placer_quality'],'selected':selected,
            'population':rows,'native_closure_calls':24,'legal_trials':sum(r['legal'] for r in rows if r['trial']),
            'eligible_trials':sum(r['eligible'] for r in rows if r['trial']),
            'full_recorded_TP_wall_seconds':pipeline['placer_process']['wall_ns']/1e9,
            'evidence':[binding(pipeline_path),binding(report_path),binding(baseline_path)]}
    return {'schema':'FUSIONPAR_TP_COMMON_OBJECTIVE_CHECKPOINT_REFERENCE_V1',
            'protocol':binding(protocol_path),'selector':binding(Path(__file__)),'designs':designs,
            'limits':protocol['limits']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('output already exists')
    result=select();a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({d:{'selected_trial':x['selected']['trial'],'selected_WL':x['selected']['wirelength'],
                        'selected_CPD':x['selected']['cpd_ns'],'TP_accepted':x['selected']['tp_accepted'],
                        'eligible_trials':x['eligible_trials'],'full_TP_seconds':x['full_recorded_TP_wall_seconds']}
                     for d,x in result['designs'].items()},indent=2))
