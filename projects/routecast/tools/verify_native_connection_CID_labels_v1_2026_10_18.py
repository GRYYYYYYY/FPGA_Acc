"""Independent raw event lexer and frozen pin-map replay of all693432CID labels."""
import sys,json,array,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';root=E/'mmc_native_connection_CID_binding_v1_2026-10-18';rp=root/'verification.json';r=json.loads(rp.read_text());queryp=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';frozen={}
 for line in queryp.read_text().splitlines():
  t=line.split()
  if t[0]=='Q':cid,net,pin,source,sink=map(int,t[1:]);frozen[net,pin]=cid
 assert len(frozen)==115572;spec=json.loads((E/'mmc_native_owner_cascade_trace_spec_v1_2026-10-18.json').read_text());bindings={**r['bindings'],str(rp):sha(rp),str(Path(__file__)):sha(__file__)};results=[]
 with Cache().installed():
  assert all(sha(p)==h for p,h in bindings.items())
  for row in r['rows']:
   case,arm=row['case'],row['arm'];ep=json.loads((E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json').read_text());queries={q['connection_id']:q for q in ep['connections']};bindingp=Path(row['binding_file']);assert sha(bindingp)==row['binding_sha256'];mapped={}
   for line in bindingp.read_text().splitlines():
    b=json.loads(line);cid=b['connection_id'];key=(b['native_NET'],b['native_sink_index']);assert frozen[key]==cid and cid not in mapped and all(b[k]==queries[cid][k] for k in ['source','sink']);mapped[cid]=key
   assert set(mapped)==set(queries)==set(range(115572));trace=E/f'mmc_native_connection_cascade_trace_v1_2026-10-18/{case}/{arm}/connection_trace.tsv';native={};terminals={};reach={};pending=None;attempts=0;success=collections.Counter();failed=collections.Counter();periter=collections.Counter();stats={};ended=False
   with trace.open() as stream:
    assert stream.readline()=='CONNECTION_TRACE 1\n'
    for line in stream:
     t=line.split();tag=t[0];assert not ended
     if tag=='N':net=int(t[1]);assert net not in native;native[net]=dict(name=bytes.fromhex(t[4]).decode('utf8','surrogateescape'),ignored=bool(int(t[2])),pins=int(t[3]))
     elif tag=='P':net,pin,rr,flag=map(int,t[1:]);key=(net,pin);assert key not in terminals;terminals[key]=rr;reach[key]=bool(flag)
     elif tag=='I':assert pending is None
     elif tag=='A':a=tuple(map(int,t[1:]));serial,it,net,pin,source,sink=a;assert pending is None and serial==attempts+1 and terminals[net,0]==source and terminals[net,pin]==sink;attempts=serial;pending=a
     elif tag in ['C','F']:
      serial,it,net,pin=map(int,t[1:]);assert pending is not None and pending[:4]==(serial,it,net,pin);pending=None
      if tag=='C':success[net,pin]+=1;periter[it]+=1
      else:failed[net,pin]+=1
     elif tag=='S':it,logged,native_count=map(int,t[1:]);assert it not in stats and logged==native_count==periter[it];stats[it]=logged
     elif tag=='END':ok,declared,good,bad=map(int,t[1:]);assert ok==1 and pending is None and declared==attempts==good+bad and good==sum(success.values()) and bad==sum(failed.values());ended=True
     else:raise AssertionError('unexpected trace record')
   assert ended and sum(stats.values())==sum(success.values());nonignored={(net,pin) for net,m in native.items() if not m['ignored'] for pin in range(1,m['pins'])};assert nonignored==set(frozen)
   for cid,key in mapped.items():
    q=queries[cid];assert native[key[0]]['name']==ep['net_names'][str(q['net_id'])] and terminals[key[0],0]==q['source'] and terminals[key]==q['sink']
   # Separate input lexer: printed seeded pin indices, no use of exported reach labels.
   job=next(j for j in spec['jobs'] if j['case']==case and bool(j['preserve_partial_first_iteration'])==(arm=='on'));seed=Path(job['seed']);seeded={};net=None
   with seed.open() as stream:
    for line in stream:
     words=line.split()
     if words and words[0]=='Net':net=int(words[1]);assert line.strip().startswith('Net '+str(net)+' ('+native[net]['name']+')')
     elif words and words[0]=='Node:' and words[2]=='SINK' and 'Net_pin_index:' in words:
      index=int(words[words.index('Net_pin_index:')+1])
      if index>0:assert (net,index) not in seeded;seeded[net,index]=int(words[1])
   assert seeded=={key:terminals[key] for key in terminals if reach[key]};vectors={}
   for name,desc in row['vectors'].items():
    p=Path(desc['path']);assert sha(p)==desc['sha256'] and desc['byteorder']==sys.byteorder;data=array.array(desc['typecode']);data.frombytes(p.read_bytes());assert len(data)==115572 and data.itemsize==desc['itemsize'];vectors[name]=data;bindings[str(p)]=sha(p)
   for cid,key in mapped.items():
    n=success[key];assert vectors['successful_sink_operations'][cid]==n and vectors['failed_sink_attempts'][cid]==failed[key] and vectors['initial_seed_reached'][cid]==int(key in seeded) and vectors['observed_explicit_reroute'][cid]==int((key in seeded and n>0) or n>1)
   extra_success=sum(n for key,n in success.items() if key not in frozen);assert extra_success==0;assert sum(success.values())==row['successful_sink_operations'];distinct=sum(n>0 for key,n in success.items() if key in frozen);rerouted=sum(((key in seeded and n>0) or n>1) for key,n in success.items() if key in frozen);assert distinct==row['distinct_routed_CIDs'] and rerouted==row['distinct_explicit_rerouted_CIDs'];results.append(dict(case=case,arm=arm,complete_CIDs=115572,explicit_sink_route_successes=sum(success.values()),distinct_CIDs_with_explicit_success=distinct,distinct_explicit_rerouted_CIDs=rerouted,initial_seed_CIDs=len(set(seeded)&set(frozen)),zero_success_CIDs=115572-distinct,unmapped_success_operations=0));bindings[str(trace)]=sha(trace);bindings[str(bindingp)]=sha(bindingp);print('INDEPENDENT CID EVENTS PASS',case,arm,flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  assert len(results)==6
  with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all693432CID_labels_and_seed_relative_explicit_reroutes_independently_verified',bindings=bindings,rows=results,scope='Actual successful native sink-routing calls and their repetitions relative to same imported seed, complete manifest CID domain including zero events. No implicit shared-trunk changes to other pins, per-CID heap/time, causal quality/net-time benefit, failure classification, strict unseen-family or hardware certification.'),f,indent=2)
 print('ALL6INDEPENDENT CID LABEL AUDITS PASS',flush=True)
if __name__=='__main__':main()
