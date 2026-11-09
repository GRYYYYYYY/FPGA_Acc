#!/usr/bin/env python3
"""Independent vectorized census of every native policy byte and terminal owner."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import struct
import numpy as np
from run_native_case import sha256


def main():
    if not __debug__:raise RuntimeError('audit requires Python assertions')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();run=args.run.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    for name in (Path(__file__).name,'run_native_case.py'):shutil.copy2(Path(__file__).with_name(name),out/name)
    rm=json.loads((run/'manifest.json').read_text());assert rm['status']=='passed' and rm['inputs_unchanged']
    graph,mapping,footprint,csr=map(Path,rm['command'][1:5]);arch=bytes.fromhex(rm['architecture_sha256'][:32]);policy=run/'policy'
    for group in ('inputs','parent_manifests'):
        for path,h in rm[group].items():assert sha256(path)==h,path
    for name,h in rm['artifacts'].items():assert sha256(run/name)==h,name
    def raw(path,words):
        assert path.stat().st_size%(4*words)==0
        return np.memmap(path,mode='r',dtype='<u4').reshape(-1,words)
    def container(path,kind,width):
        h=path.open('rb').read(64);magic,major,minor,k,count,size,fp,crc,flags=struct.unpack('<8sHHIQQ16sQQ',h)
        assert (magic,major,minor,k,fp,flags)==(b'FPGAACCP',0,1,kind,arch,1)
        assert size==count*width==path.stat().st_size-64
        return np.memmap(path,mode='r',dtype='u1' if width==1 else '<u4',offset=64,shape=(count,))
    nodes=raw(graph/'nodes.bin',16);pips=raw(graph/'pips.bin',8);pins=raw(footprint/'pins.bin',4);nets=raw(footprint/'nets.bin',16)
    nm=raw(mapping/'footprint_node_map.bin',1)[:,0];pm=raw(mapping/'footprint_pip_map.bin',1)[:,0]
    original=container(csr/'protection.bin',0x44520003,1)
    node_flags=container(policy/'node_protection.bin',0x44520004,1)
    terminals=container(policy/'terminal_net.bin',0x44520005,4)
    pip_flags=container(policy/'pip_protection.bin',0x44520006,1)
    intents={int(r['id']):r['name'] for r in csv.DictReader((graph/'intents.csv').open())}
    clocks=np.zeros(max(intents)+1,dtype=np.uint8)
    for i,name in intents.items():clocks[i]=16 if name.startswith('NODE_GLOBAL_') or name in ('CLKPIN','GLOBAL','BUFGROUT','REFCLK') else 0
    chunk=2_000_000;clock_count=0;protected_count=0
    for start in range(0,len(nodes),chunk):
        end=min(start+chunk,len(nodes));extra=clocks[nodes[start:end,7]];expected=original[start:end]|extra
        assert np.array_equal(expected,node_flags[start:end]);clock_count+=int(np.count_nonzero(extra));protected_count+=int(np.count_nonzero(expected))
    candidate=pins[nets[pins[:,0],0]==0];pin_nodes=nm[candidate[:,1]]
    order=np.lexsort((candidate[:,0],pin_nodes));sorted_nodes=pin_nodes[order];sorted_owners=candidate[order,0]
    assert not np.any((sorted_nodes[1:]==sorted_nodes[:-1])&(sorted_owners[1:]!=sorted_owners[:-1]))
    expected_terminals=np.full(len(nodes),0xffffffff,dtype='<u4');expected_terminals[pin_nodes]=candidate[:,0]
    assert np.array_equal(expected_terminals,terminals)
    assert not np.any(node_flags[pin_nodes]);terminal_count=int(np.count_nonzero(expected_terminals!=0xffffffff));del expected_terminals
    raw_arcs=permitted_arcs=restricted_pips=missing=foreign_pairs=0
    incoming=np.zeros(len(nodes),dtype=np.bool_)
    for start in range(0,len(pips),chunk):
        end=min(start+chunk,len(pips));data=pips[start:end];a=data[:,1];b=data[:,2];flags=data[:,7]
        valid=(a!=0xffffffff)&(b!=0xffffffff);expected=(flags&(4|8|16|32|128)).astype(np.uint8);expected[~valid]|=128
        assert np.array_equal(expected,pip_flags[start:end]);restricted_pips+=int(np.count_nonzero(expected));missing+=int(np.count_nonzero(~valid))
        a=a[valid];b=b[valid];f=flags[valid];weight=((f&2)!=0).astype(np.uint64)+1;raw_arcs+=int(weight.sum())
        incoming[b[((f&2)!=0)|((f&1)==0)]]=True;incoming[a[((f&2)!=0)|((f&1)!=0)]]=True
        allowed=(expected[valid]==0)&(node_flags[a]==0)&(node_flags[b]==0)
        x=terminals[a];y=terminals[b];foreign=(x!=0xffffffff)&(y!=0xffffffff)&(x!=y)
        foreign_pairs+=int(weight[allowed&foreign].sum());permitted_arcs+=int(weight[allowed&~foreign].sum())
    fp=raw(footprint/'pips.bin',8);candidate_pips=0
    for start in range(0,len(fp),chunk):
        data=fp[start:start+chunk];use=nets[data[:,0],0]==0;data=data[use];ids=pm[start:start+chunk][use];candidate_pips+=len(data)
        a=nm[data[:,1]];b=nm[data[:,2]];net=data[:,0]
        assert not np.any(pip_flags[ids]) and not np.any(node_flags[a]) and not np.any(node_flags[b])
        assert np.all((terminals[a]==0xffffffff)|(terminals[a]==net)) and np.all((terminals[b]==0xffffffff)|(terminals[b]==net))
    tasks=raw(footprint/'tasks.bin',8);sources=np.unique(nm[tasks[:,2]]);sinks=nm[tasks[:,3]]
    assert np.all(terminals[nm[tasks[:,2]]]==tasks[:,1]) and np.all(terminals[sinks]==tasks[:,1])
    measured={'nodes':len(nodes),'pips':len(pips),'raw_arcs':raw_arcs,'policy_permitted_arcs_before_net_specific_checks':permitted_arcs,
              'protected_nodes':protected_count,'clock_intent_nodes':clock_count,'restricted_native_pips':restricted_pips,'missing_endpoint_pips':missing,
              'different_terminal_owner_arcs':foreign_pairs,'exclusive_candidate_pin_nodes':terminal_count,'candidate_pins_checked':len(candidate),
              'candidate_pips_checked':candidate_pips,'candidate_tasks_checked':len(tasks),'candidate_source_nodes_with_incoming_arcs':int(incoming[sources].sum()),
              'multi_slr_source_nodes':int(np.count_nonzero(nodes[sources,5]&(nodes[sources,5]-1))),
              'multi_slr_sink_tasks':int(np.count_nonzero(nodes[sinks,5]&(nodes[sinks,5]-1))),'cross_slr_tasks':int(np.count_nonzero(tasks[:,4]!=tasks[:,5]))}
    audit=json.loads((policy/'audit.json').read_text())
    assert all(audit[k]==v for k,v in measured.items()),{k:[v,audit[k]] for k,v in measured.items() if audit[k]!=v}
    report={'schema':'dieroute.native_policy_independent_audit.v1','passed':True,'every_policy_entry_and_terminal_owner_checked':True,
            'run_manifest':str(run/'manifest.json'),'run_manifest_sha256':sha256(run/'manifest.json'),'numpy_version':np.__version__,'counts':measured,
            'scope':'independent conversion/metrics audit, not a new routing algorithm or commercial design legality proof'}
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,**measured}))


if __name__=='__main__':main()
