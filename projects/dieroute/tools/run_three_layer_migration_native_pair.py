"""Frozen same-graph native static/adaptive migration controls with full stage timing."""
import hashlib,json,os,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'work/rr_migration_remaining_tail_integration_20261016';N=D/'native_pair'
sys.path.insert(0,str(N/'native_tools'))
from rr_transfer_seed_replay import replay as seed_replay
from rr_adaptive_policy_replay import replay as adaptive_replay
from audit_adaptive_task_events import audit as credit_replay

def save(state):
    temp=N/'manifest.tmp';temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(N/'manifest.json')

def main():
    p=json.loads((N/'protocol.json').read_text())
    for f,h in p['source_sha256'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h,f
    begin=time.monotonic_ns();state=dict(status='running',pid=os.getpid(),steps=[],runs=[],research_complete=False,adopted=False);save(state)
    def run(name,command):
        start=time.monotonic_ns();step=dict(label=name,command=command,status='running');state['steps'].append(step);save(state)
        with (N/(name+'.log')).open('x') as log:
            child=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT);step['pid']=child.pid;save(state);rc=child.wait()
        step.update(status='terminal',returncode=rc,wall_ns=time.monotonic_ns()-start);save(state);assert rc==0,(name,rc)
    try:
        previous={}
        for repeat in range(p['repeats']):
            for arm in ['static','adaptive']:
                name=arm+'_'+str(repeat);out=N/'runs'/name;recipe=N/'recipes'/arm/'pair.json';start=time.monotonic_ns()
                run(name,[sys.executable,str(N/'native_tools/run_persistent_timing_online.py'),str(recipe),p['timing_build'],str(out)])
                counters=json.loads((out/'route.json').read_text());assert counters['legal'] and counters['remaining_layer_tail'] and counters['task_placement_mode']==p['arms'][arm]['placement']
                clean=dict(counters);clean.pop('wall_ms');hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob('route.*') if f.name!='route.json'}
                if arm in previous:assert previous[arm]==(clean,hashes),(arm,repeat)
                previous[arm]=(clean,hashes)
                replaystart=time.monotonic_ns()
                if arm=='adaptive':proof=adaptive_replay(Path(p['input_prefix']),out/'route',0,4,3,cost_scale=256,topology_prefix=Path(p['topology_prefix']),workers=2)
                else:proof=seed_replay(Path(p['input_prefix']),out/'route',0,4,3,cost_scale=256)
                (out/'resource_seed_replay.json').write_text(json.dumps(proof,indent=2)+'\n')
                credits=credit_replay(Path(p['input_prefix']),Path(p['topology_prefix']),out/'route',1,16777216,p['arms'][arm]['placement'])
                (out/'credit_replay.json').write_text(json.dumps(credits,indent=2)+'\n')
                state['steps'].append(dict(label=name+'_independent_resource_seed_credit',status='terminal',returncode=0,wall_ns=time.monotonic_ns()-replaystart));save(state)
                for suffix,command in p['post_commands'].items():
                    command=[a.replace(p['post_template_directory'],str(out)) for a in command]
                    if suffix=='timing':command[2]=str(recipe)
                    run(name+'_'+suffix,command)
                q=json.loads((out/'native_validation/validation.json').read_text());assert q['legal']
                state['runs'].append(dict(arm=arm,repeat=repeat,wall_ns=time.monotonic_ns()-start,quality=q,counters=counters,directory=str(out)));save(state)
        state.update(status='ten_three_layer_native_migration_runs_terminal_requires_independent_review',wall_ns=time.monotonic_ns()-begin);save(state)
    except BaseException as e:
        state.update(status='failed_preserve_evidence',error=repr(e),traceback=traceback.format_exc(),wall_ns=time.monotonic_ns()-begin);save(state);raise

if __name__=='__main__':main()
