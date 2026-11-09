"""Inventory measured CPU cost components without inventing absent total timing."""
import hashlib,json
from decimal import Decimal
from pathlib import Path


def main():
    base=Path('work/native_joint_budget_net_repair_v2_20261016')
    refresh=Path('work/native_refreshed_critical_policy_v1_20261016')
    protocol=base/'protocol.json';cases=json.loads(protocol.read_text())['cases'];inputs=[protocol]
    rows=[]
    for case in cases:
        name=case['label'];parent=Path('work/sb3_fixed_feedback_pair_20261015/native_runs')/(name+'_feedback_off_0')/'route.json'
        if not parent.exists():
            candidates=list(parent.parent.glob('*.json'))
            candidates=[p for p in candidates if 'wall_ms' in json.loads(p.read_text())]
            assert len(candidates)==1,candidates;parent=candidates[0]
        p=json.loads(parent.read_text());v2file=base/name/'manifest.json';newfile=refresh/name/'manifest.json'
        v2=json.loads(v2file.read_text());new=json.loads(newfile.read_text());inputs += [parent,v2file,newfile]
        assert all(s['wall_ns']>=0 for s in v2['steps']+new['steps'])
        parent_seconds=Decimal(p['wall_ms'])/1000
        sweep_seconds=Decimal(sum(s['wall_ns'] for s in v2['steps']))/10**9
        refresh_seconds=Decimal(sum(s['wall_ns'] for s in new['steps']))/10**9
        rows.append(dict(case=name,parent_cpp_routing_seconds=str(parent_seconds),v2_summed_net_attempt_seconds=str(sweep_seconds),refreshed_summed_net_attempt_seconds=str(refresh_seconds),
                         measured_component_sum_seconds=str(parent_seconds+sweep_seconds+refresh_seconds),
                         v2_net_attempts=len(v2['steps']),refreshed_net_attempts=len(new['steps']),
                         summed_postprocess_attempt_to_cpp_route_ratio=str((sweep_seconds+refresh_seconds)/parent_seconds),
                         missing_components=['parent initial/final native validation and process setup','v2 graph loading, wire parsing, initial native reanalysis, ordering and inter-attempt bookkeeping','refreshed graph loading, wire parsing, initial native reanalysis, packed binder loading and between-attempt binding','end-to-end launcher overhead and independent audit costs'],
                         total_wall_time_established=False))
    inputs.append(Path(__file__))
    output=dict(status='compound_CPU_cost_components_inventoried_total_wall_time_not_established',cases=rows,
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                scope='Sum of separately instrumented components is a lower bound, not measured end-to-end latency. Includes per-net search and native candidate validation where inside wall_ns. No CPU/FPGA speedup or hardware performance claim.',research_complete=False)
    D=Path('work/native_compound_cost_coverage_20261016');D.mkdir(exist_ok=False)
    (D/'audit.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
