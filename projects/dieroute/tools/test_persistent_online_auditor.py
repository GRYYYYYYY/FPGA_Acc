"""Negative controls for online timing/router equivalence checking."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from persistent_vpr_timing import sha

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pair',type=Path);parser.add_argument('online',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();pair,online,output=[p.resolve() for p in (args.pair,args.online,args.output)]
    output.mkdir(exist_ok=False)
    auditor=Path(__file__).with_name('audit_persistent_timing_online.py')
    cases=[('pristine',None),('changed_expansion_counter','route.json'),('changed_timing_output','route.timing_iteration_0.output.csv'),('changed_path','route.paths.csv'),('changed_resource_version','route.resources'),('missing_epoch','route.timing_iteration_21.input.csv')]
    results=[]
    for name,filename in cases:
        with tempfile.TemporaryDirectory(prefix='dieroute_audit_') as temporary:
            directory=Path(temporary)
            for source in online.iterdir():
                if source.is_file(): (directory/source.name).symlink_to(source)
            if filename:
                target=directory/filename;data=target.read_bytes();target.unlink()
                if name=='changed_expansion_counter':
                    value=json.loads(data);value['expanded']+=1;target.write_text(json.dumps(value)+'\n')
                elif name=='missing_epoch':pass
                elif name=='changed_resource_version':
                    altered=bytearray(data);altered[-1]^=1;target.write_bytes(altered)
                else:
                    # Keep text parseable, while changing a real exported row byte.
                    rows=data.splitlines(keepends=True);assert len(rows)>1
                    row=bytearray(rows[1]);position=next(i for i,b in enumerate(row) if 48<=b<=57)
                    row[position]=48+(row[position]-48+1)%10;rows[1]=bytes(row);target.write_bytes(b''.join(rows))
            with (output/(name+'.log')).open('w') as log:
                run=subprocess.run([sys.executable,str(auditor),str(pair),str(directory)],stdout=log,stderr=subprocess.STDOUT)
            assert (run.returncode==0)==(filename is None),name
            results.append(dict(name=name,returncode=run.returncode,expected_accept=filename is None,log_sha256=sha(output/(name+'.log'))))
    (output/'audit.json').write_text(json.dumps(dict(status='online_equivalence_auditor_pristine_and_five_corruptions_checked',cases=results,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),auditor,pair,online/'equivalence_audit.json']},scope='Observed artifact comparator negative controls;not transport failure injection or paired runtime proof',research_complete=False),indent=2)+'\n')
