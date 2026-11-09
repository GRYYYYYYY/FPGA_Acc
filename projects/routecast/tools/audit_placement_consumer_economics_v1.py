"""Measured avoided-work accounting, without changing the frozen native gate."""
import json,re,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
S=E/'xtea_fresh_paired_workflow_v1_2026-10-20'
D=E/'placement_consumer_economic_admission_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
    D.mkdir(exist_ok=False)
    audit=load(S/'independent_verification_v1.json')
    for p,h in audit['bindings'].items():assert sha(p)==h
    arms={};bindings={str(p):sha(p) for p in [S/'results.json',S/'independent_verification_v1.json',Path(__file__)]}
    for arm in ['off','on']:
        native=load(S/arm/'native/result.json');terminal=load(S/arm/'terminal.json');stages=load(S/arm/'stages.json');calls=[]
        for row in native['rows']:
            logp=Path(row['route']).parent/'native.log';text=logp.read_text();iterations=int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1]);calls.append(dict(candidate_id=row['candidate_id'],iterations=iterations,native_seconds=row['native_seconds'],audit_and_canonical_seconds=row['audit_and_canonical_seconds']));bindings[str(logp)]=sha(logp)
        gate=next(s['seconds'] for s in stages if s['stage']=='selected_native_and_gate');arms[arm]=dict(total_seconds=terminal['total_driver_seconds'],native_gate_driver_seconds=gate,measured_non_native_prefix_seconds=terminal['total_driver_seconds']-gate,calls=calls,selected_candidate=native['selected_candidate'],accepted=native['accepted'])
    off,on=arms['off'],arms['on'];assert len(off['calls'])==len(on['calls'])==2
    prefix_extra=on['measured_non_native_prefix_seconds']-off['measured_non_native_prefix_seconds'];route_saving=off['calls'][-1]['native_seconds']-on['calls'][-1]['native_seconds'];bound=on['measured_non_native_prefix_seconds'];assert prefix_extra>off['native_gate_driver_seconds'] and bound>off['total_seconds']
    protocol=dict(status='CONSUMER_AND_COST_ADMISSION_RULES_FROZEN',
        rule='Before new accelerator timing,declare the information unavailable at decision time,the consumer action,and the actual baseline work it avoids. Keep proposal generation,acceptance/legality and quality accounting fixed within each comparison.',
        allowed_comparisons=dict(same_estimator='Same input epoch,proposal sequence,outputs and constraints;compare incremental/accelerated evaluator with matched evaluator implementation. This can establish estimator acceleration,not automatically SKETCHon/off gain.',
                                 routing_work='If claiming fewer native calls or iterations,record actual launch counts and fullwork clocks in both arms;do not charge an oracle allcandidate router to a baseline that actually routes only its selected proposal.',
                                 quality_tradeoff='If call counts unchanged and predictor seeks better placement,report QoR/cost tradeoff. A qualityscreen is not inherently a time-saving consumer.'),
        next_workload_selection='Use pre-route input size/architecture/endpoint counts and a declared budget to choose workloads;record family exposure. No native outcome mining or unmeasured avoided-call credits.',
        lifetime='Declare initial snapshot ownership,one-time graph/timing/prior construction,perproposal inputs/state updates and finalgate. Immutable input APIs require byte/epoch identity and isolated rollback,not metadata-only digest shortcuts.',
        scope='New experiment admission rules,not retroactive success criteria or relaxation of original full9/legality/gates.')
    (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    out=dict(status='CURRENT_XTEA_CONSUMER_HAS_ZERO_AVOIDED_NATIVE_CALLS_OR_ITERATIONS',arms=arms,
             native_calls_avoided=len(off['calls'])-len(on['calls']),native_iterations_avoided=sum(c['iterations'] for c in off['calls'])-sum(c['iterations'] for c in on['calls']),
             added_pre_native_seconds=prefix_extra,selected_native_seconds_difference=route_saving,
             zero_cost_on_native_gate_floor_seconds=bound,off_total_seconds=off['total_seconds'],
             diagnostic_equivalent_off_gate_calls=prefix_extra/off['native_gate_driver_seconds'],
             scope='Fixed measured prefix costs;even setting onnativegate cost to0 cannot beat observed offtotal. Equivalent gatecalls is an arithmetic scenario,not measured avoidedwork or a bound on future implementations. Singledevelopmentpair only.',
             original_full9_gate=False,bindings=bindings)
    with (D/'work_accounting_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(out['status']);print('prefix_extra',prefix_extra,'zero_gate_floor',bound,'route_difference',route_saving)
if __name__=='__main__':main()
