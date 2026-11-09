"""Input-only combinational constant/global policy; never infer FF outputs constant."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_comb_constant_endpoints_v1_2026-10-09';D.mkdir(exist_ok=False)
source=E/'full_ram_native_slices_v1_2026-10-09/design.blif'
B=E/'full_ram_prospective_endpoints_v1_2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((B/'receipt.json').read_text())
for p,h in {**receipt['bindings'],**receipt['files']}.items():assert sha(Path(p))==h
blocks=[];current=None;models=0
for line in source.read_text().splitlines():
    words=line.split()
    if not words or words[0].startswith('#'):continue
    if words[0]=='.model':models+=1
    if models!=1:continue
    if words[0]=='.names':current=dict(args=words[1:-1],out=words[-1],rows=[]);blocks.append(current)
    elif words[0].startswith('.'):current=None
    elif current is not None:current['rows'].append(words)
known={};changed=True
while changed:
    changed=False
    for b in blocks:
        if b['out'] in known or not all(x in known for x in b['args']):continue
        vector=''.join(str(known[x]) for x in b['args'])
        if not b['args']:
            assert len(b['rows'])<=1
            value=int(b['rows'][0][0]) if b['rows'] else 0
        else:
            assert all(len(row)==2 and row[1]=='1' for row in b['rows'])
            value=int(any(all(p=='-' or p==v for p,v in zip(row[0],vector)) for row in b['rows']))
        known[b['out']]=value;changed=True
assert 'b2951' not in known
bindings={str(p):sha(p) for p in [Path(__file__),source,B/'receipt.json',*[B/f'cw{w}/endpoints.json' for w in (128,192,256)]]}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='exclude_root_clocks and input-proven combinational constant globals only; sequential initial transitions preserved',scope='Input-only extraction policy. No target route, occupancy or target QoR reads. Development-family candidate.'),indent=2)+'\n')
results=[]
for width in (128,192,256):
    ep=json.loads((B/f'cw{width}/endpoints.json').read_text())
    names={int(k):v for k,v in ep['net_names'].items()}
    excluded={nid:known[name] for nid,name in names.items() if name in known}
    old=ep['connections'];removed=[c for c in old if c['net_id'] in excluded]
    keep=[c for c in old if c['net_id'] not in excluded]
    assert len(removed)==264 and len(keep)==16819
    assert {names[n] for n in excluded}=={'iBus_cmd_payload_address[0]','dBus_cmd_payload_last'}
    ep['connections']=keep
    ep['comb_constant_global_policy']=dict(excluded_nets=[dict(net_id=n,name=names[n],value=v,sink_connections=sum(c['net_id']==n for c in removed)) for n,v in excluded.items()],preserve_original_connection_ids=True,source_blif_sha256=sha(source))
    (D/f'cw{width}.json').write_text(json.dumps(ep,indent=2)+'\n')
    results.append(dict(width=width,connections=len(keep),excluded_connections=len(removed)))
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,files={str(p):sha(p) for p in D.iterdir() if p.is_file()},admitted_as_unseen_family=False),indent=2)+'\n')
print(results)
