"""Actual-output negative controls for final tree/resource reconstruction."""
import argparse,json,struct,subprocess,sys,tempfile
from pathlib import Path
from persistent_vpr_timing import sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_prefix',type=Path);p.add_argument('output_prefix',type=Path);p.add_argument('directory',type=Path);a=p.parse_args()
    inp,out,directory=[p.resolve() for p in (a.input_prefix,a.output_prefix,a.directory)];directory.mkdir(exist_ok=False)
    auditor=Path(__file__).with_name('audit_rr_final_tree_state.py');results=[]
    for name in ['pristine','occupancy','owner','cycle','truncated_connection']:
        with tempfile.TemporaryDirectory(prefix='dieroute_final_state_') as temporary:
            prefix=Path(temporary)/'route'
            for suffix in ['.resources','.route_trees.csv','.paths.csv']:Path(str(prefix)+suffix).symlink_to(Path(str(out)+suffix))
            if name in ['occupancy','owner']:
                target=Path(str(prefix)+'.resources');data=bytearray(target.read_bytes());target.unlink()
                values=list(struct.iter_unpack('<HHHHII',data));index=next(i for i,v in enumerate(values) if v[0]>0);row=list(values[index]);row[0 if name=='occupancy' else 5]^=1;struct.pack_into('<HHHHII',data,index*16,*row);target.write_bytes(data)
            elif name=='cycle':
                target=Path(str(prefix)+'.route_trees.csv');rows=target.read_text().splitlines();target.unlink();row=rows[1].split(',');row[2]=row[3];rows[1]=','.join(row);target.write_text('\n'.join(rows)+'\n')
            elif name=='truncated_connection':
                target=Path(str(prefix)+'.paths.csv');rows=target.read_text().splitlines();target.unlink();target.write_text('\n'.join(rows[:-1])+'\n')
            with (directory/(name+'.log')).open('w') as log:r=subprocess.run([sys.executable,str(auditor),str(inp),str(prefix),'--report',str(Path(temporary)/'audit.json')],stdout=log,stderr=subprocess.STDOUT)
            assert (r.returncode==0)==(name=='pristine'),name
            results.append(dict(name=name,returncode=r.returncode,log_sha256=sha(directory/(name+'.log'))))
    (directory/'audit.json').write_text(json.dumps(dict(status='final_tree_state_auditor_actual_output_pristine_and_four_corruptions_checked',cases=results,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),auditor,*[Path(str(out)+s) for s in ['.resources','.route_trees.csv','.paths.csv']]]},scope='Final exported-state verifier negative controls only;not epoch/version replay or hardware coherence',board_result=False,research_complete=False),indent=2)+'\n')
