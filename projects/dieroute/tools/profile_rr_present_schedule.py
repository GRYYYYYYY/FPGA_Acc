"""Check actual Q8 growth against an explicitly bounded local-VPR schedule reference."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', type=Path)
    parser.add_argument('comparison', type=Path)
    parser.add_argument('vpr_route_source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    variant, output = args.variant.resolve(), args.output.resolve()
    comparison = args.comparison.resolve()
    evidence = json.loads(comparison.read_text())
    opts = evidence['baseline_reported_options']
    assert [float(opts[k]) for k in ('first_iter_pres_fac', 'initial_pres_fac', 'pres_fac_mult', 'max_pres_fac')] == [0, .5, 1.3, 1000]
    route_source = args.vpr_route_source.resolve()
    route_text = route_source.read_text()
    assert 'if (itry == 1)' in route_text and 'pres_fac = router_opts.initial_pres_fac;' in route_text
    assert 'pres_fac *= router_opts.pres_fac_mult;' in route_text
    assert 'pres_fac = std::min(pres_fac, router_opts.max_pres_fac);' in route_text
    output.mkdir(exist_ok=False)
    library = variant / 'build/libdieroute_rr_backend.a'
    source = output / 'probe.cpp'
    source.write_text('#include "wide_costs.hpp"\n#include <iostream>\n'
                      'int main(){for(auto start:{0ULL,256ULL}){auto p=start;'
                      'for(int i=0;i<30;++i){std::cout<<start<<","<<i<<","<<p<<"\\n";'
                      'p=dieroute::grow_present(p,start?512:333);}}}\n')
    exe = output / 'probe'
    compiler = shutil.which('g++')
    assert compiler and library.exists()
    command = [compiler, '-std=c++17', '-I'+str(variant/'source/dieroute/include'),
               '-I'+str(variant/'source/persistroute/include'), str(source), str(library), '-o', str(exe)]
    with (output/'compile.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    raw = subprocess.check_output([str(exe)], text=True)
    (output/'actual_growth.csv').write_text('start_q,iteration,present_q\n'+raw)
    actual = {(int(s),int(i)):int(p) for s,i,p in csv.reader(raw.splitlines())}
    for start,mult in [(0,333),(256,512)]:
        p=start
        for i in range(30):
            assert actual[start,i]==p
            p=max(1,(p*mult+128)//256)
    rows=[]
    vpr=0.0
    for i in range(30):
        rows.append(dict(iteration=i, current_actual_q8=actual[256,i],
                         naive_zero_start_actual_q8=actual[0,i],
                         local_vpr_reference_real=vpr))
        vpr=.5 if i==0 else min(1000.,vpr*1.3)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    snapshots={}
    for label,path in [('vpr_route.cpp',route_source),
                       ('wide_costs.cpp',variant/'source/dieroute/src/wide_costs.cpp'),
                       ('controller.cpp',variant/'source/dieroute/src/wide_controller.cpp')]:
        target=output/label;shutil.copy2(path,target);snapshots[str(target)]=sha(target)
    report=dict(status='actual_q8_growth_and_local_source_first_iteration_transition_profiled',
                rows=rows, actual_zero_start_second_iteration_q=actual[0,1],
                intended_reference_second_iteration_q=128,
                next_control_requirements=['Separate first-iteration and subsequent initial present factors.',
                    'Explicit multiplier quantization and maximum factor policy.',
                    'Record factors in every epoch and independently replay resulting resource versions.',
                    'Keep scheduling,history,net order,branch retention and quality gates fixed.'],
                command=command, source_snapshots_sha256=snapshots,
                source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),comparison,source,library,exe]},
                scope='Actual compiled DieRoute grow_present function on fixed inputs. VPR column is a '
                      'real-number reference for the local source initial transition and growth only, '
                      'not a replay of floating-point VPR routing, hold/budget resets, or original binary '
                      'execution. Original VPR complete as-built source identity remains unverified. '
                      'No routing quality experiment, causal attribution or physical performance proof.',
                board_result=False,research_complete=False)
    (output/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],zero_start_second_q=actual[0,1],reference_second_q=128)))


if __name__=='__main__':
    main()
