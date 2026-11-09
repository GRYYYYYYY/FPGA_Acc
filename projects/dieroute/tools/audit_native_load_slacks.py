#!/usr/bin/env python3
"""Audit paired min/max timing paths, distinguishing finite and absent constraints."""
import argparse
from collections import Counter, defaultdict
import csv
import json
import re
from pathlib import Path
import shutil
from audit_native_timing import rows, number
from run_native_case import sha256


def checked_bindings(loads, bindings, segments):
    expected={(int(r['net_id']),r['to_pin']):r['net_name'] for r in loads}
    assert len(expected)==len(loads)
    members=defaultdict(set)
    for r in segments:
        key=(int(r['net_id']),r['to_pin'])
        assert key in expected and r['segment'] not in members[key]
        members[key].add(r['segment'])
    seen=set();aliases=0
    for r in bindings:
        key=(int(r['net_id']),r['to_pin']);assert key in expected and key not in seen
        seen.add(key);assert r['requested_net']==expected[key]
        assert r['requested_net'] in members[key] and r['direct_net'] in members[key]
        assert len(members[key])==int(r['segment_count'])
        aliases+=r['requested_net']!=r['direct_net']
    assert seen==set(expected)==set(members)
    return aliases


def checked_query(status, properties):
    key=(int(status['net_id']),status['to_pin'],status['kind'])
    assert key[2] in ('min','max')
    if status['status']=='no_reported_path':
        assert status['object_count']=='0' and not properties
        return None
    assert status['status']=='resolved' and status['object_count']=='1'
    assert properties['CLASS']=='timing_path' and properties['DELAY_TYPE']==key[2]
    assert properties['STARTPOINT_PIN'] and properties['ENDPOINT_PIN']
    assert properties['CORNER'] in ('Slow','Fast')
    for name in ('DATAPATH_DELAY','DATAPATH_LOGIC_DELAY','DATAPATH_NET_DELAY',
                 'STARTPOINT_CLOCK_DELAY','ENDPOINT_CLOCK_DELAY'):
        number(properties[name])
    result=dict(properties)
    if properties['SLACK']=='':
        assert properties['REQUIREMENT']==properties['REQUIRED_TIME']=='', 'inconsistent missing constraint properties'
        result['_classification']='reported_unconstrained_path'
    else:
        for name in ('SLACK','REQUIREMENT','REQUIRED_TIME'):number(properties[name])
        result['_classification']='constrained_path'
    return result


def read(directory):
    m=json.loads((directory/'manifest.json').read_text())
    assert m['status']=='reports_generated' and m['returncode']==0 and m['inputs_unchanged']
    for path,digest in m['inputs'].items():assert sha256(path)==digest,path
    for path,digest in m['artifacts'].items():assert sha256(directory/path)==digest,path
    loads=rows(directory/'load_pins.tsv');expected={(int(r['net_id']),r['to_pin']) for r in loads}
    assert len(expected)==len(loads)
    aliases=checked_bindings(loads,rows(directory/'reports/net_bindings.tsv'),rows(directory/'reports/net_segments.tsv'))
    completion=dict(line.split('=',1) for line in (directory/'reports/completed.txt').read_text().splitlines())
    assert completion['routes_changed']=='false' and completion['queries_failed']=='0' and int(completion['loads'])==len(loads)
    properties=defaultdict(dict)
    for r in rows(directory/'reports/paths.tsv'):
        key=(int(r['net_id']),r['to_pin'],r['kind']);assert r['property'] not in properties[key]
        properties[key][r['property']]=r['value']
    result={}
    for r in rows(directory/'reports/query_status.tsv'):
        key=(int(r['net_id']),r['to_pin'],r['kind']);assert key not in result
        result[key]=checked_query(r,properties.get(key,{}))
    assert set(result)=={(n,pin,kind) for n,pin in expected for kind in ('min','max')}
    assert set(properties)=={key for key,value in result.items() if value is not None}
    assert sum(value is None for value in result.values())==int(completion['no_reported_paths'])
    # Frozen Tcl uses a numeric input-row index for each individual path report.
    report_names=set()
    for index,r in enumerate(loads):
        for kind in ('min','max'):
            key=(int(r['net_id']),r['to_pin'],kind)
            if result[key] is not None:
                name=f'load_{index}_{kind}.rpt';report_names.add(name)
                report=(directory/'reports'/name).read_text()
                assert r['to_pin'] in report, 'requested through pin absent from detailed path'
                if result[key]['_classification']=='reported_unconstrained_path':
                    assert re.search(r'^Slack:\s+inf\s*$',report,re.M), 'missing unconstrained-path report witness'
    assert report_names=={f.name for f in (directory/'reports').glob('load_*.rpt')}
    return m,result,aliases


def main():
    if not __debug__:raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('original','routed','mapping-audit','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();old=read(a.original.resolve());new=read(a.routed.resolve())
    assert old[1].keys()==new[1].keys()
    for file in ('check_native_load_slacks.tcl','load_pins.tsv'):
        assert old[0]['artifacts'][file]==new[0]['artifacts'][file]
    mapping=json.loads((a.mapping_audit/'audit.json').read_text());assert mapping['passed']
    for path,digest in mapping['manifests'].items():assert sha256(path)==digest,path
    for file,digest in mapping['artifacts'].items():assert sha256(a.mapping_audit/file)==digest,file
    mapped=json.loads((a.mapping_audit/'mapping.json').read_text());by_pin=defaultdict(list)
    for r in mapped:by_pin[(r['net_id'],r['to_pin'])].append(r['task'])
    assert set(by_pin)=={key[:2] for key in old[1]}
    comparisons=[];summaries={}
    for key in sorted(old[1]):
        n,pin,kind=key;before,after=old[1][key],new[1][key]
        record=dict(net_id=n,to_pin=pin,kind=kind,tasks=sorted({t for t in by_pin[n,pin] if t is not None}),
                    original_status=before['_classification'] if before is not None else 'no_reported_path',
                    routed_status=after['_classification'] if after is not None else 'no_reported_path',original=before,routed=after)
        if before is not None and after is not None:
            record['same_start_end_corner']=all(before[k]==after[k] for k in ('STARTPOINT_PIN','ENDPOINT_PIN','CORNER'))
            if before['_classification']==after['_classification']=='constrained_path':
                record['slack_delta_ns']=str(number(after['SLACK'])-number(before['SLACK']))
        comparisons.append(record)
    for label,run in [('original',old),('routed',new)]:
        summaries[label]={}
        for kind in ('min','max'):
            resolved=[v for k,v in run[1].items() if k[2]==kind and v is not None]
            constrained=[v for v in resolved if v['_classification']=='constrained_path']
            summaries[label][kind]=dict(constrained=len(constrained),reported_unconstrained=len(resolved)-len(constrained),
              no_reported_path=sum(k[2]==kind and v is None for k,v in run[1].items()),
              violations=sum(number(v['SLACK'])<0 for v in constrained),minimum_slack_ns=str(min(number(v['SLACK']) for v in constrained)) if constrained else None)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'auditor.py')
    (out/'load_paths.json').write_text(json.dumps(comparisons,indent=2)+'\n')
    coverage_changed=sum(r['original_status']!=r['routed_status'] for r in comparisons)
    result=dict(schema='dieroute.native_load_slack_audit.v1',status='passed' if coverage_changed==0 else 'coverage_changed',
                loads=len(by_pin),queries_per_design=len(old[1]),summaries=summaries,coverage_changes=coverage_changed,
                hierarchy_alias_loads=dict(original=old[2],routed=new[2]),
                same_start_end_corner_pairs=sum(r.get('same_start_end_corner',False) for r in comparisons),
                manifests={str(d.resolve()/'manifest.json'):sha256(d/'manifest.json') for d in (a.original,a.routed)},
                mapping_audit_sha256=sha256(a.mapping_audit/'audit.json'),
                artifacts={f.name:sha256(f) for f in out.iterdir() if f.is_file()},
                scope='Worst reported timing path through each frozen load, at min and max delay; finite constraints, reported unconstrained paths and no reported paths distinguished',
                limits=['no_reported_path is not a positive timing pass or a proof of the reason for absence.',
                        'Worst paths can differ between snapshots; paired differences are not isolated net-delay budgets.',
                        'No static additive PIP model, joint wirelength/CPD acceptance or board claim.'],board_result=False)
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
