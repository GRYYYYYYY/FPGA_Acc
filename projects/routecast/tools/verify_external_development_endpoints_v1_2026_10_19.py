"""Compare complete XML endpoint multiplicities against native route-free terminals."""
import json,shlex,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 root=R/'experiments/prospective_external_family_development_endpoints_v1_2026-10-19';rp=root/'receipt.json';r=read(rp);assert not r['new_route_labels'];assert all(sha(p)==h for p,h in r['bindings'].items());ep=root/'endpoints.json';e=read(ep);native=R/'experiments/prospective_external_family_preroute_context_v2_2026-10-19';nr=read(native/'receipt.json');assert nr['exit_code']==0 and all(sha(p)==h for p,h in nr['bindings'].items());np=native/'native_terminals.txt';nets={};header=None
 for line in np.read_text().split('\n'):
  if not line:continue
  t=shlex.split(line)
  if t[0]=='H':assert header is None;header=tuple(map(int,t[1:]));continue
  assert t[0]=='N' and len(t)>=7;name=t[2];assert name not in nets;flag=t[5];assert flag in ('\x00','\x01');terms=list(map(int,t[7:]));assert len(terms)==int(t[6]) and len(terms)>=1;nets[name]=dict(native_net_id=int(t[1]),ignored=bool(int(t[3])),global_net=bool(int(t[4])),clock=ord(flag),terminals=terms)
 assert header==(119878,1048247,5920) and len(nets)==header[2];names={int(n):name for n,name in e['net_names'].items()};assert set(names.values())==set(nets);excluded={z['net']:z for z in e['excluded_nets']};assert set(excluded)=={'clk'} and excluded['clk']['reason']=='explicit exclude_root_clocks policy';assert nets['clk']['clock']==1 and len(nets['clk']['terminals'])-1==excluded['clk']['sink_pins']==354
 expected=Counter((name,entry['terminals'][0],sink) for name,entry in nets.items() if name not in excluded for sink in entry['terminals'][1:]);observed=Counter((names[c['net_id']],c['source'],c['sink']) for c in e['connections']);assert observed==expected and sum(observed.values())==15616;assert [c['connection_id'] for c in e['connections']]==list(range(15616));graph=Path(e['inputs']['graph']['path']);assert sha(graph)==e['graph_sha256'];stack=[];nodecount=0;edgecount=0;kinds={}
 for event,x in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(x);continue
  parent=stack[-2] if len(stack)>1 else None
  if x.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   nid=int(x.get('id'));assert nid==nodecount;nodecount+=1
   if x.get('type') in ['SOURCE','SINK']:kinds[nid]=x.get('type')
   parent.remove(x);x.clear()
  elif x.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   assert 0<=int(x.get('src_node'))<119878 and 0<=int(x.get('sink_node'))<119878;edgecount+=1;parent.remove(x);x.clear()
  stack.pop()
 assert (nodecount,edgecount)==header[:2]
 for name,entry in nets.items():assert kinds[entry['terminals'][0]]=='SOURCE' and all(kinds[n]=='SINK' for n in entry['terminals'][1:])
 assert 'PREROUTE_CONTEXT_EXPORTED_NO_ROUTE_TREES' in (native/'export.log').read_text();assert not list(native.glob('*.route'));normal=root/'normalized_native_terminals.json';normal.write_text(json.dumps(nets,indent=2)+'\n');paths=[rp,ep,np,native/'receipt.json',native/'protocol.json',native/'export.log',graph,normal,Path(__file__).resolve()]
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL15616_CONNECTIONS_AND5920_NET_NAMES_MATCH_NATIVE_TERMINAL_MULTISETS',connections=15616,nets=5920,excluded_clock_connections=354,graph_nodes=nodecount,graph_edges=edgecount,graph_sha256=e['graph_sha256'],bindings={str(p):sha(p) for p in paths},clock_serialization='Native uint8 clock field streamed as raw NUL/SOH; decoded only at fixed field after exact byte-value check. Original export unchanged; normalized JSON records numeric0/1.',scope='Independent XML/packed extraction versus actual native loaded endpoint lists, full multiplicity and original graph node/edge count/type checks. Native route structures initialized with all route trees absent. No path feasibility/budgets/final route labels, full graph edge-attribute audit, quality gain or strict unseen-family admission.'),f,indent=2)
 print('INDEPENDENT_NATIVE_ENDPOINTS_PASS',15616,5920,'clock_excluded',354)
if __name__=='__main__':main()
