"""Full setup recurrence with domain tags and float32 operations; constants unsupported explicitly."""
import csv,struct,math
from collections import defaultdict,deque
from load_native_clock_constraints_v1 import load,resolve

def f32(v):return struct.unpack('<f',struct.pack('<f',float(v)))[0]
def timevalue(v):
 if not v['defined']:raise ValueError('undefined setup constraint on active analyzed path')
 return struct.unpack('>f',bytes.fromhex(v['bits']))[0]
def plus(a,b):return f32(a+b)
def minus(a,b):return f32(a-b)
class SetupReference:
 def __init__(self,folder):
  self.nodes={int(r['node']):int(r['type']) for r in csv.DictReader((folder/'timing_nodes.tsv').open(),delimiter='\t')};self.constraints=load(folder/'clock_constraints.tsv');self.edges=[];self.ins=defaultdict(list);self.outs=defaultdict(list);degree=dict.fromkeys(self.nodes,0)
  if self.constraints['constants']:raise ValueError('constant-generator propagation not implemented; no silent zero substitute')
  for r in csv.DictReader((folder/'timing_edges.tsv').open(),delimiter='\t'):
   if int(r['disabled']):continue
   edge=(int(r['edge']),int(r['source']),int(r['sink']),int(r['type']),f32(r['value_max_or_setup_s']));self.edges.append(edge);self.ins[edge[2]].append(edge);self.outs[edge[1]].append(edge);degree[edge[2]]+=1
  queue=deque(n for n in self.nodes if degree[n]==0);self.order=[]
  while queue:
   n=queue.popleft();self.order.append(n)
   for e in self.outs[n]:
    degree[e[2]]-=1
    if degree[e[2]]==0:queue.append(e[2])
  if len(self.order)!=len(self.nodes):raise ValueError('cyclic enabled timing graph')
 def analyze(self):
  d=self.constraints;A={n:{} for n in self.nodes};CL={n:{} for n in self.nodes};CC={n:{} for n in self.nodes};R={n:{} for n in self.nodes};clocknodes={v['source']:k for k,v in d['domains'].items() if v['source']>=0}
  def latency(mode,domain):return timevalue(d['latencies'].get((mode,domain),dict(defined=True,bits='00000000')))
  def uncertainty(src,sink):return timevalue(d['uncertainties'].get(('SETUP',src,sink),dict(defined=True,bits='00000000')))
  def merge(target,key,value,maximum=True):
   if key not in target or (value>target[key] if maximum else value<target[key]):target[key]=value
  inputs=defaultdict(list);outputs=defaultdict(list)
  for (kind,delay,node,domain),val in d['io_constraints'].items():
   if delay=='MAX':(inputs if kind=='I' else outputs)[node].append((domain,timevalue(val)))
  for n in self.order:
   typ=self.nodes[n]
   if not self.ins[n] and typ==0:
    if n in clocknodes:
     cap=clocknodes[n];CL[n][cap]=latency('LATE',cap)
     for src in d['domains']:
      c=resolve(d,src,cap)
      if c['analyze']:CC[n][src,cap]=plus(latency('EARLY',cap),timevalue(c['setup']))
    elif inputs[n]:
     if len(inputs[n])!=1:raise ValueError('multiple IO domains on one source not yet admitted')
     dom,delay=inputs[n][0];A[n][dom]=plus(latency('LATE',dom),delay)
   for e in self.ins[n]:
    eid,u,_,kind,w=e;ut=self.nodes[u];launch=ut==4 and typ==0;capture=ut==4 and typ==1
    if typ!=0:
     if not capture:
      for key,v in CL[u].items():merge(CL[n],key,plus(v,w))
     if typ!=1:
      for key,v in CC[u].items():merge(CC[n],key,plus(v,w))
    if launch:
     for key,v in CL[u].items():merge(A[n],key,plus(v,w))
    if ut!=4:
     if w<0:raise ValueError('negative data edge')
     for key,v in A[u].items():merge(A[n],key,plus(v,w))
   if typ==1:
    captures=[e for e in self.ins[n] if self.nodes[e[1]]==4]
    if len(captures)>1:raise ValueError('multiple clock capture arcs')
    if captures:
     e=captures[0];u=e[1];tsu=e[4]
     for (src,cap),clk in CC[u].items():
      c=resolve(d,src,cap,n)
      if src in A[n] and c['analyze']:
       base=resolve(d,src,cap);offset=minus(timevalue(c['setup']),timevalue(base['setup']));req=plus(plus(plus(clk,offset),-tsu),-uncertainty(src,cap));merge(R[n],(src,cap),req,False)
    elif outputs[n]:
     if len(outputs[n])!=1:raise ValueError('multiple IO domains on one sink not yet admitted')
     cap,delay=outputs[n][0]
     for src in A[n]:
      c=resolve(d,src,cap,n)
      if c['analyze']:req=plus(plus(plus(timevalue(c['setup']),latency('EARLY',cap)),-delay),-uncertainty(src,cap));merge(R[n],(src,cap),req,False)
  for n in reversed(self.order):
   if self.nodes[n]==4:continue
   for e in self.outs[n]:
    _,_,sink,_,w=e
    for pair,req in R[sink].items():
     if pair[0] in A[n]:merge(R[n],pair,minus(req,w),False)
  slacks={n:{pair:minus(req,A[n][pair[0]]) for pair,req in R[n].items() if pair[0] in A[n]} for n in self.nodes};maxreq={};worst={}
  for n in self.nodes:
   if self.nodes[n]!=1:continue
   for pair,v in R[n].items():merge(maxreq,pair,v)
   for pair,v in slacks[n].items():merge(worst,pair,v,False)
  crit={}
  for n in self.nodes:
   values=[]
   for pair,slack in slacks[n].items():
    req=maxreq[pair]
    if worst[pair]<0:shift=-worst[pair];slack=plus(slack,shift);req=plus(req,shift)
    if req>0:v=f32(1.0-f32(slack/req))
    elif req==0 and slack==0:v=1.0
    else:raise ValueError('invalid relaxed criticality denominator')
    values.append(max(0.0,min(1.0,v)))
   crit[n]=max(values,default=0.0)
  return dict(arrivals=A,required=R,slacks=slacks,criticality=crit,max_required=maxreq,worst_slack=worst)
