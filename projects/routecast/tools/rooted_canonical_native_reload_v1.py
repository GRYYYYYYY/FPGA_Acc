"""Original VPR identity/FULL/STA reload with explicit SDC and routed IPIN pins.

Call only after independent original-route correctness and memory admission.
This function preserves every native failure; no timeout or partial acceptance.
"""
import json
import os
import re
import resource
import subprocess
import time
import xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path
from audit_native_route import NODE
from rooted_canonical_route_text_v2 import render,physical_sequences
from prepare_canonical_reload_inputs_v1 import prepare
from pre_route_endpoints import sha
from stream_native_route_audit import audit

def selected_geometry(graph,wanted):
    nodes={};grid={};classes={};stack=[]
    for event,node in E.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(node);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if node.tag=='block_type' and parent=='block_types':
            tid=int(node.get('id'));assert tid not in classes;classes[tid]={}
            for cid,cls in enumerate(node.findall('pin_class')):
                for pin in cls.findall('pin'):
                    ptc=int(pin.get('ptc'));assert ptc not in classes[tid];classes[tid][ptc]=cid
            stack[-2].remove(node);node.clear()
        elif node.tag=='grid_loc' and parent=='grid':
            key=tuple(int(node.get(k,'0')) for k in ['x','y','layer']);assert key not in grid
            grid[key]=tuple(int(node.get(k)) for k in ['block_type_id','width_offset','height_offset'])
            stack[-2].remove(node);node.clear()
        elif node.tag=='node' and parent=='rr_nodes':
            nid=int(node.get('id'))
            if nid in wanted:
                assert int(node.get('capacity'))>0 and nid not in nodes
                nodes[nid]=dict(type=node.get('type'),loc=dict(node.find('loc').attrib))
            stack[-2].remove(node);node.clear()
        if node.tag=='rr_nodes':break
        stack.pop()
    assert set(nodes)==wanted
    return nodes,grid,classes

def reload(candidate,source,destination,identity_binary,reload_binary,*,child_memory_bytes):
    source,destination=Path(source),Path(destination)
    assert all(sha(p)==h for p,h in candidate['files'].items())
    cmd=list(candidate['command']);assert '--route' in cmd and '--read_rr_graph' in cmd
    graph=Path(cmd[cmd.index('--read_rr_graph')+1]);route=source/cmd[cmd.index('--route_file')+1]
    inputs=prepare(source,destination,sdc_required='--sdc_file' in cmd)
    before=dict(graph=sha(graph),route=sha(route));env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
    cmd[0]=str(reload_binary);cmd[cmd.index('--route')]='--analysis'
    cmd[cmd.index('--route_file')+1]='design.route'
    cmd[cmd.index('--net_file')+1]='design.net';cmd[cmd.index('--place_file')+1]='design.place'
    if '--sdc_file' in cmd:cmd[cmd.index('--sdc_file')+1]='design.sdc'
    table=destination/'identity.jsonl';icmd=cmd.copy();icmd[0]=str(identity_binary);icmd[icmd.index('--route_file')+1]='missing.route'
    stages=[]
    def run(label,args,environment):
        def limit():resource.setrlimit(resource.RLIMIT_AS,(child_memory_bytes,child_memory_bytes))
        tick=time.perf_counter()
        with (destination/(label+'.log')).open('x') as log:
            code=subprocess.call(args,cwd=destination,env=environment,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
        row=dict(stage=label,exit_status=code,seconds=time.perf_counter()-tick,command=args)
        stages.append(row);(destination/'stages.json').write_text(json.dumps(stages,indent=2)+'\n')
        return code
    assert run('identity',icmd,{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table),'ROUTECAST_IDENTITY_ONLY':'1'})==1 and table.exists()
    records=[json.loads(line) for line in table.read_text().splitlines()];native={r['name']:r for r in records}
    assert len(native)==len(records)
    lines=route.read_text().splitlines();wanted={int(m[1]) for line in lines if (m:=NODE.match(line))}
    nodes,grid,classes=selected_geometry(graph,wanted)
    canonical,pins=render(lines,native,nodes,grid,classes,sha(destination/'design.place'))
    (destination/'design.route').write_text('\n'.join(canonical)+'\n')
    assert run('reload',cmd,env)==0
    text=(destination/'reload.log').read_text()
    assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
    cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);assert cpd==candidate['cpd_ns']
    mismatches=int(re.search(r'Found (\d+) mismatches',text)[1]);fixups=int(re.search(r'Fixed (\d+) routing traces',text)[1])
    pattern=re.compile(r"Fixed up net '([^']*)' mapping mismatch at clustered block '(.*)' pin 'grid\[(\d+)\]\[(\d+)\]\.([^.]*)\.([^\[]*)\[(\d+)\] - layer (\d+)' \(was net '([^']*)'\)")
    allowed=Counter((r['name'],p['block'],p['x'],p['y'],p['layer'],p['port'],p['bit']) for r in records if r['ignored'] for p in r['pins'] if p['index']>0)
    observed=Counter()
    for m in pattern.finditer(text):
        routed,block,x,y,tile,port,bit,layer,old=m.groups();assert routed=='unmapped'
        observed[old,block,int(x),int(y),int(layer),port,int(bit)]+=1
    assert not observed-allowed and sum(observed.values())==mismatches==fixups
    assert (destination/'design.net').read_bytes()==(destination/'design.net.post_routing').read_bytes()
    assert physical_sequences(lines)==physical_sequences((destination/'design.route').read_text().splitlines())
    physical=audit(graph,destination/'design.route');assert physical['overflow_units']==0
    (destination/'physical_audit.json').write_text(json.dumps(physical)+'\n')
    assert before==dict(graph=sha(graph),route=sha(route)) and all(sha(p)==h for p,h in inputs.items())
    return dict(stages=stages,pins=pins,cpd_ns=cpd,original_zero_counter_gate_pass=mismatches==fixups==0,
                native_ignored_only_mismatch_pins=mismatches,packed_netlist_byte_identical=True,
                physical_sequences_identical=True,original_XML_arc_branch_capacity_pass=True,semantic_consistency_gate_pass=True,
                explicit_SDC_preserved='--sdc_file' in cmd,files={str(p):sha(p) for p in destination.iterdir() if p.is_file()},
                scope='Actual original VPR FULL/STA plus actual post-route IPIN/root/pin labels; ignored-only counters, exact packed bytes, physical traces and CPD. Not source HDL, heldout or workflow benefit proof.')
