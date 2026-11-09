#!/usr/bin/env python3
"""Paired native-export cache study with byte equivalence and charged setup."""
import argparse
import json
from pathlib import Path
from statistics import median
import sys

from audit_development import audit, require
from run_development import ROOT, execute, sha

FILES = ('candidate.state','candidate.place','candidate.route','quality.txt',
         'timing.txt','connection_delays.txt','timing.output.csv')


def binding(path):
    return {'path':str(path.resolve()),'sha256':sha(path)}


def analyze(xml_root, cache_root, design):
    roots = {'xml':xml_root,'sqlite':cache_root}
    receipts = {k:json.loads((p/'audit.json').read_text()) for k,p in roots.items()}
    audits = {}
    for key, path in roots.items():
        audits[key] = audit(path)
        (path/'publication_audit.json').write_text(json.dumps(audits[key],indent=2)+'\n')
        require(receipts[key]['deterministic'] and receipts[key]['rr_export_backend']==key,
                'backend/determinism check failed')
    for name in ('design.txt','graph.nodes','graph.edges','graph.resources'):
        require(sha(xml_root/'bundle'/name)==sha(cache_root/'bundle'/name), 'cache changed C++ input')
    old = json.loads((ROOT/'work'/(design+'_sequential_retained_v1')/'audit.json').read_text())
    modes = {}
    export_checks = []
    for mode in ('sequential_shared_tree_reuse','interleaved_tree_reuse'):
        samples = []
        for repeat in range(5):
            pair = {key:next(r for r in receipt['records'] if r['mode']==mode and r['repeat']==repeat)
                    for key,receipt in receipts.items()}
            baseline = next(r for r in old['records'] if r['mode']==mode and r['repeat']==repeat)
            for field in ('final_state_sha256','event_semantics','timing_events'):
                require(pair['xml'][field]==pair['sqlite'][field]==baseline[field], 'cache changed state/event/timing semantics')
            directories = {key:Path(r['directory']) for key,r in pair.items()}
            names = {key:{p.name for p in path.glob('validation_*')} for key,path in directories.items()}
            require(names['xml']==names['sqlite'], 'different candidate/native validation counts')
            for name in sorted(names['xml']):
                digests = {}
                for file in FILES:
                    a,b=(directories[key]/name/file for key in ('xml','sqlite'))
                    require(sha(a)==sha(b), 'cache changed native export: '+str(b))
                    digests[file]=sha(a)
                export_checks.append({'mode':mode,'repeat':repeat,'validation':name,'equal_sha256':digests})
            row={'repeat':repeat}
            for key,r in pair.items():
                phases = {}
                for p in directories[key].glob('validation_*/costs.json'):
                    for e in json.loads(p.read_text())['phases']:
                        phases[e['phase']]=phases.get(e['phase'],0)+e['wall_ns']/1e9
                row[key]={'host_seconds':r['process']['wall_ns']/1e9,
                          'charged_seconds':r['charged_wall_ns']/1e9,'phase_seconds':phases,
                          'commits':r['summary']['commits'],'aborts':r['summary']['aborts']}
            samples.append(row)
        first=next(r for r in receipts['xml']['records'] if r['mode']==mode)
        modes[mode]={'quality':{k:first['final_native_quality'][k] for k in ('wirelength','cpd_ns')},
            'samples':samples,'medians':{key:{metric:median(r[key][metric] for r in samples)
                                           for metric in ('host_seconds','charged_seconds')} for key in roots}}
    cache=json.loads((cache_root/'bundle/manifest.json').read_text())['rr_export']
    preparation={key:json.loads((path/'prepare.process.json').read_text())['wall_ns']/1e9 for key,path in roots.items()}
    return {'design':design,'pass':True,'audits':audits,'modes':modes,
            'cache_metadata':cache['metadata'],'cache_bytes':(cache_root/'bundle/rr_export.sqlite').stat().st_size,
            'cache_construction_and_roundtrip_seconds':cache['preparation_ns']/1e9,
            'full_preparation_seconds':preparation,'byte_equivalent_validations':export_checks,
            'evidence':[binding(p/'audit.json') for p in roots.values()]+
                       [binding(p/'publication_audit.json') for p in roots.values()]}


def run(out):
    require(not out.exists(),'output already exists');out.mkdir(parents=True)
    protocol_path=ROOT/'experiments/rr_export_cache_protocol_2026-10-13.json'
    protocol=json.loads(protocol_path.read_text());protocol_sha=sha(protocol_path)
    require(protocol['designs']==['ex5p','alu4','misex3'] and protocol['repeats_per_mode_backend']==5,
            'unexpected protocol')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    vtr=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
    for index,design in enumerate(protocol['designs']):
        directory=out/design;directory.mkdir()
        case=ROOT.parent/'tileplace/experiments/tileplace_new_cohort_2026-09-29'/design
        for backend in (('xml','sqlite') if index%2==0 else ('sqlite','xml')):
            command=[sys.executable,str(ROOT/'tools/run_development.py'),'--case-root',str(case),
                '--design',design,'--vpr',str(vtr/'build_tileplace_vpr/vpr/vpr'),
                '--timing-vpr',str(vtr/'build_tileplace_vpr_timing_optional/vpr/vpr'),
                '--arch',str(vtr/'vtr_flow/arch/timing/k6_frac_N10_mem32K_40nm.xml'),
                '--circuit',str(vtr/'vtr_flow/benchmarks/blif'/f'{design}.blif'),
                '--output',str(directory/backend),'--rr-export-backend',backend,
                '--attempts',str(protocol['attempts']),'--repeats','5',
                '--tree-timing-weight-q',str(protocol['tree_timing_weight_q']),'--modes',*protocol['modes']]
            print(f'Start {design} {backend}',flush=True)
            execute(command,directory/(backend+'_process'))
            print(f'Complete {design} {backend}',flush=True)
    results={}
    # Keep independent audit CPU costs out of every measured host sample.
    for design in protocol['designs']:
        print('Audit and compare '+design,flush=True)
        results[design]=analyze(out/design/'xml',out/design/'sqlite',design)
        (out/'partial_analysis.json').write_text(json.dumps(results,indent=2)+'\n')
    require(sha(protocol_path)==protocol_sha,'protocol changed during study')
    result={'schema':'FUSIONPAR_RR_EXPORT_CACHE_STUDY_V1','designs':results,
            'protocol':binding(protocol_path),'runner':binding(Path(__file__)),
            'limits':protocol['limits']}
    (out/'study.json').write_text(json.dumps(result,indent=2)+'\n')
    print('All cache/export/native/state comparisons passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.output.resolve())
