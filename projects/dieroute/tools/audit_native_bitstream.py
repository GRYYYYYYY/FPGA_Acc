#!/usr/bin/env python3
"""Validate native generation receipts and bit-file envelopes, not device operation."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
from run_native_case import sha256


def bit_header(path):
    """Read the tagged .bit envelope; packet/frame correctness remains Vivado's check."""
    with Path(path).open('rb') as f:
        def take(n):
            data=f.read(n)
            if len(data)!=n:raise ValueError('truncated bitstream header/payload prefix')
            return data
        def short():return struct.unpack('>H',take(2))[0]
        if short()!=9 or take(9)!=bytes.fromhex('0ff00ff00ff00ff000') or short()!=1:
            raise ValueError('unsupported bitstream envelope')
        values={}
        for tag,name in ((b'a','design'),(b'b','part'),(b'c','date'),(b'd','time')):
            if take(1)!=tag:raise ValueError('missing/reordered bitstream header tag')
            raw=take(short())
            if not raw or raw[-1:]!=b'\0' or b'\0' in raw[:-1]:raise ValueError('invalid bitstream header string')
            values[name]=raw[:-1].decode('ascii')
        if take(1)!=b'e':raise ValueError('missing bitstream payload tag')
        size=struct.unpack('>I',take(4))[0];offset=f.tell()
        if size==0 or offset+size!=Path(path).stat().st_size:raise ValueError('bitstream payload length mismatch')
        prefix=take(min(size,4096));sync=prefix.find(bytes.fromhex('aa995566'))
        if sync<0 or sync%4:raise ValueError('missing/alignment-invalid configuration synchronization word')
        values.update(payload_offset=offset,payload_bytes=size,sync_offset_within_payload=sync)
        return values


def route_counts(text):
    counts={label.strip():int(value) for label,value in re.findall(r'# of ([^.\n]+)\.+\s*:\s*(\d+)\s*:',text)}
    required={'logical nets','routable nets','fully routed nets','nets with routing errors'}
    if not required<=counts.keys():raise ValueError('incomplete route status')
    if counts['routable nets']==0 or counts['fully routed nets']!=counts['routable nets'] or counts['nets with routing errors']:
        raise ValueError('bitstream design not fully routed')
    return counts


def payload_sha256(path):
    header=bit_header(path);digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        stream.seek(header['payload_offset'])
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def drc_counts(text):
    total=re.search(r'Violations found:\s*(\d+)',text)
    if not total:raise ValueError('missing bitstream DRC total')
    rules={};severities=Counter()
    for line in text.splitlines():
        cols=[v.strip() for v in line.split('|')]
        if len(cols)==6 and re.fullmatch(r'[A-Z0-9]+-\d+',cols[1]):
            if cols[1] in rules or cols[2] not in ('Warning','Advisory','Critical Warning','Error'):raise ValueError('invalid DRC summary row')
            count=int(cols[4]);rules[cols[1]]=dict(severity=cols[2],count=count);severities[cols[2]]+=count
    if sum(severities.values())!=int(total[1]):raise ValueError('incomplete bitstream DRC summary')
    if severities['Error'] or severities['Critical Warning']:raise ValueError('bitstream DRC contains errors/critical warnings')
    return dict(total=int(total[1]),rules=rules,severities=dict(severities))


def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--ruledeck-reference',type=Path,help='Rule enumeration from a separate empty-design probe using this toolchain')
    p.add_argument('--comparison-run',type=Path,help='Compare generated payloads with an archived prior attempt, without accepting that attempt')
    a=p.parse_args();run=a.run.resolve();out=a.output.resolve();rm=json.loads((run/'manifest.json').read_text())
    assert rm['status']=='bitstreams_generated' and rm['returncode']==0 and rm['inputs_unchanged']
    inputs=dict(rm['inputs']);inputs[str(run/'manifest.json')]=sha256(run/'manifest.json')
    inputs.update({str(run/name):digest for name,digest in rm['artifacts'].items()})
    if a.ruledeck_reference:inputs[str(a.ruledeck_reference.resolve())]=sha256(a.ruledeck_reference)
    previous=None
    if a.comparison_run:
        previous=a.comparison_run.resolve();old=json.loads((previous/'manifest.json').read_text())
        assert old['status'] in ('failed','bitstreams_generated')
        assert old['inputs']=={path:rm['inputs'][path] for path in old['inputs']}
        assert old['command'][0]==rm['command'][0]
        assert old['artifacts']['check_native_bitstream.tcl']==rm['artifacts']['check_native_bitstream.tcl']
        inputs[str(previous/'manifest.json')]=sha256(previous/'manifest.json')
        inputs.update({str(previous/name):value for name,value in old['artifacts'].items()})
    for path,digest in inputs.items():assert sha256(path)==digest,path
    directory=run/'output'
    assert (directory/'completed.txt').read_text()=='write_bitstream_completed=true\nroute_design_invoked=false\ndevice_programmed=false\n'
    before=route_counts((directory/'before_route_status.rpt').read_text());after=route_counts((directory/'after_route_status.rpt').read_text())
    assert before==after,'route status changed during generation'
    design=dict(line.split('=',1) for line in (directory/'design.txt').read_text().splitlines())
    assert design['part']==rm['expected_part']
    drc=drc_counts((directory/'bitstream_drc.rpt').read_text())
    rules=list(csv.DictReader((directory/'drc_checks.tsv').open(),delimiter='\t'))
    assert rules and len({r['check'] for r in rules})==len(rules)
    assert all(r['enabled'] in ('0','1','true','false') for r in rules)
    deck=dict(line.split('=',1) for line in (directory/'drc_ruledeck.txt').read_text().splitlines())
    assert deck['name']=='bitstream_checks' and deck['factory'] in ('1','true') and deck['enumeration_apis_equal']=='true'
    assert int(deck['enumerated_checks'])==len(rules) and int(deck['declared_size'])>0
    reference_equal=None
    if a.ruledeck_reference:
        reference=list(csv.DictReader(a.ruledeck_reference.open(),delimiter='\t'))
        reference_equal=sorted(reference,key=lambda r:r['check'])==sorted(rules,key=lambda r:r['check'])
        assert reference_equal,'enumerated rule names, enabled state or severity changed from reference'
    entries=list(csv.DictReader((directory/'bitstreams.tsv').open(),delimiter='\t'));seen=set();bits=[]
    for row in entries:
        name=row['file'];assert Path(name).name==name and name.endswith('.bit') and name not in seen;seen.add(name)
        path=directory/name;assert int(row['bytes'])==path.stat().st_size
        header=bit_header(path)
        # Vivado envelopes can omit the speed/temperature suffix from PART.
        expected=rm['expected_part'].split('-')
        assert header['part'] in (rm['expected_part'],'-'.join(expected[:2]),''.join(expected[:2])),header['part']
        bits.append(dict(file=name,bytes=path.stat().st_size,sha256=sha256(path),header=header))
    assert 'candidate.bit' in seen and seen=={p.name for p in directory.glob('*.bit')}
    comparisons=[]
    if previous:
        assert seen=={p.name for p in (previous/'output').glob('*.bit')}
        for name in sorted(seen):
            before=payload_sha256(previous/'output'/name);after=payload_sha256(directory/name)
            comparisons.append(dict(file=name,previous_payload_sha256=before,current_payload_sha256=after,payload_equal=before==after))
    for path,digest in inputs.items():assert sha256(path)==digest,path
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'auditor.py')
    result=dict(schema='dieroute.native_bitstream_audit.v1',status='native_bitstream_checks_passed',inputs=inputs,inputs_unchanged=True,
                design=design,route=after,route_status_unchanged=True,drc=drc,ruledeck_checks=len(rules),ruledeck_metadata=deck,
                enumerated_rules_equal_reference=reference_equal,
                previous_attempt_payload_comparisons=comparisons,
                disabled_rules=[r['check'] for r in rules if r['enabled'] in ('0','false')],bitstreams=bits,
                auditor_sha256=sha256(out/'auditor.py'),board_result=False,device_programmed=False,
                limits=['Envelope parsing does not independently decode configuration frames or verify their hardware meaning.',
                        'This is bitstream generation for the rerouted workload, not a DieRoute accelerator implementation.',
                        'No xclbin deployment compatibility, device programming, board performance or energy claim.'])
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','disabled_rules')}))


if __name__=='__main__':main()
