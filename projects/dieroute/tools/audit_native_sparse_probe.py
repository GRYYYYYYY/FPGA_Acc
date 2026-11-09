#!/usr/bin/env python3
"""Resolve probe paths against raw native PIPs, qualified CSR and net ownership."""
import argparse,csv,json,mmap,struct,time
from collections import defaultdict
from pathlib import Path
from run_native_case import sha256

def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    run=args.run.resolve();rm=json.loads((run/'manifest.json').read_text());assert rm['status']=='passed' and rm['inputs_unchanged']
    _,graph,search,footprint,mapping,arch,probe,limit,take,repeats=rm['command'][:10]
    graph,search,footprint,mapping,probe=map(Path,(graph,search,footprint,mapping,probe));limit,take,repeats=map(int,(limit,take,repeats))
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    inputs=dict(rm['inputs']);inputs[str(run/'manifest.json')]=sha256(run/'manifest.json')
    gm=graph.parent/'manifest.json';inputs[str(gm)]=sha256(gm);inputs[str(graph/'pips.bin')]=json.loads(gm.read_text())['artifacts']['graph/pips.bin']
    for name in ('results.csv','paths.csv','audit.json'):inputs[str(probe/name)]=rm['artifacts']['probe_output/'+name]
    for path,digest in inputs.items():assert sha256(path)==digest,path
    files=[];maps=[]
    def mapped(path):
        f=Path(path).open('rb');files.append(f);m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);maps.append(m);return m
    def raw(path,width):
        m=mapped(path);assert len(m)%width==0;return m
    def container(path,kind,width):
        m=mapped(path);h=struct.unpack_from('<8sHHIQQ16sQQ',m);assert h[:4]==(b'FPGAACCP',0,1,kind) and h[6].hex()==arch and h[8]==1
        assert h[4]*width==h[5]==len(m)-64;return m
    nodes=raw(graph/'nodes.bin',64);pips=raw(graph/'pips.bin',32);tasks=raw(footprint/'tasks.bin',32);nm=raw(mapping/'footprint_node_map.bin',4)
    offsets=container(search/'offsets.bin',0x44520001,8);arcs=container(search/'arcs.bin',0x44520002,8)
    masks=container(search/'node_protection.bin',0x4452000a,1);owners=container(search/'exclusive_net.bin',0x4452000b,4)
    def node_id(old):return struct.unpack_from('<I',nm,old*4)[0]
    groups=defaultdict(int);selected=[]
    for task in range(len(tasks)//32):
        record=struct.unpack_from('<8I',tasks,task*32);assert record[0]==task
        pair=record[4:6]
        if groups[pair]<take:selected.append(task)
        groups[pair]+=1
    rows=list(csv.DictReader((probe/'results.csv').open()));paths=defaultdict(list)
    for row in csv.DictReader((probe/'paths.csv').open()):
        row={k:int(v) for k,v in row.items()};paths[(row['repeat'],row['task'])].append(row)
    assert [(int(r['repeat']),int(r['task'])) for r in rows]==[(rep,t) for rep in range(repeats) for t in selected]
    previous={};counts=defaultdict(int);pair_counts=defaultdict(lambda:defaultdict(int));pips_checked=0;cross_paths=0;max_workspace=0;max_touched=0
    for row in rows:
        rep,task=int(row['repeat']),int(row['task']);record=struct.unpack_from('<8I',tasks,task*32);net=record[1];src,dst=map(node_id,record[2:4]);path=paths.pop((rep,task),[])
        assert [int(row[k]) for k in ('net','source','sink','source_slr','sink_slr')]==[net,src,dst,*record[4:6]]
        assert int(row['touched'])<=limit and int(row['expanded'])<=int(row['touched'])
        max_workspace=max(max_workspace,int(row['workspace_bytes']));max_touched=max(max_touched,int(row['touched']))
        def allowed(n):return masks[64+n]==0 and struct.unpack_from('<I',owners,64+4*n)[0] in (0xffffffff,net)
        assert allowed(src) and allowed(dst)
        status=row['status'];assert status in ('found','budget_exhausted') # Original candidates are known reachable.
        counts[status]+=1;pair_counts[str(record[4])+'->'+str(record[5])][status]+=1
        signature={k:v for k,v in row.items() if k not in ('repeat','workspace_bytes','quotient_workspace_bytes')}
        signature['path']=[(r['source'],r['destination'],r['pip_key']) for r in path]
        if task in previous:assert previous[task]==signature,task
        previous[task]=signature
        if status!='found':assert not path;continue
        assert len(path)==int(row['hops']);assert int(row.get('lower_bound',0))<=len(path)
        current=src;visited={src};sll=0
        for step,r in enumerate(path):
            assert r['step']==step and r['source']==current and allowed(r['destination'])
            dest,key=r['destination'],r['pip_key'];pid,reverse=key>>1,key&1
            native=struct.unpack_from('<8I',pips,pid*32);assert native[0]==pid
            assert not reverse or native[7]&2
            assert tuple(native[1:3][::-1] if reverse else native[1:3])==(current,dest)
            lo=struct.unpack_from('<Q',offsets,64+current*8)[0];end=struct.unpack_from('<Q',offsets,64+(current+1)*8)[0];hi=end
            while lo<hi:
                mid=(lo+hi)//2
                if struct.unpack_from('<II',arcs,64+8*mid)<(dest,key):lo=mid+1
                else:hi=mid
            assert lo<end and struct.unpack_from('<II',arcs,64+8*lo)==(dest,key)
            assert dest not in visited;visited.add(dest);current=dest;pips_checked+=1
            membership=struct.unpack_from('<I',nodes,dest*64+20)[0];sll+=bool(membership&(membership-1))
        assert current==dst
        if record[4]!=record[5]:assert sll>0;cross_paths+=1
    assert not paths
    for m in maps:m.close()
    for f in files:f.close()
    for path,digest in inputs.items():assert sha256(path)==digest,path
    report=dict(schema='dieroute.native_sparse_probe_audit.v1',passed=True,inputs=inputs,inputs_unchanged=True,finished_ns=time.time_ns(),
                selected_tasks=len(selected),repeats=repeats,counts=dict(counts),slr_pairs={k:dict(v) for k,v in pair_counts.items()},
                resolved_pip_occurrences=pips_checked,cross_slr_paths=cross_paths,maximum_retained_workspace_bytes=max_workspace,
                maximum_touched_labels=max_touched,repeat_comparison_performed=repeats>1,
                repeated_paths_and_search_counts_identical=True if repeats>1 else None,
                scope='Raw PIP identity, net permission, exact selected CSR arcs, simple paths and repeat equality; no physical timing, negotiated routing, optimality proof or native DCP legality')
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('inputs','slr_pairs')}))
if __name__=='__main__':main()
