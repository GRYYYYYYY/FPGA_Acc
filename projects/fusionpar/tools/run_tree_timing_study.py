#!/usr/bin/env python3
"""Execute the preregistered two-weight study; preserve all QoR and cost outcomes."""
import argparse
import json
from pathlib import Path
from statistics import median
import sys

from audit_development import audit, require
from run_development import ROOT, execute, sha


def binding(path):
    return {'path': str(path.resolve()), 'sha256': sha(path)}


def summarize_suite(path, design, arm, weight, baseline):
    receipt = json.loads((path/'audit.json').read_text())
    independent = audit(path)
    (path/'publication_audit.json').write_text(json.dumps(independent, indent=2)+'\n')
    require(receipt['deterministic'] and receipt['route_tree_timing_weight_q'] == weight,
            'missing determinism or wrong configuration')
    reference_root = ROOT/'work'/(design + ('_frozen_tp_pr_v2/routing' if arm=='fixed' else '_sequential_retained_v1'))
    reference = json.loads((reference_root/'audit.json').read_text())
    modes = {}
    for mode in sorted({r['mode'] for r in receipt['records']}):
        records = [r for r in receipt['records'] if r['mode']==mode]
        samples = []
        for r in records:
            completed = mode != 'route_only' or r['summary']['commits'] == 1
            quality = {k: r['final_native_quality'][k] for k in ('wirelength', 'cpd_ns')} if completed else None
            phases = {}
            for p in Path(r['directory']).glob('validation_*/costs.json'):
                profile = json.loads(p.read_text())
                for e in profile['phases']:
                    phases[e['phase']] = phases.get(e['phase'], 0) + e['wall_ns']
            samples.append({'repeat': r['repeat'], 'completed': completed, 'quality': quality,
                'within_original_2pct_gate': completed and quality['wirelength'] <= baseline['wirelength']*1.02 and
                                             quality['cpd_ns'] <= baseline['cpd_ns']*1.02,
                'host_seconds': r['process']['wall_ns']/1e9, 'charged_seconds': r['charged_wall_ns']/1e9,
                'native_adapter_seconds': r['summary']['native_ns']/1e9,
                'routing_seconds': r['summary']['routing_ns']/1e9,
                'phase_seconds': {k:v/1e9 for k,v in phases.items()},
                'commits': r['summary']['commits'], 'aborts': r['summary']['aborts'],
                'kernel_searches': sum(e['kernel_searches'] for e in r['event_semantics']),
                'expanded': sum(e['expanded'] for e in r['event_semantics'])})
        old = next(r for r in reference['records'] if r['mode']==mode)
        unchanged = all(r['final_state_sha256']==old['final_state_sha256'] and
                        r['event_semantics']==old['event_semantics'] and r['timing_events']==old['timing_events']
                        for r in records)
        if weight==0:
            require(unchanged, 'weight-zero state/event/timing differs from archived reference')
        modes[mode] = {'samples': samples,
            'median_host_seconds': median(s['host_seconds'] for s in samples),
            'median_charged_seconds': median(s['charged_seconds'] for s in samples),
            'median_phase_seconds': {k: median(s['phase_seconds'].get(k,0) for s in samples)
                                     for k in sorted({k for s in samples for k in s['phase_seconds']})},
            'state_events_timing_equal_to_old_weight_zero': unchanged,
            'final_state_sha256': records[0]['final_state_sha256']}
    return {'design':design, 'arm':arm, 'weight_q8':weight, 'modes':modes,
            'independent_audit':independent, 'sources':[binding(path/'audit.json'),
               binding(path/'publication_audit.json'), binding(reference_root/'audit.json')]}


def run(out):
    require(not out.exists(), 'output already exists')
    out.mkdir(parents=True)
    protocol_path = ROOT/'experiments/tree_timing_cost_protocol_2026-10-13.json'
    protocol = json.loads(protocol_path.read_text())
    require(protocol['weights_q8']==[0,256] and protocol['designs']==['ex5p','alu4','misex3'], 'unexpected protocol')
    (out/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
    vtr = ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
    suites, references = [], {}
    for index, design in enumerate(protocol['designs']):
        directory = out/design; directory.mkdir()
        original = ROOT.parent/'tileplace/experiments/tileplace_new_cohort_2026-09-29'/design
        tp_root = ROOT/'work'/(design+'_frozen_tp_pr_v2')
        pipeline = json.loads((tp_root/'pipeline.json').read_text())
        for suffix in ('place','route'):
            p = (tp_root/'case/baseline'/f'{design}.{suffix}').resolve()
            require(sha(p)==pipeline['placer_artifacts'][str(p)], 'reproduced TP artifact changed')
        baseline = json.loads((original/'baseline/baseline.json').read_text())
        references[design] = {'original_quality':{k:baseline[k] for k in ('wirelength','cpd_ns')},
            'TP_native_quality':pipeline['placer_quality'],
            'archived_placer_wall_ns':pipeline['placer_process']['wall_ns'],
            'pipeline':binding(tp_root/'pipeline.json'), 'baseline':binding(original/'baseline/baseline.json')}
        for arm in ('fixed','controller'):
            spec = protocol['fixed_placement_arm' if arm=='fixed' else 'controller_arm']
            case = tp_root/'case' if arm=='fixed' else original
            modes = ['route_only'] if arm=='fixed' else spec['modes']
            for weight in ([0,256] if index%2==0 else [256,0]):
                path = directory/f'{arm}_w{weight}'
                command = [sys.executable, str(ROOT/'tools/run_development.py'), '--case-root', str(case),
                    '--design', design, '--vpr', str(vtr/'build_tileplace_vpr/vpr/vpr'),
                    '--timing-vpr', str(vtr/'build_tileplace_vpr_timing_optional/vpr/vpr'),
                    '--arch', str(vtr/'vtr_flow/arch/timing/k6_frac_N10_mem32K_40nm.xml'),
                    '--circuit', str(vtr/'vtr_flow/benchmarks/blif'/f'{design}.blif'),
                    '--priority-reference', str(ROOT/'work'/(design+'_sequential_retained_v1')/'bundle/manifest.json'),
                    '--output', str(path), '--attempts', str(spec['attempts']),
                    '--repeats', str(spec['repeats_per_weight']), '--tree-timing-weight-q', str(weight), '--modes', *modes]
                print(f'Start {design} {arm} weight={weight}', flush=True)
                process = execute(command, directory/f'{arm}_w{weight}_process')
                suites.append({'path':path, 'design':design, 'arm':arm, 'weight':weight,
                               'process':process, 'baseline':baseline})
                print(f'Complete {design} {arm} weight={weight}', flush=True)
    # Measurements finish before CPU-intensive independent publication audits.
    results = []
    for suite in suites:
        print(f"Audit {suite['design']} {suite['arm']} weight={suite['weight']}", flush=True)
        result = summarize_suite(suite['path'], suite['design'], suite['arm'], suite['weight'], suite['baseline'])
        result['suite_process'] = suite['process']
        results.append(result)
        (out/'partial_analysis.json').write_text(json.dumps(results,indent=2)+'\n')
    result = {'schema':'FUSIONPAR_TREE_TIMING_STUDY_V1', 'protocol':binding(protocol_path),
              'runner':binding(Path(__file__)), 'references':references, 'suites':results,
              'limits':protocol['limits'] + ['No new TP execution in this study',
                   'Fixed placement: five repeats; controller mechanism study: two repeats',
                   'Validation-body intervals exclude Python startup and cost-report write',
                   'Keep native quality checks and timing export in end-to-end cost']}
    (out/'study.json').write_text(json.dumps(result,indent=2)+'\n')
    print('All measurements and independent audits complete',flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    run(args.output.resolve())
