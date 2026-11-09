"""Posterior two-net diagnostic derived from a frozen relaxed-cut result."""
import collections
import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[1]
T=R/'work/sb_development_roundtrip_preflight_20261015/tools'
sys.path.insert(0,str(T))
from export_native_vpr_tree import extract
from vpr_route_connections import convert
from write_vpr_route import write_route


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda:stream.read(1048576),b''):h.update(b)
    return h.hexdigest()


def main():
    begin=time.monotonic_ns()
    C=R/'work/native_capacity_coverage_20261017/frisc_20x16_seed1'
    D=R/'work/native_single_owner_pin_exchange_20261017';D.mkdir(exist_ok=False)
    cutfile=R/'work/native_single_pin_relaxed_cut_probe_20261017/result.json'
    cut=json.loads(cutfile.read_text());assert cut['minimum_saturated_entries']==1 and len(cut['blocking_nets'])==1
    target=cut['net'];displaced=cut['blocking_nets'][0];assert target!=displaced
    vpr=R/'work/vpr_four_layer_build_20261015/build/vpr/vpr'
    files=[C/n for n in ['circuit.route','rr_graph.xml','circuit.net','circuit.place','architecture.xml','circuit.blif']]+[cutfile,Path(__file__).resolve(),vpr,*[T/n for n in ['export_native_vpr_tree.py','vpr_route_connections.py','write_vpr_route.py','validate_vpr_route_device.py']]]
    (D/'protocol.json').write_text(json.dumps(dict(status='frozen_before_exchange',target=target,displaced=displaced,rule='Apply archived target alternative path and prune obsolete stub. Release one derived blocking net; rebuild all its sinks in original order with deterministic multi-source BFS, preserving original SOURCE/OPIN. Charge shared resources once per net, forbid other-net full resources and other terminals. No other nets change. No tuning/retry on outcomes.',source_sha256={str(p):sha(p) for p in files},scope=__doc__,research_complete=False),indent=2)+'\n')
    original=extract(C/'circuit.route');trees=copy.deepcopy(original)
    adjacency=collections.defaultdict(list);kind={};capacity={}
    for _,e in ET.iterparse(C/'rr_graph.xml',events=('end',)):
        if e.tag=='node':
            n=int(e.attrib['id']);kind[n]=e.attrib['type'];capacity[n]=int(e.attrib['capacity']);e.clear()
        elif e.tag=='edge':
            a,b,s=[int(e.attrib[k]) for k in ['src_node','sink_node','switch_id']];adjacency[a].append((b,s));e.clear()
    conflict=cut['conflict'];sink=cut['sink'];path=[tuple(edge) for edge in cut['path']]
    assert path and all(b in dict(adjacency[a]) for a,b,_ in path)
    for a,b,s in path:assert (b,s) in adjacency[a]
    last=path[-1][1];switch=next(s for b,s in adjacency[last] if b==sink)
    old=trees[target];remaining=[edge for edge in old['edges'] if edge[0]!=conflict and edge[1] not in [conflict,sink]]+path+[(last,sink,switch)]
    parents={b:a for a,b,_ in remaining};assert len(parents)==len(remaining)
    keep={n for n,_ in old['sinks']}
    for n in list(keep):
        seen=set()
        while n!=old['source']:
            assert n not in seen;seen.add(n);n=parents[n];keep.add(n)
    old['edges']=[edge for edge in remaining if edge[1] in keep]
    occupancy=collections.defaultdict(set)
    for n,t in trees.items():
        if n==displaced:continue
        for node in {t['source']}|{v for edge in t['edges'] for v in edge[:2]}:occupancy[node].add(n)
    assert all(len(v)<=capacity[n] for n,v in occupancy.items())
    donor=trees[displaced]
    edges=[edge for edge in donor['edges'] if edge[0]==donor['source'] and kind[edge[1]]=='OPIN']
    assert edges
    nodes={donor['source']}|{b for _,b,_ in edges}
    assert all(len(occupancy[n])+1<=capacity[n] for n in nodes)
    attempts=[];failed=False
    for goal,pin in donor['sinks']:
        if goal in nodes:continue
        queue=collections.deque(sorted(nodes));previous={n:None for n in nodes};found=False
        while queue:
            a=queue.popleft()
            if a==goal:found=True;break
            for b,s in adjacency[a]:
                if b in previous:continue
                if kind[b] in ['SOURCE','OPIN'] or (kind[b]=='SINK' and b!=goal):continue
                if kind[b]=='IPIN' and not any(c==goal for c,_ in adjacency[b]):continue
                if len(occupancy[b])>=capacity[b]:continue
                previous[b]=(a,s);queue.append(b)
        record=dict(sink=goal,pin=pin,visited=len(previous),found=found);attempts.append(record)
        if not found:failed=True;break
        branch=[];n=goal
        while previous[n] is not None:
            a,s=previous[n];branch.append((a,n,s));n=a
        branch.reverse();edges+=branch;nodes.update(b for _,b,_ in branch);record['new_edges']=len(branch)
    result=dict(status='displaced_net_rebuild_failed' if failed else 'two_net_capacity_and_connectivity_candidate_ready',target=target,displaced=displaced,attempts=attempts,scope='One posterior two-net diagnostic; not frozen cohort replacement or general method evidence.',research_complete=False)
    if not failed:
        donor['edges']=edges
        unchanged=[n for n in original if n not in [target,displaced]]
        assert all(trees[n]==original[n] for n in unchanged)
        occupancy=collections.defaultdict(set)
        for n,t in trees.items():
            for node in {t['source']}|{v for edge in t['edges'] for v in edge[:2]}:occupancy[node].add(n)
        assert all(len(v)<=capacity[n] for n,v in occupancy.items())
        with (D/'trees.csv').open('x',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['net_id','source','parent','child','switch_id'])
            for n,t in trees.items():
                for a,b,s in t['edges']:writer.writerow([n,t['source'],a,b,s])
        convert(C/'circuit.route',D/'connections.csv',0,65535)
        write_route(C/'circuit.route',C/'rr_graph.xml',D/'connections.csv',D/'trees.csv',D/'candidate.route')
        result.update(unchanged_nets=len(unchanged),global_overused_resources=0,candidate_sha256=sha(D/'candidate.route'))
        (D/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        command=[sys.executable,str(T/'validate_vpr_route_device.py'),'--vpr',str(vpr),'--device','DieRouteCapacity20x16','--arch',str(C/'architecture.xml'),'--circuit',str(C/'circuit.blif'),'--net',str(C/'circuit.net'),'--place',str(C/'circuit.place'),'--route',str(D/'candidate.route'),'--rr-graph',str(C/'rr_graph.xml'),'--channel-width','80','--work-dir',str(D/'native_validation')]
        result['native_command']=command
        with (D/'native_validation.log').open('x') as log:run=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT)
        result['native_returncode']=run.returncode
        result['status']='native_validation_terminal'
    result['wall_ns']=time.monotonic_ns()-begin
    (D/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
