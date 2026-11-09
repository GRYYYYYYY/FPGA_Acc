"""Freeze original certified reference, then admit complete compiled parity.

This is an external final verifier, not a second pipeline or recovery owner.
It never starts/restarts the model or any audit stage.
"""
import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure

OLD=R/'experiments/titan23_neuron_compact_wide_retained_pipeline_v3_2026-10-13'
NEW=R/'experiments/titan23_neuron_compiled_criticality_pipeline_v1_2026-10-15'
OUT=R/'experiments/neuron_compiled_final_admission_v1_2026-10-15'
FRAMES=['initial.json','floors.json','round0.json','round1.json','sketch.json']
AUDITS=['initial_physical_verification.json','sketch_physical_verification.json','verification.json']
STAGES=['model','initial_audit','sketch_audit','event_audit']
PHYSICAL='all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'


def load(p):
    with p.open() as f:return json.load(f)


def write(p,data):
    with p.open('x') as f:json.dump(data,f,indent=2);f.write('\n')


def check(bindings):
    for p,h in bindings.items():assert sha(p)==h,('binding changed',p)


def freeze():
    # Stream hashes only, with no large model receipt parsing while solver lives.
    resource.setrlimit(resource.RLIMIT_AS,(2**30,2**30))
    reference_cert=R/'experiments/neuron_certified_native_metrics_v1_2026-10-15/label_admission.json'
    cert=load(reference_cert);assert cert['label_accepted']
    assert load(OLD/'pipeline_terminal.json')['all_stages_completed']
    bindings=closure([Path(__file__)])
    bindings[str(reference_cert)]=sha(reference_cert)
    files=[OLD/'model'/name for name in FRAMES+AUDITS+['receipt.json','protocol.json']]
    for p in files:
        assert str(p) in cert['bindings'],('reference not bound by existing certificate',p)
        assert sha(p)==cert['bindings'][str(p)],p
        bindings[str(p)]=cert['bindings'][str(p)]
    for p in [OLD/(s+'_terminal.json') for s in STAGES]+[OLD/'pipeline_terminal.json']:
        assert load(p)['exit_status']==0
        bindings[str(p)]=sha(p)
    for name in AUDITS:
        v=load(OLD/'model'/name);assert v[PHYSICAL] and v['completed']==77106
    protocol=load(NEW/'protocol.json')
    assert (protocol['original_nodes'],protocol['original_edges'],protocol['connections'],protocol['nets'],protocol['rounds'])==(3593250,39165143,77106,50767,2)
    bindings[str(NEW/'protocol.json')]=sha(NEW/'protocol.json')
    OUT.mkdir(exist_ok=False)
    write(OUT/'protocol.json',dict(bindings=bindings,prepared_utc=datetime.now(timezone.utc).isoformat(),
        original_reference_directory=str(OLD),candidate_directory=str(NEW),
        baseline_frames_and_receipt_locked_before_candidate_termination=not (NEW/'model_terminal.json').exists(),
        frame_equality='All five complete files byte-identical to independently certified original.',
        event_equality='All complete round metadata/event lists identical, excluding only seconds and state_file.',
        native_and_metric_protocol_changes_allowed=False,
        stage_limits_bytes=dict(model=20*2**30,initial_audit=8*2**30,sketch_audit=8*2**30,event_audit=8*2**30),
        metadata_correction='Pipeline process.json uses the model 20 GiB limit for audit metadata too. Actual bounded_child uses stage_limit; stage admission records are authoritative, and frozen pipeline source is checked. Original metadata retained.',
        performance_scope='Separate full model/audit process observations; no paired speedup or full workflow gain inferred.',
        scope='Original full neuron parity admission only. No goal completion, improved hotspot quality, heldout or hardware claim.'))
    print('FROZEN original certified five frames, receipt, audits and candidate protocol',flush=True)


def event_digest(receipt):
    rows=[]
    for row in receipt['rounds']:
        value={k:v for k,v in row.items() if k not in ['seconds','state_file']}
        blob=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
        rows.append(dict(round_index=row['round_index'],event_count=len(row['events']),
                         sha256=hashlib.sha256(blob).hexdigest()))
    return rows


def verify():
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));tick=time.perf_counter()
    protocol=load(OUT/'protocol.json');check(protocol['bindings'])
    pipeline=load(NEW/'pipeline_terminal.json')
    assert pipeline['exit_status']==0 and pipeline['all_stages_completed']
    bindings={**protocol['bindings'],str(OUT/'protocol.json'):sha(OUT/'protocol.json')}
    stages={}
    for name in STAGES:
        terminal=load(NEW/(name+'_terminal.json'));assert terminal['exit_status']==0
        admission=load(NEW/(name+'_admission.json'))
        assert admission['admitted'] and admission['child_limit_bytes']==protocol['stage_limits_bytes'][name]
        assert admission['shared_memory_max_bytes']-admission['shared_memory_current_bytes']>=admission['child_limit_bytes']+admission['margin_bytes']
        stages[name]=dict(terminal=terminal,admission=admission)
        for suffix in ['_terminal.json','_admission.json']:bindings[str(NEW/(name+suffix))]=sha(NEW/(name+suffix))
    for name in FRAMES:
        assert sha(NEW/'model'/name)==protocol['bindings'][str(OLD/'model'/name)],name
        bindings[str(NEW/'model'/name)]=sha(NEW/'model'/name)
    old_protocol=load(OLD/'model/protocol.json');new_protocol=load(NEW/'model/protocol.json')
    assert {k:v for k,v in old_protocol.items() if k!='bindings'}=={k:v for k,v in new_protocol.items() if k!='bindings'}
    for name in AUDITS:
        p=NEW/'model'/name;v=load(p);assert v[PHYSICAL] and v['completed']==77106
        check(v['bindings']);bindings[str(p)]=sha(p)
        for q,h in v['bindings'].items():
            assert q not in bindings or bindings[q]==h
            bindings[q]=h
    old=load(OLD/'model/receipt.json');old_rounds=event_digest(old);old_timers={k:v for k,v in old.items() if k.endswith('_seconds')}
    del old;gc.collect()
    actual=load(NEW/'model/receipt.json');check(actual['bindings']);check(actual['files'])
    new_rounds=event_digest(actual);assert old_rounds==new_rounds and len(new_rounds)==2
    new_timers={k:v for k,v in actual.items() if k.endswith('_seconds')}
    for p in [NEW/'model/receipt.json',NEW/'pipeline_terminal.json',NEW/'exact_reference_parity.json',NEW/'model/compiled_primary_work.json']:
        bindings[str(p)]=sha(p)
    check(bindings)
    result=dict(bindings=bindings,all_pass=True,all_original_connections=77106,
        all_complete_frames_byte_identical=True,all_events_and_round_metadata_identical=True,
        same_full_model_scientific_protocol=True,all_three_original_independent_audits_pass=True,
        complete_round_event_digests=new_rounds,stage_resource_and_terminal_evidence=stages,
        original_model_timers=old_timers,compiled_model_timers=new_timers,
        native_primitive_work=load(NEW/'model/compiled_primary_work.json'),
        observed_full_model_time_ratio=stages['model']['terminal']['seconds']/load(OLD/'model_terminal.json')['seconds'],
        paired_speedup_proven=False,end_to_end_gain_proven=False,
        quality_change_claim=False,heldout_family_certified=False,
        source_metadata_limit_inaccuracy_preserved_and_resolved_by_stage_admission=True,
        seconds=time.perf_counter()-tick,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope=protocol['scope'])
    write(OUT/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','stage_resource_and_terminal_evidence']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['freeze','verify']);args=parser.parse_args()
    globals()[args.stage]()
