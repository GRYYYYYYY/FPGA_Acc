#!/usr/bin/env python3
"""Bind a fresh native timing oracle to a serialized C++ repair and re-evaluate."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
from audit_dcp_reports import native_reports
from audit_native_load_slacks import read
from run_native_case import sha256
from run_native_timing_feedback import write_snapshot


def main():
    if not __debug__:raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('feedback-run','feedback-audit','writeback','native-run','dcp-audit','load-run','members','connectivity','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--case',choices=('hold20','setup1434'),required=True)
    a=p.parse_args();fr=a.feedback_run.resolve();wb=a.writeback.resolve();out=a.output.resolve()
    fm=json.loads((fr/'manifest.json').read_text());fa=json.loads((a.feedback_audit/'audit.json').read_text())
    wm=json.loads((wb/'manifest.json').read_text());member=json.loads(a.members.read_text())
    dcp_audit=json.loads(a.dcp_audit.read_text())
    assert fm['status']=='passed' and fm['inputs_unchanged'] and fa['passed'] and fa['inputs_unchanged']
    assert wm['status']=='passed' and wm['physical_reload_equal'] and wm['inputs_unchanged'] and wm['sdk_unchanged']
    assert wm['feedback_candidate']['run']==str(fr) and wm['feedback_candidate']['case']==a.case
    assert wm['feedback_candidate']['audit']==str(a.feedback_audit.resolve())
    assert wm['feedback_candidate']['trees_sha256']==fa['cases'][a.case]['candidate_trees_sha256']
    assert member['inputs_unchanged']
    controls=member['members']['control']['raw'];candidate=member['members']['routed']['raw']
    assert {k:v for k,v in controls.items() if not k.endswith('.edf')}=={k:v for k,v in candidate.items() if not k.endswith('.edf')}
    assert member['inputs'][str(wb/'write/routed.dcp')]==wm['artifacts']['write/routed.dcp']
    # Constraint/HWDEF/stub bytes must match the previously checked proposal.
    # EDIF serialization order may differ; separately require complete exported
    # leaf/terminal connectivity equality to the original readable netlist.
    old_dcp,=[path for path in member['inputs'] if path!=str(wb/'write/routed.dcp')]
    assert old_dcp in fm['inputs'] and fm['inputs'][old_dcp]==member['inputs'][old_dcp]
    connectivity=json.loads((a.connectivity/'provenance.json').read_text())
    assert connectivity['passed'] and connectivity['strict_exported_terminal_and_leaf_equality']
    assert connectivity['writeback_manifest_sha256']==sha256(wb/'manifest.json')
    assert connectivity['comparison_sha256']==sha256(a.connectivity/'audit.json')
    assert dcp_audit['status']=='native_checks_passed' and all(dcp_audit['checks'].values())
    assert dcp_audit['writeback_manifest_sha256']==sha256(wb/'manifest.json')
    assert dcp_audit['members_audit_sha256']==sha256(a.members)
    assert dcp_audit['logical_connectivity']==connectivity
    inputs=dict(fa['inputs'])
    def add(path,digest):
        path=str(Path(path).resolve());assert path not in inputs or inputs[path]==digest,path;inputs[path]=digest
    for directory in (fr,wb,a.native_run,a.load_run):add(directory/'manifest.json',sha256(directory/'manifest.json'))
    add(a.feedback_audit/'audit.json',sha256(a.feedback_audit/'audit.json'));add(a.members,sha256(a.members))
    add(a.dcp_audit,sha256(a.dcp_audit))
    for name in ('provenance.json','audit.json'):add(a.connectivity/name,sha256(a.connectivity/name))
    for path,digest in connectivity['parent_manifests'].items():add(path,digest)
    for records in (wm['inputs'],wm['sdk'],member['inputs']):
        for path,digest in records.items():add(path,digest)
    for name,digest in wm['artifacts'].items():add(wb/name,digest)
    report=native_reports(a.native_run.resolve());nm=json.loads((a.native_run/'manifest.json').read_text())
    assert dcp_audit['routed']==report
    assert nm['input']==str(wb/'write/routed.dcp') and nm['input_sha256']==wm['artifacts']['write/routed.dcp']
    assert report['fully_routed_without_errors'] and report['no_drc_errors_or_critical_warnings']
    assert report['timing']['tns_ns']==0 and report['timing']['ths_ns']==0
    assert report['timing']['wns_ns']>=0 and report['timing']['whs_ns']>=0
    for name,digest in nm['artifacts'].items():add(a.native_run/name,digest)
    for path,digest in nm.get('dependencies',{}).items():add(path,digest)
    lm,observations,aliases=read(a.load_run.resolve())
    assert lm['inputs'][str(wb/'write/routed.dcp')]==wm['artifacts']['write/routed.dcp']
    assert lm['artifacts']['check_native_load_slacks.tcl']==fm['context']['query_sha256']
    assert lm['artifacts']['load_pins.tsv']==fm['context']['load_set_sha256']
    for path,digest in lm['inputs'].items():add(path,digest)
    for name,digest in lm['artifacts'].items():add(a.load_run/name,digest)
    before=dict(line.split('=',1) for line in (wb/'write/before.txt').read_text().splitlines())
    after=dict(line.split('=',1) for line in (wb/'write/expected.txt').read_text().splitlines())
    assert before.keys()==after.keys() and all(before[k]==after[k] for k in before if k!='selected_routes')
    assert (wb/'write/expected.txt').read_bytes()==(wb/'reload/snapshot.txt').read_bytes()
    load_ids={(r['net'],r['pin']):r['load'] for r in json.loads((fr/'load_ids.json').read_text())}
    assert set(observations)=={(net,pin,kind) for net,pin in load_ids for kind in ('min','max')}
    out.mkdir(parents=True,exist_ok=False);(out/'route').mkdir();(out/'snapshots').mkdir();(out/'source').mkdir()
    for name in ('verify_native_feedback_repair.py','run_native_timing_feedback.py','audit_native_load_slacks.py','audit_dcp_reports.py','audit_native_timing.py','run_native_case.py'):
        shutil.copy2(Path(__file__).with_name(name),out/'source'/name)
    old_command=next(r['command'] for r in fm['steps'] if r['name']==a.case)
    for name in ('trees.csv','usage.csv'):shutil.copy2(fr/a.case/'candidate'/name,out/'route'/name)
    shutil.copy2(Path(old_command[6])/'selection.csv',out/'route/selection.csv')
    shutil.copy2(fr/'snapshots/baseline.timing',out/'snapshots/baseline.timing')
    context=(fr/'snapshots/baseline.timing').read_text().splitlines()[1].split()[1]
    write_snapshot(out/'snapshots/proposal.timing',fr/a.case/'candidate/tree_identity.txt',context,1,observations,load_ids)
    command=list(old_command);command[6:9]=[str(out/'route'),str(out/'snapshots'),str(out/'evaluated')]
    manifest=out/'manifest.json';record=dict(schema='dieroute.native_feedback_repair_verification.v1',status='running',
        inputs=inputs,started_ns=time.time_ns(),command=command,case=a.case,board_result=False,native_reports=report,
        logical_connectivity=connectivity,
        scope='Fresh native route/DRC and per-load setup/hold oracle for a C++ repair; strict leaf/terminal equality to original plus unchanged constraint/HWDEF/stub members')
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        for path,digest in inputs.items():assert sha256(path)==digest,path
        with (out/'feedback.log').open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);record['pid']=proc.pid;save();record['returncode']=proc.wait()
        assert record['returncode']==0,'fresh repair feedback failed'
        decision=json.loads((out/'evaluated/decision.json').read_text())
        assert decision['selected_scope_accepted'] and not decision['repair_requires_native_timing']
        assert decision['authority_epoch']==1 and not decision['restored_nets']
        for name in ('trees.csv','usage.csv'):
            assert (out/'evaluated/authority'/name).read_bytes()==(out/'route'/name).read_bytes()
        for path,digest in inputs.items():assert sha256(path)==digest,path
        summaries={}
        for kind in ('min','max'):
            from decimal import Decimal
            values=[v for (n,p,k),v in observations.items() if k==kind]
            finite=[Decimal(v['SLACK']) for v in values if v and v['_classification']=='constrained_path']
            summaries[kind]=dict(finite=len(finite),minimum_slack_ns=str(min(finite)),
                                reported_unconstrained=sum(v is not None and v['_classification']=='reported_unconstrained_path' for v in values),
                                missing=sum(v is None for v in values))
        record.update(status='selected_scope_accepted_after_fresh_native_checks',inputs_unchanged=True,
                      decision=decision,load_timing=summaries,hierarchy_alias_loads=aliases,
                      limitations=['No joint wirelength/CPD acceptance or global margin-floor claim.',
                                   'Full-design timing cost model, native corridor/shadow integration, bitstream acceptance and board performance remain open.'])
    except Exception as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns();record['artifacts']={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest};save()
    print(json.dumps({k:record[k] for k in ('status','load_timing','decision')}))


if __name__=='__main__':main()
