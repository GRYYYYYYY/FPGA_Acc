"""Independently bind static placement receipts to real tasks and ordered commits."""
import argparse,csv,json,struct
from collections import defaultdict
from pathlib import Path
from persistent_vpr_timing import sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recipe',type=Path);p.add_argument('run',type=Path);a=p.parse_args()
    recipe,run=a.recipe.resolve(),a.run.resolve();m=json.loads(recipe.read_text());mode,=m['modes'];step=next(s for s in m['steps'] if s['label']==mode+'_0')
    placement=int(step['routing_environment']['DIEROUTE_TASK_PLACEMENT_MODE']);assert placement in (0,1,2)
    tasks_path=Path(step['command'][1]+'.tasks');owners_path=Path(step['command'][2]+'.node_die')
    tasks={r[0]:r for r in struct.iter_unpack('<IIIIHHIII',tasks_path.read_bytes())};owners=[r[0] for r in struct.iter_unpack('<H',owners_path.read_bytes())]
    result_path=run/'route.json';result=json.loads(result_path.read_text());assert result['task_placement_mode']==placement and result['legal']
    manifest=run/'manifest.json';assert json.loads(manifest.read_text())['status']=='online_router_completed_equivalence_audit_required'
    trace_path=run/'route.task_migration.csv';transactions_path=run/'route.transactions.csv'
    with trace_path.open() as stream:
        reader=csv.DictReader(stream);assert reader.fieldnames==['window','task_id','epoch','queue_position','seed_count','source_die','execution_die','executed','logical_envelope_bytes'];rows=[{k:int(v) for k,v in r.items()} for r in reader]
    with transactions_path.open() as stream:transactions=list(csv.DictReader(stream))
    assert len(transactions)==result['speculative_proposals']-result['speculative_replays']
    queues=defaultdict(int);seen=set();moved=0;logical_bytes=0;transferred_bytes=0
    if placement:
        assert len(rows)==len(transactions)
        for r,t in zip(rows,transactions):
            assert (r['window'],r['task_id'],r['epoch'])==tuple(int(t[k]) for k in ['window','task_id','epoch'])
            key=(r['window'],r['task_id']);assert key not in seen;seen.add(key)
            task=tasks[r['task_id']];source=owners[task[2]];destination=owners[task[3]] if placement==2 else source
            assert r['source_die']==source and r['execution_die']==destination and r['executed']==1 and r['seed_count']>0
            queue=(r['window'],destination);assert r['queue_position']==queues[queue];queues[queue]+=1
            assert r['logical_envelope_bytes']==32+12*r['seed_count']
            logical_bytes+=r['logical_envelope_bytes']
            if source!=destination:moved+=1;transferred_bytes+=r['logical_envelope_bytes']
    else:assert not rows
    report=dict(status='static_task_placement_receipts_bound_to_tasks_and_ordered_transactions',placement_mode=placement,receipts=len(rows),transactions=len(transactions),moved_task_occurrences=moved,logical_all_envelope_bytes=logical_bytes,logical_moved_envelope_bytes=transferred_bytes,source_sha256={str(p):sha(p) for p in [recipe,manifest,tasks_path,owners_path,result_path,trace_path,transactions_path,Path(__file__).resolve()]},scope='Independent task identity,owner-derived execution location,per-window queue positions and ordered transaction binding. Seed counts and logical byte formula checked;seed contents not independently reconstructed. CPU observer placement only,not physical PE transfer or measured network bytes. Full resource/read-set replay,queue saturation/cancellation and adaptive policy remain required.',board_result=False,research_complete=False)
    (run/'placement_trace_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
