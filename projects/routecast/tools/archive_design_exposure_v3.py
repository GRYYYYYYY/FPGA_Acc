"""Bounded declared-source identity inventory; never certifies unseen families."""
import datetime,hashlib,json,re,resource,subprocess
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
SUFFIXES={'.blif','.eblif','.v','.sv','.vhd','.vhdl'}
HEX=re.compile('[0-9a-f]{64}')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()


def declarations(value,where=()):
    if isinstance(value,dict):
        path=value.get('path')
        if isinstance(path,str) and Path(path).suffix.lower() in SUFFIXES:
            yield dict(json_location=list(where),path=path,declared_sha256=value.get('sha256'))
        for key,item in value.items():
            if isinstance(key,str) and Path(key).suffix.lower() in SUFFIXES and isinstance(item,str) and HEX.fullmatch(item):
                yield dict(json_location=list(where)+( [key]),path=key,declared_sha256=item)
            yield from declarations(item,where+(str(key),))
    elif isinstance(value,list):
        for i,item in enumerate(value):yield from declarations(item,where+(str(i),))


def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*2**20,512*2**20))
    run=subprocess.run(['rg','--files','--hidden','-g','protocol.json','experiments'],cwd=R,text=True,capture_output=True,check=True)
    paths=sorted(set(run.stdout.splitlines()));records=[];unresolved=[];hashes={};groups=defaultdict(list)
    for name in paths:
        p=R/name
        try:
            before=p.stat();digest=sha(p)
            if before.st_size>2**21:
                unresolved.append(dict(protocol=name,reason='above2MiB_decode_bound',bytes=before.st_size));hashes[name]=digest;continue
            data=json.loads(p.read_text());after=p.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or sha(p)!=digest:
                unresolved.append(dict(protocol=name,reason='changed_during_read'));continue
            hashes[name]=digest;rows=list(declarations(data))
            if not rows:unresolved.append(dict(protocol=name,reason='no_declared_source_identity'))
            for row in rows:
                h=row['declared_sha256'];valid=isinstance(h,str) and HEX.fullmatch(h) is not None
                row.update(protocol=name,protocol_sha256=digest,declared_sha256=h if isinstance(h,str) else None,identity_hash_valid=valid,filename_stem=Path(row['path']).stem)
                index=len(records);records.append(row)
                groups[h if valid else 'unknown:'+row['path']].append(index)
        except (FileNotFoundError,json.JSONDecodeError,UnicodeDecodeError,RecursionError) as error:
            unresolved.append(dict(protocol=name,reason=type(error).__name__))
    changed=[]
    for name,h in hashes.items():
        try:
            if sha(R/name)!=h:changed.append(name)
        except FileNotFoundError:changed.append(name)
    out=R/'experiments/design_exposure_inventory_v3_2026-10-15';out.mkdir()
    result=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=sha(__file__),protocol_count=len(paths),stable_protocol_hashes=hashes,protocols_changed_before_finish=changed,declared_source_records=records,exposure_by_declared_content_identity=dict(groups),unresolved_protocols=unresolved,filename_stems=sorted({r['filename_stem'] for r in records}),all_strict_family_admission_flags_false=True,scope='Local protocol declarations of BLIF/EBLIF/Verilog/SystemVerilog/VHDL source identities only. Declared source hashes are not reauthenticated here; declarations do not prove successful route/model or label exposure. Equal content hashes establish declared identity, not family independence. Missing references, indirect inputs, archive gaps, other projects and global history remain unknown. No unseen family certified.')
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(protocols=len(paths),source_records=len(records),declared_identity_groups=len(groups),unresolved_protocols=len(unresolved),changed_before_finish=changed,strict_family_admitted=0,stems=result['filename_stems']),indent=2))


if __name__=='__main__':main()
