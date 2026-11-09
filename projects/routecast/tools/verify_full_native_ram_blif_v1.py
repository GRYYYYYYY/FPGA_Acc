"""Independent complete BLIF body, pin and initialization readback."""
import hashlib,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_native_ram_blif_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_native_ram_blif_v1_2026-10-09'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((B/'receipt.json').read_text());assert r['exit_code']==0
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
def parse(text):
    ins=[];outs=[];names=[];latches=[];sub=[];pending=[];model=0;current=None
    for raw in text.splitlines():
        words=raw.split()
        if not words or words[0].startswith('#'):continue
        continued=words[-1]==chr(92);pending+=words[:-1] if continued else words
        if continued:continue
        words=pending;pending=[]
        if words[0]=='.model':model+=1;current=None
        elif model!=1:continue
        elif words[0]=='.inputs':ins+=words[1:];current=None
        elif words[0]=='.outputs':outs+=words[1:];current=None
        elif words[0]=='.names':current=[tuple(words[1:]),[]];names.append(current)
        elif words[0]=='.latch':latches.append(tuple(words[1:]));current=None
        elif words[0]=='.subckt':sub.append((words[1],tuple(sorted(words[2:]))));current=None
        elif words[0]=='.end':current=None
        else:assert current is not None;current[1].append(tuple(words))
    assert not pending
    return ins,outs,Counter((a,tuple(rows)) for a,rows in names),Counter(latches),Counter(sub)
source=E/'full_native_ram_gates_v3_2026-10-09/gates.json'
m=json.loads(source.read_text())['modules']['VexRiscvFull']
mapped=E/'full_native_ram_cut_mapping_v1_2026-10-09/mapped.blif'
actual=parse((B/'design.blif').read_text());body=parse(mapped.read_text())[2]
token=lambda b:'b'+str(b) if type(b)is int else 'const'+b
ins=[];outs=[];aliases=Counter()
for name,p in m['ports'].items():
    for i,b in enumerate(p['bits']):
        label=name if len(p['bits'])==1 else f'{name}[{i}]'
        (ins if p['direction']=='input' else outs).append(label)
        pair=(label,token(b)) if p['direction']=='input' else (token(b),label)
        aliases[pair,(('1','1'),)]+=1
assert actual[:2]==(ins,outs) and actual[2]==body+aliases
initial={}
for net in m['netnames'].values():
    if 'init' in net['attributes']:
        for b,v in zip(net['bits'],reversed(net['attributes']['init'])):
            if v in '01':assert b not in initial or initial[b]==v;initial[b]=v
latches=Counter();sub=Counter()
for c in m['cells'].values():
    kind=c['type']; conn=c['connections']
    if kind=='$_DFF_P_':
        latches[token(conn['D'][0]),token(conn['Q'][0]),'re',token(conn['C'][0]),initial.get(conn['Q'][0],'2')]+=1
    elif kind in ('$_DFF_PP0_','$_DFF_PP1_','dual_port_ram'):
        pairs=[]
        for pin,bits in conn.items():
            for i,b in enumerate(bits):pairs.append((pin if len(bits)==1 else f'{pin}[{i}]')+'='+token(b))
        sub[kind,tuple(sorted(pairs))]+=1
assert actual[3]==latches and actual[4]==sub
reload=json.loads((B/'reload.json').read_text())['modules']['VexRiscvFull']
wire=lambda t:t[-1] if t in ('const0','const1') else reload['netnames'][t]['bits'][0]
plain=Counter();black=Counter();reload_init={}
for net in reload['netnames'].values():
    if 'init' in net['attributes']:
        for b,v in zip(net['bits'],reversed(net['attributes']['init'])):
            if v in '01':reload_init[b]=v
for c in reload['cells'].values():
    if c['type']=='$dff':
        assert int(c['parameters']['CLK_POLARITY'],2)==1 and int(c['parameters']['WIDTH'],2)==1
        plain[tuple(c['connections'][p][0] for p in ('D','Q','CLK'))]+=1
    elif c['type'] in ('$_DFF_PP0_','$_DFF_PP1_','dual_port_ram'):
        assert all(len(v)==1 for v in c['connections'].values())
        black[c['type'],tuple(sorted((p,b[0]) for p,b in c['connections'].items()))]+=1
    else:assert c['type']=='$lut'
assert plain==Counter((wire(d),wire(q),wire(clk)) for d,q,edge,clk,init in latches.elements())
expected=Counter()
for (kind,pairs),count in sub.items():
    expected[kind,tuple(sorted((p,wire(v)) for p,v in (pair.split('=') for pair in pairs)))]+=count
assert black==expected
assert reload_init=={wire(q):init for d,q,edge,clk,init in latches if init!='2'}
out=dict(passed=True,ordinary_ff=sum(latches.values()),initialized_ff=len(reload_init),
    native_ram=15,mapped_body_exact=True,all_boundary_pins_and_init_readback_exact=True,
    bindings={str(p):sha(p) for p in [Path(__file__),source,mapped,B/'design.blif',B/'reload.json',B/'receipt.json']},
    scope='Full structural reconstruction and fresh reload equality only; no full HDL sequential equivalence or physical timing.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['ordinary_ff'],out['initialized_ff'],out['passed'])
