"""Read-only bounded observation of the serial full-neuron factor1 pipeline.

Never submits, recovers or stops jobs. Missing/partial metadata is unknown;
process absence alone never establishes a successful or failed stage.
"""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
CASE=R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15'


def receipt(path):
    try:
        with Path(path).open('rb') as f:data=f.read(65537)
        if len(data)>65536:return dict(observed=False,status='above_read_bound')
        value=json.loads(data)
        if type(value) is not dict:return dict(observed=False,status='invalid_object')
        return dict(observed=True,value=value)
    except FileNotFoundError:return dict(observed=False,status='not_present')
    except (ValueError,UnicodeDecodeError):return dict(observed=False,status='partial_or_invalid')


def process(pid,startticks,expected_args=None):
    root=Path('/proc')/str(pid)
    try:
        fields=(root/'stat').read_text().rsplit(')',1)[1].split()
        identity=int(fields[19])==startticks
        argv=[s.decode(errors='replace') for s in (root/'cmdline').read_bytes().split(b'\0') if s]
        command=expected_args is None or argv==expected_args
        memory={k:int(v.split()[0]) for line in (root/'status').read_text().splitlines() if ':' in line for k,v in [line.split(':',1)] if k in ('VmRSS','VmSize','VmHWM')}
        again=(root/'stat').read_text().rsplit(')',1)[1].split()
        identity=identity and int(again[19])==startticks
        return dict(pid=pid,startticks=int(fields[19]),state=again[0],verified_identity=identity,command_matches=command,verified_live=identity and command and again[0] not in ('Z','X'),ppid=int(again[1]),cpu_ticks=int(again[11])+int(again[12]),memory_KiB=memory)
    except FileNotFoundError:return dict(pid=pid,verified_live=False,status='missing_not_terminal_evidence')
    except (ValueError,IndexError):return dict(pid=pid,verified_live=False,status='invalid_process_metadata')


def snapshot():
    stages={}
    for name in ('model','initial_audit','sketch_audit','event_audit'):
        row=dict(terminal=receipt(CASE/(name+'_terminal.json')))
        meta=receipt(CASE/(name+'_process.json'))
        if meta['observed']:
            try:
                m=meta['value'];start=int(m['start_stat'].rsplit(')',1)[1].split()[19]);row['process']=process(m['pid'],start,m['args'])
                row['recorded_address_space_limit_bytes']=m['address_space_limit_bytes']
            except (KeyError,ValueError,IndexError,TypeError):row['process_metadata_status']='invalid_unknown'
        else:row['process_metadata_status']=meta['status']
        stages[name]=row
    launch=receipt(CASE/'launch_observation_v1.json');supervisor=dict(verified_live=False,status='launch_metadata_unknown')
    if launch['observed']:
        try:
            m=launch['value'];supervisor=process(m['supervisor_pid'],m['supervisor_startticks'])
        except (KeyError,ValueError,IndexError,TypeError):supervisor=dict(verified_live=False,status='invalid_launch_metadata_unknown')
    tail=[];log=CASE/'model.log'
    try:
        with log.open('rb') as f:f.seek(max(0,log.stat().st_size-2048));tail=f.read(2048).decode(errors='replace').splitlines()[-8:]
    except FileNotFoundError:pass
    return dict(case=str(CASE),session_id=46207,supervisor=supervisor,stages=stages,present_files=[n for n in ('initial.json','floors.json','floor_engine_release.json','round0.json','round1.json','sketch.json','receipt.json') if (CASE/'model'/n).exists()],model_log_tail=tail,pipeline_terminal=receipt(CASE/'pipeline_terminal.json'),complete_reference_parity=receipt(CASE/'exact_reference_parity.json'),development_admission=receipt(CASE/'development_admission.json'),release_snapshot=receipt(CASE/'model/floor_engine_release.json'),shared_headroom_bytes=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text()),memory_events=Path('/sys/fs/cgroup/memory.events').read_text(),scope='Read-only process/limited receipt observation. File presence is not closure, parity or complete-goal evidence; no automatic recovery or submission.')


if __name__=='__main__':print(json.dumps(snapshot(),indent=2))
