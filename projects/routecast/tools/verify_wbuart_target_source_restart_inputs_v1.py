"""Check actual incoming trees and per-NET delay multisets against source."""
import json,re,hashlib
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_target_source_restart_reference_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 m=read(D/'manifest.json');assert read(D/'terminal.json')['all_pass'];bindings={str(p):sha(p) for p in [Path(__file__),D/'manifest.json',D/'terminal.json']};rows=[]
 for c in m['cases']:
  out=Path(c['output']);v=read(out/'verification.json');assert v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert all(sha(p)==h for p,h in v['bindings'].items());ep=read(c['endpoint']);names={name:int(n) for n,name in ep['net_names'].items()};wanted=defaultdict(set);net=None
  for line in Path(c['restart_seed']).read_text().splitlines():
   match=re.match(r'Net\s+\d+\s+\((.*?)\)',line)
   if match:net=names.get(match[1]);continue
   match=re.match(r'\s*Node:\s*(\d+)',line)
   if match and net is not None:wanted[net].add(int(match[1]))
  incoming={};active=False
  for line in (out/'owner_trace.tsv').read_text().splitlines():
   if line=='CP initial 0':active=True;continue
   if not active:continue
   if line=='CE':break
   words=line.split()
   if words[0]=='T':
    n,ignored,present,remaining,count=map(int,words[1:6]);nodes=set(map(int,words[6:]));assert count==len(nodes)
    if not ignored and present:assert remaining==0;incoming[n]=nodes
  assert dict(wanted)==incoming
  expected_NETs=int(re.search(r'retained=(\d+)',c['expected_load_marker'])[1]);assert len(incoming)==expected_NETs
  observed=defaultdict(list)
  for net,pin,value in re.findall(r'ROUTECAST_SOURCE_RESTART_DELAY net=(\d+) pin=(\d+) value=(\S+)',(out/'native.log').read_text()):observed[int(net)].append(float.fromhex(value))
  source=read(E/'wbuart_source_checkpoints_v1_2026-10-20'/f"w{c['width']:03d}/source/initial.json");expected=defaultdict(list)
  for q in source['records']:
   if q['net_id'] in incoming:expected[q['net_id']].append(q['answer']['delay']/source['scale'])
   else:
    import struct
    expected[q['net_id']].append(struct.unpack('f',struct.pack('f',1e-9))[0])
  assert observed.keys()==expected.keys();maxerror=0
  for n in expected:
   a,b=sorted(expected[n]),sorted(observed[n]);assert len(a)==len(b)
   for x,y in zip(a,b):
    if n not in incoming:assert x==y
    else:assert abs(x-y)<=1e-14
    maxerror=max(maxerror,abs(x-y))
  rows.append({'case':c['target_case'],'width':c['width'],'complete_incoming_trees':expected_NETs,'delay_values':2493,'max_absolute_delay_error_seconds':maxerror,'iterations':v['iterations'],'full_physical_canonical_trace_pass':True});bindings[str(out/'verification.json')]=sha(out/'verification.json')
 assert len(rows)==9
 (D/'independent_input_verification_v1.json').write_text(json.dumps({'status':'ALL9_TARGET_INITIAL_SEED_TREES_AND22437_DELAY_VALUES_VERIFIED','rows':rows,'bindings':bindings,'scope':'Initial owner-trace tree sets exactly target seed; retained per-NET delay multisets versus source exact RC within1e-14 seconds diagnostic tolerance; missing NET delay float32(1ns) exact. No retained per-pin mapping/bit-exact certificate or full native-state persistence/quality/gain claim.'},indent=2)+'\n');print('ALL9_TARGET_INITIAL_SEED_TREES_AND22437_DELAY_VALUES_VERIFIED')
if __name__=='__main__':main()
