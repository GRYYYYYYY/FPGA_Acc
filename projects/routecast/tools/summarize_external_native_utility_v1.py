"""Fixed all9-target utility gate, exact zero equivalence, no subset promotion."""
import argparse,json
from pathlib import Path
from pre_route_endpoints import sha
KEYS=('NET_operations','connection_operations','heap_pushes','heap_pops')
def component_gate(zero,on):
    nonreg={k:on['native_work'][k]<=zero['native_work'][k] for k in KEYS}
    strict={k:on['native_work'][k]<zero['native_work'][k] for k in KEYS}
    wire=on['wirelength']<=zero['wirelength'];cpd=on['diagnostic_cpd_ns']<=zero['diagnostic_cpd_ns']+1e-12
    return dict(work_nonregression=nonreg,work_strict_improvement=strict,wire_nonregression=wire,diagnostic_cpd_nonregression=cpd,pass_component_gate=all(nonreg.values()) and any(strict.values()) and wire and cpd)

def summarize(manifest,output):
    manifest=Path(manifest).resolve();m=json.loads(manifest.read_text());bindings={str(manifest):sha(manifest)}
    if len(m['cases'])!=27:raise ValueError('fixed27 native arms required')
    groups={}
    for job in m['cases']:
        arms=groups.setdefault(job['target_case'],{})
        if job['utility_arm'] in arms:raise ValueError('duplicate utility arm')
        arms[job['utility_arm']]=job
    if len(groups)!=9 or any(set(a)!=set(('disabled','zero','forecast')) for a in groups.values()):raise ValueError('fixed9 case roles')
    rows=[]
    for case,jobs in groups.items():
        row=dict(case=case,availability_pass=False,zero_equivalence_pass=False,pass_component_gate=False);arms={}
        try:
            for arm,job in jobs.items():
                p=Path(job['output'])/'verification.json';v=json.loads(p.read_text())
                if v['status']!='FULL_PHYSICAL_AND_CANONICAL_PASS' or not v.get('independent_trace_replay_pass'):raise ValueError(arm+' native/trace failed')
                if any(sha(q)!=h for q,h in v['bindings'].items()):raise ValueError(arm+' changed evidence')
                bindings.update(v['bindings']);bindings[str(p)]=sha(p)
                if arm!='disabled' and (v['preload_state']['all_nodes_checked']!=job['graph_nodes'] or not v['preload_state']['all_bits_match_fixed_one_pseudo_iteration']):raise ValueError('readback')
                arms[arm]=v
            row['availability_pass']=True
            for name in ('output.route','design.net.post_routing','owner_trace.tsv'):
                if sha(Path(jobs['disabled']['output'])/name)!=sha(Path(jobs['zero']['output'])/name):raise ValueError('zero/disabled bytes differ: '+name)
            for key in ('native_work','iterations','wirelength','diagnostic_cpd_ns'):
                if arms['disabled'][key]!=arms['zero'][key]:raise ValueError('zero/disabled counters differ: '+key)
            row['zero_equivalence_pass']=True;row.update(component_gate(arms['zero'],arms['forecast']))
            row['arms']={a:{k:v[k] for k in ('native_work','iterations','wirelength','diagnostic_cpd_ns','native_process_seconds')} for a,v in arms.items()}
        except Exception as e:row['error']=repr(e)
        rows.append(row)
    result=dict(status='FIXED9_NATIVE_UTILITY_REVIEW',bindings=bindings,rows=rows,all9_available=all(r['availability_pass'] for r in rows),all9_zero_equivalent=all(r['zero_equivalence_pass'] for r in rows),all9_component_gate_pass=all(r['availability_pass'] and r['zero_equivalence_pass'] and r['pass_component_gate'] for r in rows),candidate_promoted=False,complete_workflow_gain_proven=False,strict_unseen_admitted=False,scope='Fixed initial excess component utility. All4 independently replayed integer work counters and wire/diagnostic CPD gates required per case; no averaging away failures. Component clocks do not establish full workflow gain.')
    with Path(output).open('x') as f:json.dump(result,f,indent=2)
    return result['all9_component_gate_pass']
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('output');a=p.parse_args();print('ALL9_COMPONENT_GATE',summarize(a.manifest,a.output))
