"""Canonicalize a native output and reload with original VPR FULL/STA."""
import json,os,re,shutil,subprocess
from pathlib import Path
from audit_native_route import NODE
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2]
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
binary=ROOT/'build/native_verbose_sync_v2_2026-10-08/verbose_sync_vpr'
identity=ROOT/'build/native_ignored_identity_v1_2026-10-08/routecast_net_identity_vpr'
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
def run(cmd,work,log,environment):
    with log.open('w') as stream:return subprocess.run(cmd,cwd=work,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
def canonical_reload(p,source,destination,inventory):
    assert all(sha(path)==h for path,h in p['files'].items())
    width,decision=p['width'],p['decision'];src=Path(source);work=Path(destination)
    graph=Path(p['command'][p['command'].index('--read_rr_graph')+1])
    inventory.validate(graph,inventory.digest);nodes={nid:loc for nid,(kind,loc) in inventory.nodes.items()};work.mkdir()
    shutil.copyfile(src/'design.blif',work/'design.blif');shutil.copyfile(src/'design.net.post_routing',work/'design.net')
    place=src/('accepted.place' if decision=='A' else 'design.place')
    text=re.sub(r'Netlist_ID:\s*\S+','Netlist_ID: SHA256:'+sha(work/'design.net'),place.read_text(),count=1)
    (work/'design.place').write_text(text)
    cmd=p['command'].copy();cmd[0]=str(binary);cmd[cmd.index('--route')]='--analysis';cmd[cmd.index('--route_file')+1]='design.route'
    icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route_file')+1]='missing.route'
    table=work/'identity.jsonl'
    assert run(icmd,work,work/'identity.log',{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table),'ROUTECAST_IDENTITY_ONLY':'1'})==1 and table.exists()
    nets={row['name']:row for row in map(json.loads,table.read_text().splitlines())}
    sections={};head=[];record=None;pins=0
    for line in (src/'output.route').read_text().splitlines():
        m=re.match(r'^Net\s+(\d+)\s+\((.*?)\)',line)
        if m:
            record=nets[m[2]];nid=record['net_id'];assert nid not in sections
            sections[nid]=[re.sub(r'^Net\s+\d+',f'Net {nid}',line)];continue
        if record is None:head.append(line);continue
        m=NODE.match(line)
        if m and m[2]=='SINK':
            loc=nodes[int(m[1])];site=tuple(int(loc.get(k,'0')) for k in ('xlow','ylow','layer','ptc'))
            options=[pin for pin in record['pins'] if pin['index']>0 and tuple(pin[k] for k in ('x','y','layer','class'))==site]
            assert len(options)==1,'ambiguous canonical SINK identity'
            line=re.sub(r'Net_pin_index:\s*\d+',f"Net_pin_index: {options[0]['index']}",line);pins+=1
        sections[nid].append(line)
    head[0]='Placement_File: design.place Placement_ID: SHA256:'+sha(work/'design.place')
    lines=head[:]
    for nid in sorted(sections):lines.extend(sections[nid])
    (work/'design.route').write_text('\n'.join(lines)+'\n')
    inventory.validate(graph,inventory.digest)
    code=run(cmd,work,work/'reload.log',env);log=(work/'reload.log').read_text()
    cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)
    mis=re.search(r'Found (\d+) mismatches',log);fix=re.search(r'Fixed (\d+) routing traces',log)
    row=dict(width=width,decision=decision,command=cmd,exit_code=code,cpd_ns=float(cpd[1]) if cpd else None,expected_cpd_ns=p['cpd_ns'],mismatches=int(mis[1]) if mis else None,fixups=int(fix[1]) if fix else None,pins=pins,graph_sha256=sha(graph),files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
    assert row['exit_code']==0 and row['cpd_ns']==p['cpd_ns']
    assert 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log
    # Original counter gate is still reported, not rewritten as a successful zero count.
    row['original_zero_counter_gate_pass']=row['mismatches']==row['fixups']==0
    pattern=re.compile(r"Fixed up net '([^']*)' mapping mismatch at clustered block '(.*)' pin 'grid\[(\d+)\]\[(\d+)\]\.([^.]*)\.([^\[]*)\[(\d+)\] - layer (\d+)' \(was net '([^']*)'\)")
    from collections import Counter
    allowed=Counter()
    for record in nets.values():
        if record['ignored']:
            for pin in record['pins']:
                if pin['index']>0:allowed[record['name'],pin['block'],pin['x'],pin['y'],pin['layer'],pin['port'],pin['bit']]+=1
    observed=Counter()
    for m in pattern.finditer(log):
        routed,block,x,y,tile,port,bit,layer,old=m.groups()
        assert routed=='unmapped'
        observed[old,block,int(x),int(y),int(layer),port,int(bit)]+=1
    assert not observed-allowed
    assert sum(observed.values())==row['mismatches']==row['fixups']
    assert (work/'design.net').read_bytes()==(work/'design.net.post_routing').read_bytes()
    from audit_native_route import NET
    def sequences(path):
        result={};net=None
        for line in path.read_text().splitlines():
            m=NET.match(line)
            if m:net=m[2];assert net not in result;result[net]=[]
            n=NODE.match(line)
            if n:assert net is not None;result[net].append((int(n[1]),n[2],int(n[3])))
        return result
    assert sequences(src/p['command'][p['command'].index('--route_file')+1])==sequences(work/'design.route')
    from stream_native_route_audit import audit
    physical=audit(graph,work/'design.route');assert physical['overflow_units']==0
    row['native_ignored_only_mismatch_pins']=sum(observed.values())
    row['packed_netlist_byte_identical']=True
    row['all_NET_physical_node_type_switch_sequences_identical']=True
    row['canonical_original_XML_arc_branch_capacity_pass']=True
    row['semantic_consistency_gate_pass']=True
    row['scope']='Logging-only original VPR objects, original FULL/STA. Nonzero counters admitted only with independently captured ignored pin membership, exact final packed bytes, all physical sequences, original XML arc/branch/capacity and exact CPD invariants. Original zero-counter gate retained separately.'

    return row
