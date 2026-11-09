"""Fixed CHANNEL max(occupancy-capacity,0), factor1, binary32 native input.
No native labels are consumed. Native all-node readback remains mandatory.
"""
import argparse,json,struct
from pathlib import Path
from pre_route_endpoints import sha

def encode(resources,ledger,graph_sha,nodes):
    if len(graph_sha)!=64 or any(c not in '0123456789abcdef' for c in graph_sha):raise ValueError('graph digest')
    if type(nodes) is not int or nodes<1:raise ValueError('node count')
    if any(type(n) is not int or not 0<=n<nodes or type(v) is not int or v<0 for n,v in ledger.items()):raise ValueError('ledger domain')
    entries=[];seen=set()
    for row in resources:
        n,cap=row['id'],row['capacity']
        if type(n) is not int or not 0<=n<nodes or n in seen or type(cap) is not int or cap<=0:raise ValueError('CHANNEL domain')
        seen.add(n);excess=max(0,ledger.get(n,0)-cap)
        if excess>2**24:raise ValueError('excess integer not guaranteed exact binary32')
        if excess:
            bits=struct.unpack('<I',struct.pack('<f',excess))[0];entries.append((n,bits))
    entries.sort()
    return f'RCRISK1 {graph_sha} {nodes} {len(entries)}\n'+''.join(f'{n} {bits}\n' for n,bits in entries)

def export(frame_path,frame_proof,domain_proof,output):
    frame_path,frame_proof,domain_proof,output=map(lambda p:Path(p).resolve(),(frame_path,frame_proof,domain_proof,output))
    proof=json.loads(frame_proof.read_text());domain=json.loads(domain_proof.read_text());bindings={}
    for d in (proof,domain):
        for p,h in d['bindings'].items():
            if p in bindings and bindings[p]!=h:raise ValueError('evidence conflict')
            if sha(p)!=h:raise ValueError('evidence drift')
            bindings[p]=h
    if proof.get('all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass') is not True:raise ValueError('complete forecast audit required')
    if proof['bindings'].get(str(frame_path))!=sha(frame_path):raise ValueError('uncertified frame')
    f=json.loads(frame_path.read_text())
    if f['graph_sha256']!=domain['graph_sha256'] or f['completed_connections']!=f['required_connections']:raise ValueError('frame graph/coverage')
    resources=[json.loads(line) for line in (domain_proof.parent/'resources.jsonl').read_text().splitlines()]
    ledger={int(n):v for n,v in f['ledger'].items()};risk=encode(resources,ledger,domain['graph_sha256'],domain['graph_nodes'])
    output.mkdir(exist_ok=False)
    for name,text in [('forecast.risk',risk),('zero.risk',encode(resources,{},domain['graph_sha256'],domain['graph_nodes']))]:(output/name).write_text(text)
    for p in [frame_path,frame_proof,domain_proof,Path(__file__).resolve(),output/'forecast.risk',output/'zero.risk']:bindings[str(p)]=sha(p)
    result=dict(status='FIXED_EXCESS_AND_ZERO_PRELOAD_INPUTS_EXPORTED_NATIVE_READBACK_PENDING',bindings=bindings,graph_sha256=domain['graph_sha256'],nodes=domain['graph_nodes'],positive_entries=int(risk.splitlines()[0].split()[3]),policy='CHANNEL only; max(uniqueNEToccupancy-capacity,0); factor1; native initial acc_cost = binary32(1+binary32(excess)); no history/criticality/net-order/seed changes',native_readback_pending=True)
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n');return result['positive_entries']
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('frame','frame_proof','domain_proof','output'):p.add_argument(name)
    a=p.parse_args();print(export(a.frame,a.frame_proof,a.domain_proof,a.output))
