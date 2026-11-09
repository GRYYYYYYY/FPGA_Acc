"""Fresh bit/atom/physical pin audit and complete current CID admission."""
import json,math,struct
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def f32(t):return struct.unpack('<f',struct.pack('<f',float(t)))[0]
def word(x):return int.from_bytes(struct.pack('<f',x),'little')
def decode(text,bits):
 b=int(bits,16);x=struct.unpack('<f',b.to_bytes(4,'little'))[0]
 if math.isnan(x):assert math.isnan(float(text))
 else:assert word(float(text))==b
 return x,b

def main():
 root=R/'experiments/prospective_external_family_current_initial_timing_v1_2026-10-19';rp=root/'receipt.json';r=read(rp);pp=root/'protocol.json';p=read(pp);assert r['capture_passed'] and r['exit_code']==0
 for d in [r,p]:
  for f,h in d['bindings'].items():assert sha(f)==h
 end=R/'experiments/prospective_external_family_development_endpoints_v1_2026-10-19';er=read(end/'receipt.json');assert all(sha(f)==h for f,h in er['bindings'].items());ep=end/'endpoints.json';e=read(ep);mapping=read(end/'mapping_report.json');assert e['source_sha256']==sha(R/'tools/pre_route_endpoints.py');assert p['command'][p['command'].index('--read_rr_graph')+1]==e['inputs']['graph']['path'];work=root/'work';assert sha(work/'design.net')==e['inputs']['net']['sha256'] and sha(work/'design.place')==e['inputs']['place']['sha256'];sinkdetails=[d for d in mapping['pin_details'] if d['role']=='SINK'];xml={(d['net'],d['block'],d['physical_pin_ptc']):d for d in sinkdetails};assert len(xml)==len(sinkdetails)==15970;manifest={};byphysical={};netids={};sources={d['net']:d['rr_node'] for d in mapping['pin_details'] if d['role']=='SOURCE'}
 for i,line in enumerate((work/'pin_manifest.tsv').read_text().splitlines()):
  t=line.split('\t')
  if i==0:assert t==['H','1'];continue
  assert len(t)==12 and t[0]=='P' and int(t[1])==i;seq,net,glob,local,bid=map(int,t[1:6]);name=t[11];key=(net,local);phys=(name,t[6],int(t[7]));assert key not in manifest and phys not in byphysical and phys in xml;d=xml[phys];assert (bid,int(t[8]),int(t[9]),int(t[10]))==(d['block_id'],d['class_id'],sources[name],d['rr_node']);assert name not in netids or netids[name]==net;netids[name]=net;row=dict(sequence=seq,native_net_id=net,global_pin=glob,local_sink_pin=local,block_id=bid,block_name=t[6],physical_pin_ptc=int(t[7]),class_id=int(t[8]),source_rr=int(t[9]),target_rr=int(t[10]),net_name=name);manifest[key]=row;byphysical[phys]=key
 assert len(manifest)==len(byphysical)==15970 and len(netids)==5920
 critical=[]
 for i,line in enumerate((work/'criticality.tsv').read_text().splitlines(),1):
  t=line.split('\t');assert len(t)==10 and t[0]=='C' and int(t[1])==i;value,maximum=f32(t[5]),f32(t[6]);assert math.isfinite(value) and 0<=value<=maximum<=1;critical.append(t)
 assert len(critical)==15970;atoms=[];rows={};atomcount=0;header=None
 for line in (work/'timing.tsv').read_text().splitlines():
  t=line.split('\t')
  if t[0]=='H':assert header is None and t[1]=='1' and t[4]=='0';header=t;continue
  assert header is not None
  if t[0]=='A':
   assert len(t)==10;seq,net,glob,local,atom=map(int,t[1:6]);slack,sbits=decode(t[6],t[7]);crit,cbits=decode(t[8],t[9]);atoms.append((seq,net,glob,local,atom,slack,crit,sbits,cbits));atomcount+=1;continue
  assert t[0]=='S' and len(t)==15;seq,net,glob,local,count=map(int,t[1:6]);assert seq==len(rows)+1 and len(atoms)==count;key=(net,local);assert key in manifest and key not in rows;manifestrow=manifest[key];assert (manifestrow['sequence'],manifestrow['global_pin'])==(seq,glob);c=critical[seq-1];assert list(map(int,c[1:5]))==[seq,net,glob,local];slack,sbits=decode(t[6],t[7]);raw,rbits=decode(t[8],t[9]);trans,tbits=decode(t[10],t[11]);assert word(float(c[5]))==tbits and t[12:14]==c[8:10] and all(x in ['0','1'] for x in t[12:15]);mn=math.inf;mx=0.0
  for a in atoms:
   assert a[:4]==(seq,net,glob,local)
   if a[5]<mn:mn=a[5]
   if mx<a[6]:mx=a[6]
  assert word(mn)==sbits and word(mx)==rbits;rows[key]=dict(manifestrow,criticality_float32_text=c[5],criticality_bits=t[11],maximum_text=c[6],exponent_text=c[7],slack_bits=t[7],raw_criticality_bits=t[9],atom_count=count,ignored=t[12]=='1',global_net=t[13]=='1',clock_net=t[14]=='1');atoms=[]
 assert not atoms and len(rows)==15970 and atomcount==24625;sinks=defaultdict(list)
 for d in sinkdetails:sinks[d['net']].append(d)
 counters=Counter();payload=[];names={int(n):name for n,name in e['net_names'].items()};keys=set()
 for q in e['connections']:
  name=names[q['net_id']];d=sinks[name][counters[name]];counters[name]+=1;assert d['rr_node']==q['sink'];key=byphysical[(name,d['block'],d['physical_pin_ptc'])];a=rows[key];assert not a['ignored'] and not a['clock_net'];assert (a['source_rr'],a['target_rr'])==(q['source'],q['sink']) and key not in keys;keys.add(key);val=f32(a['criticality_float32_text']);num,den=val.as_integer_ratio();payload.append(dict(a,connection_id=q['connection_id'],endpoint_net_id=q['net_id'],criticality_numerator=num,criticality_denominator=den))
 assert len(payload)==len(keys)==15616 and keys=={k for k,a in rows.items() if not a['ignored']};ignored=[a for a in rows.values() if a['ignored']];assert len(ignored)==354 and all(a['net_name']=='clk' and a['clock_net'] for a in ignored);assert not list(work.glob('*.route'));text=(work/'native.log').read_text();assert 'exit_before_first_getter_returns=1' in text and 'Successfully routed after' not in text;target=root/'initial_connection_criticalities.json';target.write_text(json.dumps(payload,indent=2)+'\n');paths=[rp,pp,ep,end/'mapping_report.json',end/'receipt.json',target,work/'criticality.tsv',work/'timing.tsv',work/'pin_manifest.tsv',work/'native.log',Path(__file__).resolve()];stats=Counter(a['criticality_float32_text'] for a in payload)
 with (root/'verification.json').open('x') as f:json.dump(dict(schema='ROUTECAST_EXTERNAL_CURRENT_INITIAL_TIMING_V1',status='ALL15616_CURRENT_CIDS_PHYSICAL_PIN_IDENTITIES_FLOAT_BITS_AND_ATOM_AGGREGATES_VERIFIED',all_sink_pins=15970,connections=15616,ignored_clock_pins=354,atom_rows=atomcount,current_float32_values_verified=True,current_XML_pin_and_endpoint_identities_verified=True,no_route_generated=True,after_endpoint=str(ep),criticality_histogram=dict(stats),bindings={str(p):sha(p) for p in paths},scope='Fresh same-process REAL native initialized criticality and per-atom metadata, independent min-slack/max-criticality reconstruction and exact current physical pin/CID join. No legacy value equality, copied design timings, additive budget claim, routed timing closure or strict family admission.'),f,indent=2)
 print('CURRENT_EXTERNAL_TIMING_FULL_AUDIT_PASS',15616,15970,atomcount,'criticality_values',len(stats))
if __name__=='__main__':main()
