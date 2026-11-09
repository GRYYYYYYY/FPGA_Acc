"""Native feedback wire-format, provenance binding and adversarial host inputs."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from native_csr_test import FINGERPRINT,table
from native_search_graph_test import container
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from run_native_timing_feedback import picoseconds


def main():
    p=argparse.ArgumentParser();p.add_argument('--host',type=Path,required=True);a=p.parse_args()
    for value,expected in [('0.004',4),('-0.001',-1),('1.434',1434),('9223372036854775.807',2**63-1)]:
        assert picoseconds(value)==expected
    for value in ['0.0001','NaN','Infinity','9223372036854775.808']:
        try:picoseconds(value)
        except ValueError:pass
        else:raise AssertionError('nonexact/nonfinite/out-of-range slack accepted')
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);base=root/'input'
        for name in ('graph','search','footprint','mapping','route','snapshots'):(base/name).mkdir(parents=True)
        originals={n:[n*10,n,n*10+1] for n in range(1,4)}
        proposals={n:[n*10,4 if n==1 else n-1,n*10+1] for n in range(1,4)}
        pairs=sorted({(s,d) for groups in (originals,proposals) for path in groups.values() for s,d in zip(path,path[1:])})
        keys={pair:i*2 for i,pair in enumerate(pairs)}
        table(base/'graph/nodes.bin',[[n,n,0,n,0,1,1,0,0,0,0,0,0,0,0,0] for n in range(40)])
        table(base/'graph/pips.bin',[[i,s,d,0,i,0,0,0] for i,(s,d) in enumerate(pairs)])
        table(base/'mapping/footprint_node_map.bin',[[n] for n in range(40)])
        oldpips=[];pipmap=[];nets=[[0]*16 for _ in range(4)]
        for net,path in originals.items():
            nets[net][5]=len(oldpips);nets[net][6]=2
            for s,d in zip(path,path[1:]):oldpips.append([net,s,d,0,keys[s,d]//2,0,0,0]);pipmap.append([keys[s,d]//2])
        table(base/'footprint/nets.bin',nets);table(base/'footprint/pips.bin',oldpips);table(base/'mapping/footprint_pip_map.bin',pipmap)
        table(base/'footprint/tasks.bin',[[i,n,n*10,n*10+1,0,0,0,0] for i,n in enumerate(originals)])
        table(base/'footprint/owners.bin',[[n,net] for net,path in originals.items() for n in path])
        offsets=[0];arcs=[]
        for n in range(40):arcs.extend(sorted((d,keys[s,d]) for s,d in pairs if s==n));offsets.append(len(arcs))
        container(base/'search/offsets.bin',0x44520001,8,struct.pack('<41Q',*offsets))
        container(base/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*arc) for arc in arcs))
        container(base/'search/node_protection.bin',0x4452000a,1,bytes(40))
        container(base/'search/exclusive_net.bin',0x4452000b,4,struct.pack('<40I',*([0xffffffff]*40)))
        (base/'route/selection.csv').write_text('task,net,source,sink,selection_seed\n'+''.join(f'{i},{n},{n*10},{n*10+1},1\n' for i,n in enumerate(originals)))
        def tree_rows(paths):
            result=[]
            for net,path in paths.items():
                for depth,n in enumerate(path):
                    result.append((net,n,path[depth-1] if depth else 0xffffffff,keys[path[depth-1],n] if depth else 0xffffffff,depth))
            return sorted(result)
        (base/'route/trees.csv').write_text('repeat,net,node,parent,pip_key,depth\n'+''.join('0,'+','.join(map(str,r))+'\n' for r in tree_rows(proposals)))
        (base/'route/usage.csv').write_text('repeat,node,net,history,version\n'+''.join(f'0,{n},{net},2,7\n' for net,path in proposals.items() for n in sorted(path)))
        def snapshot(paths,epoch,hold):
            return ('dieroute.native_timing_snapshot.v1\ncontext '+'a'*64+f'\nepoch {epoch}\n'+
                    ''.join('T '+' '.join(map(str,r))+'\n' for r in tree_rows(paths))+
                    ''.join(f'L {n} {n} setup finite 1434\nL {n} {n} hold finite {hold if n==1 else 29}\n' for n in paths)+'end\n')
        (base/'snapshots/baseline.timing').write_text(snapshot(originals,0,29))
        (base/'snapshots/proposal.timing').write_text(snapshot(proposals,1,4))
        cases=[('good',None,True),('tree_binding',lambda s:s.replace('T 1 4 10','T 1 4 20'),False),
               ('stale',lambda s:s.replace('epoch 1','epoch 0'),False),
               ('context',lambda s:s.replace('context '+'a'*64,'context '+'b'*64),False),
               ('duplicate',lambda s:s.replace('end\n','L 1 1 hold finite 4\nend\n'),False),
               ('unsigned_negative',lambda s:s.replace('L 1 1 hold','L -1 1 hold'),False),
               ('missing_end',lambda s:s.replace('end\n',''),False),
               ('trailing',lambda s:s+'garbage\n',False),
               ('missing_path',lambda s:s.replace('hold finite 4','hold missing NA'),False),
               ('overflow',lambda s:s.replace('hold finite 4','hold finite 9223372036854775808'),False)]
        for name,mutate,ok in cases:
            case=root/name;shutil.copytree(base,case)
            if mutate:
                file=case/'snapshots/proposal.timing';file.write_text(mutate(file.read_text()))
            command=[str(a.host.resolve()),*[str(case/d) for d in ('graph','search','footprint','mapping')],FINGERPRINT,str(case/'route'),str(case/'snapshots'),str(case/'result'),'0','20','0']
            result=subprocess.run(command,capture_output=True,text=True)
            assert (result.returncode==0)==ok,(name,result.stderr)
            if ok:
                decision=json.loads((case/'result/decision.json').read_text());assert decision['restored_nets']==[1,2,3] and decision['hold_violations']==1
                for name in ('trees.csv','usage.csv'):
                    assert (case/'result/authority'/name).read_bytes()==(case/'result/baseline'/name).read_bytes()
            else:assert not (case/'result/authority').exists(), 'malformed oracle published authority'
        # The host handoff must preserve owner placement through hold repair.
        # All trees and canonical versions remain equal to the centralized case.
        from audit_native_owner import verify_owner_usage
        for mode in ('partition','missing_flag','wrong_owner','missing_inventory'):
            case=root/mode;shutil.copytree(base,case)
            memberships=[6 if n==2 else 1<<(n%3) for n in range(40)]
            table(case/'graph/nodes.bin',[[n,n,0,n,0,memberships[n],1,0,0,0,0,0,0,0,0,0] for n in range(40)])
            with (case/'route/usage.csv').open() as stream:uses=list(csv.DictReader(stream))
            owner_rows=[dict(repeat=0,owner=(memberships[int(r['node'])]&-memberships[int(r['node'])]).bit_length()-1,**{k:int(v) for k,v in r.items() if k!='repeat'}) for r in uses]
            owner_rows.sort(key=lambda r:(r['owner'],r['node'],r['net']))
            if mode=='wrong_owner':owner_rows[0]['owner']=(owner_rows[0]['owner']+1)%3
            if mode!='missing_inventory':
                with (case/'route/owner_usage.csv').open('w') as stream:
                    writer=csv.DictWriter(stream,fieldnames=['repeat','owner','node','net','history','version'],lineterminator='\n');writer.writeheader();writer.writerows(owner_rows)
            command=[str(a.host.resolve()),*[str(case/d) for d in ('graph','search','footprint','mapping')],FINGERPRINT,str(case/'route'),str(case/'snapshots'),str(case/'result'),'0','20','0']
            if mode!='missing_flag':command.append('1')
            result=subprocess.run(command,capture_output=True,text=True)
            assert (result.returncode==0)==(mode=='partition'),(mode,result.stderr)
            if mode=='partition':
                for phase in ('baseline','proposal','authority','candidate'):
                    for filename in ('trees.csv','usage.csv','tree_identity.txt'):
                        assert (case/'result'/phase/filename).read_bytes()==(root/'good/result'/phase/filename).read_bytes()
                    audit=verify_owner_usage(case/'result'/phase,(case/'graph/nodes.bin').read_bytes(),True,1)
                    assert {r['owner'] for r in audit['records']}=={0,1,2}
            else:assert not (case/'result/authority').exists()
    print('14 native feedback host cases, owner-preserving repair and exact ps checks passed')


if __name__=='__main__':main()
