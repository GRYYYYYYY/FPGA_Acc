"""Strict explicit native sink-operation trace replay; CID mapping is separate."""
from collections import Counter

class TraceError(ValueError):pass

def replay(path):
    nets={};pins={};successes=Counter();failures=Counter();iterations=[];current=None;pending=None;sequence=0;ended=False;total_success=total_failed=0;iteration_success=iteration_failed=0;stats_seen=False;work_pushes=Counter();work_pops=Counter();iteration_pushes=iteration_pops=0;before_work=None
    def require(ok,message):
        if not ok:raise TraceError(message)
    with open(path) as stream:
        require(stream.readline()=='CONNECTION_TRACE 2\n','header')
        for number,line in enumerate(stream,2):
            require(not ended,'content after END');parts=line.split();require(bool(parts),'empty record');tag=parts[0]
            try:
                if tag=='N':
                    require(current is None and len(parts)==5,'NET metadata phase/schema');net,ignored,count=map(int,parts[1:4]);require(net>=0 and net not in nets and ignored in [0,1] and count>=1,'NET identity');name=bytes.fromhex(parts[4]).decode('utf8','surrogateescape');nets[net]=dict(name=name,ignored=bool(ignored),pins=count)
                elif tag=='P':
                    require(current is None and len(parts)==5,'pin metadata phase/schema');net,pin,rr,reached=map(int,parts[1:]);key=(net,pin);require(net in nets and 0<=pin<nets[net]['pins'] and key not in pins and rr>=0 and reached in [0,1],'pin identity');require(pin>0 or reached==0,'driver reach flag');pins[key]=dict(rr=rr,initially_reached=bool(reached))
                elif tag=='I':
                    require(len(parts)==2 and pending is None,'iteration schema/pending');iteration=int(parts[1]);require(iteration==(1 if current is None else current+1),'iteration sequence')
                    if current is None:
                        require(bool(nets),'empty native domain')
                        for net,meta in nets.items():
                            if not meta['ignored']:require(all((net,p) in pins for p in range(meta['pins'])),'incomplete native terminal domain')
                    else:require(stats_seen,'missing previous iteration stats')
                    current=iteration;iteration_success=iteration_failed=0;iteration_pushes=iteration_pops=0;stats_seen=False
                elif tag=='A':
                    require(len(parts)==9 and current is not None and not stats_seen and pending is None,'attempt phase/schema');seq,it,net,pin,source,sink,before_pushes,before_pops=map(int,parts[1:]);require(before_pushes>=0 and before_pops>=0,'negative heap baseline');before_work=(before_pushes,before_pops);require(seq==sequence+1 and it==current and pin>0 and (net,pin) in pins and (net,0) in pins,'attempt identity');require(source==pins[net,0]['rr'] and sink==pins[net,pin]['rr'],'terminal mismatch');sequence=seq;pending=(seq,it,net,pin)
                elif tag in ['C','F']:
                    require(len(parts)==7 and pending is not None,'unmatched result');result=tuple(map(int,parts[1:5]));require(result==pending,'result identity');key=result[2:];after_pushes,after_pops=map(int,parts[5:]);require(after_pushes>=before_work[0] and after_pops>=before_work[1],'heap counter decreased');pushes=after_pushes-before_work[0];pops=after_pops-before_work[1];work_pushes[key]+=pushes;work_pops[key]+=pops;iteration_pushes+=pushes;iteration_pops+=pops;pending=None;before_work=None
                    if tag=='C':successes[key]+=1;total_success+=1;iteration_success+=1
                    else:failures[key]+=1;total_failed+=1;iteration_failed+=1
                elif tag=='S':
                    require(len(parts)==8 and current is not None and not stats_seen and pending is None,'stats phase/schema');it,observed,native,attributed_pushes,attributed_pops,native_pushes,native_pops=map(int,parts[1:]);require(attributed_pushes==iteration_pushes<=native_pushes and attributed_pops==iteration_pops<=native_pops,'heap attribution/native mismatch');require(it==current and observed==native==iteration_success,'native counter mismatch');stats_seen=True;iterations.append(dict(iteration=it,successful=observed,failed_attempts=iteration_failed,native_counter_checked=True,attributed_heap_pushes=attributed_pushes,attributed_heap_pops=attributed_pops,native_heap_pushes=native_pushes,native_heap_pops=native_pops,outside_sink_heap_pushes=native_pushes-attributed_pushes,outside_sink_heap_pops=native_pops-attributed_pops))
                elif tag=='END':
                    require(len(parts)==7 and current is not None and pending is None,'END schema/pending');success,attempts,completed,failed,all_pushes,all_pops=map(int,parts[1:]);require(all_pushes==sum(work_pushes.values()) and all_pops==sum(work_pops.values()),'END heap totals');require(success in [0,1] and attempts==sequence==total_success+total_failed and completed==total_success and failed==total_failed,'END totals');require(not success or stats_seen,'successful END lacks native stats');ended=True
                    if not stats_seen:iterations.append(dict(iteration=current,successful=iteration_success,failed_attempts=iteration_failed,native_counter_checked=False))
                else:raise TraceError('unknown record '+tag)
            except (ValueError,KeyError,IndexError) as exc:
                if isinstance(exc,TraceError):raise TraceError(f'line{number}: {exc}') from exc
                raise TraceError(f'line{number}: malformed {tag}') from exc
    require(ended,'truncated before END')
    return dict(heap_pushes_by_native_pin=work_pushes,heap_pops_by_native_pin=work_pops,attributed_heap_pushes=sum(work_pushes.values()),attributed_heap_pops=sum(work_pops.values()),nets=nets,pins=pins,successful_operations=successes,failed_attempts=failures,iterations=iterations,router_success=bool(success),attempts=sequence,successful=total_success,failed=total_failed,distinct_successful_native_pins=len(successes),distinct_initially_reached_successful_pins=sum(pins[k]['initially_reached'] for k in successes),distinct_repeated_native_pins=sum(pins[k]['initially_reached'] or n>1 for k,n in successes.items()),scope='Explicit sink-routing attempts/results only; Measured heap snapshots per explicit call, not elapsed-time or implicit shared-trunk work. Manifest CID binding and legacy event projection must be verified separately.')
