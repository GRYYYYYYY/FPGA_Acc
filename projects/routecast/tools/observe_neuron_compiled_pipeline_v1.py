"""Bounded read-only observation; never resumes, stops or starts any process.

Receipts are reported, not certified. Missing/transient process or partial JSON
does not establish completion; the original supervisor/session remains owner.
"""
import json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
CASE=R/'experiments/titan23_neuron_compiled_criticality_pipeline_v1_2026-10-15'


def receipt(path):
    try:
        with path.open() as f:
            value=json.load(f)
        return dict(observed=True,value=value)
    except FileNotFoundError:
        return dict(observed=False,status='not_present')
    except (OSError,ValueError) as error:
        return dict(observed=False,status='unreadable_or_incomplete',error=type(error).__name__)


def process(pid,expected_startticks=None,expected_args=None,expected_parent=None):
    try:
        fields=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
        start=int(fields[19])
        if expected_startticks is not None and start!=expected_startticks:
            return dict(pid=pid,verified_live=False,status='identity_mismatch',actual_startticks=start)
        if expected_parent is not None and int(fields[1])!=expected_parent:
            return dict(pid=pid,verified_live=False,status='parent_mismatch')
        if expected_args is not None:
            args=(Path('/proc')/str(pid)/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
            if args!=expected_args:
                return dict(pid=pid,verified_live=False,status='command_mismatch')
        if fields[0] in ['Z','X']:
            return dict(pid=pid,verified_live=False,state=fields[0],startticks=start,
                        status='exiting_or_zombie_not_a_terminal_receipt')
        return dict(pid=pid,verified_live=True,startticks=start,state=fields[0],
                    cpu_ticks=int(fields[11])+int(fields[12]))
    except FileNotFoundError:
        return dict(pid=pid,verified_live=False,status='not_present_not_a_terminal_receipt')
    except (OSError,ValueError,IndexError) as error:
        return dict(pid=pid,verified_live=False,status='unknown_transient_read',error=type(error).__name__)


def tail(path,limit=4096):
    try:
        with path.open('rb') as f:
            f.seek(0,2);f.seek(max(0,f.tell()-limit))
            return f.read().decode(errors='replace').splitlines()
    except FileNotFoundError:return []
    except OSError:return []


def snapshot():
    result=dict(case=str(CASE),original_session_id=23866,
                supervisor=process(1028439,1630248003),model=process(1075109,1630252740),
                stages={},closed_frame_candidates=[],model_log_tail=tail(CASE/'model.log')[-4:],
                scope='Read-only live/receipt observation, not hash, numerical, complete-goal or termination certification.')
    for name in ['model','initial_audit','sketch_audit','event_audit']:
        row=dict(terminal=receipt(CASE/(name+'_terminal.json')))
        observed=receipt(CASE/(name+'_process.json'))
        if observed['observed']:
            pid=observed['value']['pid']
            row['process']=process(pid,1630252740 if name=='model' else None,
                                   observed['value']['args'],1028439)
        result['stages'][name]=row
    for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json','receipt.json']:
        if (CASE/'model'/name).is_file():result['closed_frame_candidates'].append(name)
    for line in reversed(tail(CASE/'model_memory.jsonl')):
        try:result['last_model_memory']=json.loads(line);break
        except ValueError:continue
    result['pipeline_terminal']=receipt(CASE/'pipeline_terminal.json')
    result['raw_parity']=receipt(CASE/'exact_reference_parity.json')
    result['external_final_verification']=receipt(R/'experiments/neuron_compiled_final_admission_v1_2026-10-15/verification.json')
    for key in ['raw_parity','external_final_verification']:
        if result[key]['observed']:
            # Never print large binding inventories during routine monitoring.
            result[key]['value']={k:v for k,v in result[key]['value'].items()
                                  if k in ['all_pass','all_complete_frames_byte_equal','all_events_and_round_metadata_equal',
                                           'all_complete_frames_byte_identical','all_events_and_round_metadata_identical']}
    cgroup=Path('/sys/fs/cgroup')
    try:
        result['shared_headroom_bytes']=int((cgroup/'memory.max').read_text())-int((cgroup/'memory.current').read_text())
        result['memory_events']={k:int(v) for k,v in (line.split() for line in (cgroup/'memory.events').read_text().splitlines())}
    except (OSError,ValueError):result['shared_memory_status']='unavailable'
    return result


if __name__=='__main__':print(json.dumps(snapshot(),indent=2))
