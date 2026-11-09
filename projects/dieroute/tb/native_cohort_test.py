"""Whole-net closure, frozen outside occupancy, negotiation and budget reporting."""
import argparse,csv,json,shutil,struct,subprocess,tempfile,sys
from pathlib import Path
from native_csr_test import FINGERPRINT,table
from native_search_graph_test import container

def main():
    p=argparse.ArgumentParser();p.add_argument('--router',type=Path,required=True);p.add_argument('--quotient-builder',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--parallel-router',type=Path);a=p.parse_args()
    if a.output is None:scratch=tempfile.TemporaryDirectory();a.output=Path(scratch.name)/'cases'
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);base=out/'input';base.mkdir()
    for name in ('graph','search','footprint','mapping'):(base/name).mkdir()
    # Die 2 exists in the graph even though no task endpoint uses it.
    table(base/'graph/nodes.bin',[[n,n,0,n,0,5 if n==10 else 3 if n==1 else 2 if n in (4,6) else 1,1,0,0,0,0,0,0,0,0,0] for n in range(11)])
    table(base/'mapping/footprint_node_map.bin',[[n] for n in range(11)])
    tasks=[[0,0,0,5,0,0,0,0],[1,1,4,6,1,1,0,0],[2,0,0,7,0,0,0,0],[3,2,8,9,0,0,0,0]]
    table(base/'footprint/tasks.bin',tasks);table(base/'footprint/nets.bin',[[0]*16 for _ in range(3)])
    table(base/'footprint/owners.bin',[[n,net] for net,ns in [(0,[0,2,3,5,7]),(1,[4,1,6]),(2,[8,10,9])] for n in ns])
    pairs=[(0,1),(0,2),(0,10),(1,5),(1,6),(2,3),(3,5),(3,7),(4,1),(8,10),(10,7),(10,9)]
    def slr_mask(n):return 5 if n==10 else 3 if n==1 else 2 if n in (4,6) else 1
    table(base/'graph/pips.bin',[[k,src,dst,0,k,k,(slr_mask(src)&slr_mask(dst)&-(slr_mask(src)&slr_mask(dst))).bit_length()-1,0] for k,(src,dst) in enumerate(pairs)])
    offsets=[0];arcs=[]
    for n in range(11):arcs.extend(sorted((dst,k*2) for k,(src,dst) in enumerate(pairs) if src==n));offsets.append(len(arcs))
    container(base/'search/offsets.bin',0x44520001,8,struct.pack('<12Q',*offsets));container(base/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*x) for x in arcs))
    container(base/'search/node_protection.bin',0x4452000a,1,bytes(11))
    container(base/'search/exclusive_net.bin',0x4452000b,4,struct.pack('<11I',0,0xffffffff,0xffffffff,0xffffffff,1,0,1,0,2,2,0xffffffff))
    r=subprocess.run([str(a.quotient_builder.resolve()),str(base/'graph'),str(base/'search'),FINGERPRINT,str(base/'quotient')],capture_output=True,text=True);assert r.returncode==0,r.stderr
    cases=[];commands={}
    for name,budget,iterations,repeats in [('complete',100,10,3),('shadow1',100,10,3),('shadow3',100,10,3),('corridor',100,10,3),('corridor_shadow3',100,10,3),('corridor_bounded',100,10,3),('corridor_candidates',100,10,3),('corridor_candidates_shadow3',100,10,3),('corridor_joint',100,10,3),('corridor_joint_shadow3',100,10,3),('corridor_joint_reentry',100,10,3),('one_epoch',100,1,1),('budget',1,2,1),('frozen_source',100,10,1)]:
        d=out/name;shutil.copytree(base,d)
        if name=='frozen_source':bad=[list(t) for t in tasks];bad[0][2]=bad[2][2]=10;table(d/'footprint/tasks.bin',bad)
        command=[str(a.router.resolve()),str(d/'graph'),str(d/'search'),str(d/'footprint'),str(d/'mapping'),str(d/'quotient'),FINGERPRINT,str(d/'route'),str(budget),'1',str(iterations),str(repeats)]
        if name.startswith('shadow'):
            command[1:7]=commands['complete'][1:7];command.append(name[-1])
        if name.startswith('corridor'):command.extend(['3' if name.endswith('shadow3') else '0','3'])
        if name=='corridor_bounded':command.extend(['1','1'])
        if name.startswith('corridor_candidates'):command.extend(['0','1','3'])
        if name.startswith('corridor_joint'):command.extend(['1' if 'reentry' in name else '0','1' if 'reentry' in name else '0','1','1'])
        commands[name]=command
        r=subprocess.run(command,capture_output=True,text=True);(d/'run.log').write_text(r.stdout+r.stderr)
        if name=='frozen_source':assert r.returncode==1 and 'endpoint frozen or forbidden' in r.stderr
        else:
            assert r.returncode==0,r.stderr;report=json.loads((d/'route/audit.json').read_text());assert report['selected_seed_tasks']==2 and report['selected_nets']==2 and report['all_selected_net_tasks']==3 and report['frozen_unselected_footprint_nodes']==3
            trees=list(csv.DictReader((d/'route/trees.csv').open()));assert all(int(t['node']) not in (8,9,10) for t in trees)
            iters=list(csv.DictReader((d/'route/iterations.csv').open()))
            if name in ('complete','shadow1','shadow3','corridor','corridor_shadow3','corridor_bounded','corridor_candidates','corridor_candidates_shadow3','corridor_joint','corridor_joint_shadow3','corridor_joint_reentry'):
                assert report['electrical_model_converged_repeats']==3
                if not name.startswith('corridor'):assert any(int(r['overused_nodes'])>0 for r in iters)
                for rep in range(repeats):assert [r for r in iters if int(r['repeat'])==rep][-1]['overused_nodes']=='0'
                uses=list(csv.DictReader((d/'route/usage.csv').open()))
                for rep in range(repeats):
                    active=[r for r in uses if int(r['repeat'])==rep and int(r['net'])!=0xffffffff];assert len({r['node'] for r in active})==len(active)
                if name.startswith('shadow'):
                    for filename in ('selection.csv','trees.csv','usage.csv','paths.csv','connections.csv'):
                        assert (d/'route'/filename).read_bytes()==(out/'complete/route'/filename).read_bytes(),filename
                    metrics=list(csv.DictReader((d/'route/shadow_metrics.csv').open()))
                    assert all(int(r['remote_reads'])>0 for r in metrics)
                    assert all(int(r['logical_deliveries'])==2*int(r['changed_summaries']) for r in metrics)
                    assert all((int(r['replays'])==0 if name=='shadow1' else int(r['replays'])>0) for r in metrics)
                if name.startswith('corridor'):
                    runs=list(csv.DictReader((d/'route/corridor_runs.csv').open()))
                    assert runs and any(int(r['local_searches'])+int(r.get('joint_searches',0)) for r in runs) and any(int(r['fallbacks']) for r in runs)
                    assert all(int(r['reserved'])==int(r['released'])+int(r['retained']) for r in runs)
            else:assert report['electrical_model_converged_repeats']==0
            if name=='budget':assert any(r['status']=='budget_exhausted' for r in csv.DictReader((d/'route/connections.csv').open()))
        cases.append(dict(case=name,passed=True,returncode=r.returncode))
    # Route the same full fixture through real owner shards (flat, corridor and
    # stale-shadow modes). Every pre-existing artifact must be byte-identical.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
    from audit_native_owner import verify_owner_usage
    for name in ('complete','shadow3','corridor_joint','corridor_joint_shadow3'):
        directory=out/(name+'_owners');directory.mkdir();command=list(commands[name]);command[7]=str(directory/'route')
        defaults=['0','0','0','0','1','0','0']
        command.extend(defaults[len(command)-12:]);command.append('1')
        result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
        for f in (out/name/'route').iterdir():
            if f.name!='owner_usage.csv':assert f.read_bytes()==(directory/'route'/f.name).read_bytes(),(name,f.name)
        nodes=Path(command[1],'nodes.bin').read_bytes()
        verified=verify_owner_usage(directory/'route',nodes,True,3)
        assert verified['unique_owner_inventory_verified'] and {r['owner'] for r in verified['records']}=={0,1}
        if name.startswith('corridor'):
            from audit_native_corridor import verify_trace
            assert verify_trace(directory,{'command':command})['authority_reconstructed']
        path=directory/'route/owner_usage.csv';original=path.read_bytes()
        with path.open() as stream:records=list(csv.DictReader(stream))
        records[0]['owner']=str((int(records[0]['owner'])+1)%3)
        with path.open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
        rejected=False
        try:verify_owner_usage(directory/'route',nodes,True,3)
        except AssertionError:rejected=True
        assert rejected,'wrong owner accepted with unchanged canonical authority'
        path.write_bytes(original)
    if a.parallel_router:
        from audit_native_parallel import verify as verify_parallel
        controls=None
        for workers in (1,2,4):
            directory=out/('parallel_'+str(workers));directory.mkdir()
            command=list(commands['corridor_joint']);command[0]=str(a.parallel_router.resolve());command[7]=str(directory/'route')
            defaults=['0','0','0','0','1','0','0','0','0'];command.extend(defaults[len(command)-12:])
            command[18:21]=['1','1','1'];command.append(str(workers))
            result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
            proof=verify_parallel(directory,{'command':command});assert proof['passed']
            if controls is None:controls=directory
            for filename in ('trees.csv','usage.csv','paths.csv','connections.csv','owner_usage.csv','accepted_work.csv'):
                assert (controls/'route'/filename).read_bytes()==(directory/'route'/filename).read_bytes(),(workers,filename)
            for filename in ('trees.csv','usage.csv','paths.csv','connections.csv'):
                assert (out/'corridor_joint/route'/filename).read_bytes()==(directory/'route'/filename).read_bytes(),filename
            for filename,field in [('transactions.csv','conflicts'),('transactions.csv','expanded'),('proposals.csv','cost')]:
                path=directory/'route'/filename;original=path.read_bytes()
                with path.open() as stream:records=list(csv.DictReader(stream))
                records[0][field]=str(int(records[0][field])+1)
                with path.open('w') as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
                rejected=False
                try:verify_parallel(directory,{'command':command})
                except AssertionError:rejected=True
                finally:path.write_bytes(original)
                assert rejected,(filename,field)
        from native_csr_test import crc
        path=directory/'route/readsets.bin';original=path.read_bytes();damaged=bytearray(original)
        for offset in range(64,len(damaged),16):
            version=struct.unpack_from('<Q',damaged,offset+8)[0];struct.pack_into('<Q',damaged,offset+8,version+1)
        struct.pack_into('<Q',damaged,48,crc(damaged[64:]));path.write_bytes(damaged)
        rejected=False
        try:verify_parallel(directory,{'command':command})
        except AssertionError:rejected=True
        finally:path.write_bytes(original)
        assert rejected,'forged read versions with valid CRC'
        cases.append(dict(case='parallel_nets_serial_parity_and_audit_corruption',passed=True,returncode=0))
    # Execute the joint search on independent die queues and demand summaries.
    # Physical route and every legacy journal remain identical to the control.
    for name in ('corridor_joint','corridor_joint_reentry'):
        directory=out/(name+'_workers');directory.mkdir();command=list(commands[name]);command[7]=str(directory/'route')
        defaults=['0','0','0','0','1','0','0','0']
        command.extend(defaults[len(command)-12:]);command[19]='1';command.append('1')
        result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
        for f in (out/name/'route').iterdir():
            if f.name not in ('owner_usage.csv','worker_queues.csv','worker_reads.csv','worker_access.csv','worker_transport.csv','worker_packets.bin'):
                assert f.read_bytes()==(directory/'route'/f.name).read_bytes(),(name,f.name)
        from audit_native_corridor import verify_trace
        verified=verify_trace(directory,{'command':command});assert verified['workers']['recorded_protocol_verified']
        assert verified['workers']['totals']['attempts']>0
        assert verified['workers']['label_transport']['verified']
        # These same-die fixtures use the controller fallback for incidental boundaries.
        assert verified['workers']['totals']['transfers']==0
        # Final route remains untouched by these adversarial journal mutations.
        for filename,field in [('worker_queues.csv','expanded'),('worker_access.csv','requests'),('worker_transport.csv','probes')]:
            path=directory/'route'/filename;original=path.read_bytes()
            with path.open() as stream:records=list(csv.DictReader(stream))
            records[0][field]=str(int(records[0][field])+1)
            with path.open('w') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
            rejected=False
            try:verify_trace(directory,{'command':command})
            except AssertionError:rejected=True
            assert rejected,(filename,field);path.write_bytes(original)
    # Three physical dies in descending order force nonowner boundary reads,
    # including an off-path branch, and actual frontier transfers.
    cross=out/'worker_cross';cross.mkdir()
    for name in ('graph','search','footprint','mapping'):(cross/name).mkdir()
    memberships=[4,6,2,3,1,6,1,2,4]
    table(cross/'graph/nodes.bin',[[n,n,0,n,0,memberships[n],1,0,0,0,0,0,0,0,0,0] for n in range(9)])
    table(cross/'mapping/footprint_node_map.bin',[[n] for n in range(9)])
    table(cross/'footprint/tasks.bin',[[0,0,0,4,2,0,0,0]])
    table(cross/'footprint/nets.bin',[[0]*16]);table(cross/'footprint/owners.bin',[[n,0] for n in range(5)])
    crossing=[(0,1,2),(0,5,2),(1,2,1),(2,3,1),(3,4,0)];offsets=[0];arcs=[]
    table(cross/'graph/pips.bin',[[k,s,d,0,k,k,die,0] for k,(s,d,die) in enumerate(crossing)])
    for n in range(9):arcs.extend(sorted((d,k*2) for k,(s,d,die) in enumerate(crossing) if s==n));offsets.append(len(arcs))
    container(cross/'search/offsets.bin',0x44520001,8,struct.pack('<10Q',*offsets));container(cross/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*arc) for arc in arcs))
    container(cross/'search/node_protection.bin',0x4452000a,1,bytes(9));container(cross/'search/exclusive_net.bin',0x4452000b,4,struct.pack('<9I',*([0xffffffff]*9)))
    result=subprocess.run([str(a.quotient_builder.resolve()),str(cross/'graph'),str(cross/'search'),FINGERPRINT,str(cross/'quotient')],capture_output=True,text=True);assert result.returncode==0,result.stderr
    for enabled in (0,1):
        case=cross/str(enabled);case.mkdir()
        cmd=[str(a.router.resolve()),*[str(cross/n) for n in ('graph','search','footprint','mapping','quotient')],FINGERPRINT,str(case/'route'),'100','1','3','3','0','3','0','0','1','1','0','1',str(enabled)]
        result=subprocess.run(cmd,capture_output=True,text=True);assert result.returncode==0,result.stderr
        proof=verify_trace(case,{'command':cmd})
        if enabled:
            assert proof['workers']['totals']['requests']>=6 and proof['workers']['totals']['transfers']>=6
            for filename in ('trees.csv','usage.csv','paths.csv','connections.csv','corridor_runs.csv','iterations.csv'):
                assert (case/'route'/filename).read_bytes()==(cross/'0/route'/filename).read_bytes()
            for field in ('owner','version'):
                path=case/'route/worker_reads.csv';original=path.read_bytes()
                with path.open() as stream:records=list(csv.DictReader(stream))
                records[0][field]=str(int(records[0][field])+1)
                with path.open('w') as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
                rejected=False
                try:verify_trace(case,{'command':cmd})
                except AssertionError:rejected=True
                assert rejected,field;path.write_bytes(original)
            # Change every repetition identically and recompute the container
            # CRC, so these require semantic checks rather than hash failures.
            from native_csr_test import crc
            packet_path=case/'route/worker_packets.bin';original=packet_path.read_bytes()
            assert proof['workers']['label_transport']['verified']
            for corruption in ('ack_created','probe_version','trace_cost','relax_parent','request_id'):
                damaged=bytearray(original);changed=0
                for offset in range(64,len(damaged),128):
                    words=list(struct.unpack_from('<8Q',damaged,offset+64));op=(words[2]>>32)&255
                    if corruption=='ack_created' and op==4:words[6]^=8<<32
                    elif corruption=='probe_version' and op==2:words[7]+=9
                    elif corruption=='trace_cost' and op==6:words[3]+=1
                    elif corruption=='relax_parent' and op==3:words[5]=(words[5]&0xffffffff)|(8<<32)
                    elif corruption=='request_id' and op in (1,2):words[1]=1
                    else:continue
                    struct.pack_into('<8Q',damaged,offset+64,*words);changed+=1
                assert changed
                struct.pack_into('<Q',damaged,48,crc(damaged[64:]));packet_path.write_bytes(damaged)
                rejected=False
                try:verify_trace(case,{'command':cmd})
                except AssertionError:rejected=True
                finally:packet_path.write_bytes(original)
                assert rejected,corruption
    if a.parallel_router:
        controls=out/'parallel_reverse_control';controls.mkdir();command=list(cmd)
        command[0]=str(a.parallel_router.resolve());command[7]=str(controls/'route');command[18]='1';command.append('2')
        result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
        assert verify_parallel(controls,{'command':command})['passed']
        for period in (1,3):
            directory=out/('persistent_shadow_'+str(period));directory.mkdir();command=list(command[:22]);command[7]=str(directory/'route');command.append(str(period))
            result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
            proof=verify_parallel(directory,{'command':command});assert proof['persistent_shadows']['enabled'] and proof['persistent_shadows']['complete_tail_verified']
            for filename in ('trees.csv','usage.csv','paths.csv','connections.csv','owner_usage.csv','accepted_work.csv'):
                assert (controls/'route'/filename).read_bytes()==(directory/'route'/filename).read_bytes(),(period,filename)
            for filename,field in [('persistent_shadow_reads.csv','version'),('persistent_shadow_checks.csv','stale'),('persistent_shadow_publications.csv','messages')]:
                path=directory/'route'/filename;original=path.read_bytes()
                with path.open() as stream:records=list(csv.DictReader(stream))
                assert records
                for record in records:record[field]=str(int(record[field])+1)
                with path.open('w') as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
                rejected=False
                try:verify_parallel(directory,{'command':command})
                except AssertionError:rejected=True
                finally:path.write_bytes(original)
                assert rejected,(filename,field)
            path=directory/'route/worker_shadow_messages.bin';original=path.read_bytes();damaged=bytearray(original);changed=0
            for offset in range(64,len(damaged),128):
                words=list(struct.unpack_from('<8Q',damaged,offset+64))
                if (words[1]>>48)&255 in (2,3):
                    words[4]+=1;struct.pack_into('<8Q',damaged,offset+64,*words);changed+=1
            assert changed;struct.pack_into('<Q',damaged,48,crc(damaged[64:]));path.write_bytes(damaged)
            rejected=False
            try:verify_parallel(directory,{'command':command})
            except AssertionError:rejected=True
            finally:path.write_bytes(original)
            assert rejected,'forged summary wire version with valid CRC'
        cases.append(dict(case='persistent_worker_summaries_and_semantic_corruption',passed=True,returncode=0))
        for period in (1,3):
            shadow_baseline=out/('persistent_shadow_'+str(period));directory=out/('summary_hbm_'+str(period));directory.mkdir()
            hbm_command=list(command[:22])+[str(period),'1'];hbm_command[7]=str(directory/'route')
            result=subprocess.run(hbm_command,capture_output=True,text=True);assert result.returncode==0,result.stderr
            assert verify_parallel(directory,{'command':hbm_command})['passed']
            for f in (shadow_baseline/'route').iterdir():
                if (f.suffix=='.csv' and f.name!='execution.csv' and not f.name.startswith('summary_hbm_')) or f.name in ('readsets.bin','worker_shadow_messages.bin'):
                    assert f.read_bytes()==(directory/'route'/f.name).read_bytes(),(period,f.name)
            (directory/'command.json').write_text(json.dumps(hbm_command,indent=2)+'\n')
            # Preserve valid CRCs and repeat normalization while corrupting
            # descriptor, reply, receipt or publication semantics.
            path=directory/'route/summary_hbm_frames.bin';original=path.read_bytes()
            for word,reason in ((17,0),(26,0),(32,0),(10,1)):
                damaged=bytearray(original);changed=0
                for offset in range(64,len(damaged),384):
                    words=list(struct.unpack_from('<48Q',damaged,offset))
                    if words[5]==reason:
                        words[word]+=1;struct.pack_into('<48Q',damaged,offset,*words);changed+=1
                assert changed
                struct.pack_into('<Q',damaged,48,crc(damaged[64:]));path.write_bytes(damaged)
                rejected=False
                try:verify_parallel(directory,{'command':hbm_command})
                except AssertionError:rejected=True
                finally:path.write_bytes(original)
                assert rejected,('forged endpoint frame with valid CRC',word,reason)
            # Keep every endpoint operation and state transition intact, but
            # claim the initial zero owner values were installed after commit.
            # Endpoint replay alone accepts this; coordinator binding must fail.
            from audit_native_summary_hbm import SummaryEndpointAudit
            damaged=bytearray(original)
            for offset in range(64,len(damaged),384):
                words=list(struct.unpack_from('<48Q',damaged,offset))
                if words[5]==1 and words[1]==0 and words[2]==0 and words[4]==0:
                    words[1]=0xffffffff;words[2]=1;struct.pack_into('<48Q',damaged,offset,*words)
            struct.pack_into('<Q',damaged,48,crc(damaged[64:]));path.write_bytes(damaged)
            rejected=False
            try:
                SummaryEndpointAudit(directory/'route',hbm_command)
                verify_parallel(directory,{'command':hbm_command})
            except AssertionError as error:
                rejected=str(error)=='owner install does not match actual coordinator state'
            finally:path.write_bytes(original)
            assert rejected,'endpoint-valid owner installation at wrong commit boundary'
        cases.append(dict(case='live_summary_hbm_routing_parity',passed=True,returncode=0))

    # Receiver refuses a new remote label when the global label credit is spent.
    case=cross/'credit_denied';case.mkdir();cmd=list(cmd);cmd[7]=str(case/'route');cmd[8]='1'
    result=subprocess.run(cmd,capture_output=True,text=True);assert result.returncode==0,result.stderr
    proof=verify_trace(case,{'command':cmd})
    assert proof['workers']['label_transport']['totals']['rejected']>0
    cases.append(dict(case='label_transport_semantic_corruption_and_credit',passed=True,returncode=0))
    # Exercise the independent journal audit, including adversarial edits whose
    # file hashes have been updated (so failure requires semantic checks).
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
    from audit_native_boundary_shadow import verify
    from audit_native_corridor import verify_trace
    from compare_native_corridor import die_path_census
    from run_native_case import sha256
    shared_inputs={str(f):sha256(f) for name in ('graph','search','footprint','mapping','quotient') for f in (out/'complete'/name).rglob('*') if f.is_file()}
    def manifest(name):
        directory=out/name
        record=dict(status='passed',inputs_unchanged=True,electrical_model_converged=True,
                    command=commands[name],inputs=shared_inputs,source_sha256={'router':sha256(a.router)},
                    artifacts={str(f.relative_to(directory)):sha256(f) for f in (directory/'route').iterdir() if f.is_file()})
        (directory/'manifest.json').write_text(json.dumps(record))
    for name in ('complete','shadow1','shadow3'):manifest(name)
    for name in ('shadow1','shadow3'):assert verify(out/'complete',out/name)['passed']
    census=die_path_census(out/'complete',commands['complete'])
    assert census['paths']==3 and census['paths_with_die_reentry']==[]
    assert census['paths_with_incidental_internal_boundaries']==[1] and census['unique_incidental_boundary_nodes']==[1]
    for name in ('corridor','corridor_shadow3','corridor_bounded','corridor_candidates','corridor_candidates_shadow3','corridor_joint','corridor_joint_shadow3','corridor_joint_reentry'):
        assert verify_trace(out/name,{'command':commands[name]})['authority_reconstructed']
    path=out/'corridor/route/corridor_runs.csv';original=path.read_bytes()
    with path.open() as stream:records=list(csv.DictReader(stream))
    records[0]['cost']=str(int(records[0]['cost'])+1)
    with path.open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    rejected=False
    try:verify_trace(out/'corridor',{'command':commands['corridor']})
    except AssertionError:rejected=True
    assert rejected,'corrupted corridor candidate cost'
    path.write_bytes(original)
    for field in ('stale','read_hash'):
        path=out/'shadow3/route/shadow_trace.csv';original=path.read_bytes()
        with path.open() as stream:records=list(csv.DictReader(stream))
        records[0][field]=str(1-int(records[0][field])) if field=='stale' else str(int(records[0][field])^1)
        with path.open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
        manifest('shadow3');rejected=False
        try:verify(out/'complete',out/'shadow3')
        except AssertionError:rejected=True
        assert rejected,field
        path.write_bytes(original);manifest('shadow3')
    path=out/'shadow3/route/shadow_final.csv';original=path.read_bytes()
    lines=original.splitlines(keepends=True);assert len(lines)>1;path.write_bytes(b''.join(lines[:-1]));manifest('shadow3')
    rejected=False
    try:verify(out/'complete',out/'shadow3')
    except AssertionError:rejected=True
    assert rejected,'missing final boundary update'
    path.write_bytes(original);manifest('shadow3')
    cases.append(dict(case='journal_audit_and_corruption',passed=True,returncode=0))
    # The first sink exhausts the budget on false quotient shortcuts. Routing
    # the nearer second sink grows a tree whose new seed avoids that expansion.
    d=out/'deferred';shutil.copytree(base,d)
    table(d/'graph/nodes.bin',[[n,2 if n>=5 else n,n,2 if n>=5 else n,n,1,1,0,0,0,0,0,0,0,0,0] for n in range(10)])
    table(d/'mapping/footprint_node_map.bin',[[n] for n in range(10)])
    table(d/'footprint/tasks.bin',[[0,0,0,4,0,0,0,0],[1,0,0,2,0,0,0,0]])
    table(d/'footprint/nets.bin',[[0]*16]);table(d/'footprint/owners.bin',[[n,0] for n in range(5)])
    pairs=[(0,1),*[(0,n) for n in range(5,10)],(1,2),(2,3),(3,4)];offsets=[0];arcs=[]
    for n in range(10):arcs.extend(sorted((dst,k*2) for k,(src,dst) in enumerate(pairs) if src==n));offsets.append(len(arcs))
    container(d/'search/offsets.bin',0x44520001,8,struct.pack('<11Q',*offsets));container(d/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*x) for x in arcs))
    container(d/'search/node_protection.bin',0x4452000a,1,bytes(10));container(d/'search/exclusive_net.bin',0x4452000b,4,struct.pack('<10I',0,0xffffffff,0,0xffffffff,0,*([0xffffffff]*5)))
    r=subprocess.run([str(a.quotient_builder.resolve()),str(d/'graph'),str(d/'search'),FINGERPRINT,str(d/'deferred_quotient')],capture_output=True,text=True);assert r.returncode==0,r.stderr
    cmd=[str(a.router.resolve()),str(d/'graph'),str(d/'search'),str(d/'footprint'),str(d/'mapping'),str(d/'deferred_quotient'),FINGERPRINT,str(d/'route'),'8','1','1','3']
    r=subprocess.run(cmd,capture_output=True,text=True);(d/'run.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
    report=json.loads((d/'route/audit.json').read_text());assert report['electrical_model_converged_repeats']==3
    rows=list(csv.DictReader((d/'route/iterations.csv').open()));assert all(int(r['deferred_retries'])==1 and int(r['max_labels'])==8 and r['failed_tasks']=='0' for r in rows)
    cases.append(dict(case='deferred',passed=True,returncode=r.returncode))
    # The same budget-limited first sink recovers after the nearer sink grows
    # the tree, without a duplicate full-graph search in the first pass.
    growth=out/'joint_deferred_growth';shutil.copytree(d,growth,ignore=shutil.ignore_patterns('route','run.log'))
    table(growth/'graph/pips.bin',[[k,src,dst,0,k,k,0,0] for k,(src,dst) in enumerate(pairs)])
    growth_cmd=[str(a.router.resolve()),str(growth/'graph'),str(growth/'search'),str(growth/'footprint'),str(growth/'mapping'),str(growth/'deferred_quotient'),FINGERPRINT,str(growth/'route'),'8','1','1','3','0','3','0','0','1','1','1']
    r=subprocess.run(growth_cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
    for name in ('trees.csv','paths.csv','usage.csv','connections.csv'):assert (growth/'route'/name).read_bytes()==(d/'route'/name).read_bytes()
    checked=verify_trace(growth,{'command':growth_cmd});assert checked['schedule']['accepted_budget_deferrals']==3 and checked['schedule']['rescue_transitions']==0 and checked['metrics']['flat_searches']==0
    cases.append(dict(case='joint_deferred_growth',passed=True,returncode=0))
    # A valid short path uses a boundary wire within the same die. The joint
    # policy excludes it and exhausts its budget on a long dead-end chain.
    # Once no other sink can grow the tree, full-graph rescue must find it.
    rescue_cases={}
    for name,budget,expected in [('joint_rescue',6,3),('joint_rescue_budget',1,0)]:
        d=out/name;shutil.copytree(base,d)
        table(d/'graph/nodes.bin',[[n,0,n,0,n,3 if n==1 else 1,1,0,0,0,0,0,0,0,0,0] for n in range(10)])
        table(d/'footprint/tasks.bin',[[0,0,0,4,0,0,0,0]])
        table(d/'footprint/nets.bin',[[0]*16]);table(d/'footprint/owners.bin',[[n,0] for n in (0,1,4)])
        pairs=[(0,1),(1,4),(0,2),(2,3),(3,5),(5,6),(6,7),(7,8),(8,9)];offsets=[0];arcs=[]
        table(d/'graph/pips.bin',[[k,src,dst,0,k,k,0,0] for k,(src,dst) in enumerate(pairs)])
        for n in range(10):arcs.extend(sorted((dst,k*2) for k,(src,dst) in enumerate(pairs) if src==n));offsets.append(len(arcs))
        container(d/'search/offsets.bin',0x44520001,8,struct.pack('<11Q',*offsets));container(d/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*x) for x in arcs))
        container(d/'search/node_protection.bin',0x4452000a,1,bytes(10));container(d/'search/exclusive_net.bin',0x4452000b,4,struct.pack('<10I',*([0xffffffff]*10)))
        r=subprocess.run([str(a.quotient_builder.resolve()),str(d/'graph'),str(d/'search'),FINGERPRINT,str(d/'rescue_quotient')],capture_output=True,text=True);assert r.returncode==0,r.stderr
        cmd=[str(a.router.resolve()),str(d/'graph'),str(d/'search'),str(d/'footprint'),str(d/'mapping'),str(d/'rescue_quotient'),FINGERPRINT,str(d/'route'),str(budget),'1','1','3','0','3','0','0','1','1','1']
        r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
        assert json.loads((d/'route/audit.json').read_text())['electrical_model_converged_repeats']==expected
        verified=verify_trace(d,{'command':cmd});assert verified['schedule']['rescue_transitions']==3 and verified['metrics']['flat_searches']==3 and verified['metrics']['joint_searches']==3
        logs=list(csv.DictReader((d/'route/corridor_runs.csv').open()));assert [r['fallback_mode'] for r in logs]==['1','2']*3
        actor=out/(name+'_workers');actor.mkdir();actor_cmd=list(cmd);actor_cmd[7]=str(actor/'route');actor_cmd.extend(['1','1'])
        result=subprocess.run(actor_cmd,capture_output=True,text=True);assert result.returncode==0,result.stderr
        proof=verify_trace(actor,{'command':actor_cmd});assert proof['workers']['recorded_protocol_verified'] and proof['metrics']['flat_searches']==3
        for file in ('trees.csv','usage.csv','paths.csv','connections.csv','iterations.csv','cohort_passes.csv'):
            assert (actor/'route'/file).read_bytes()==(d/'route'/file).read_bytes(),file
        rescue_cases[name]=(d,cmd);cases.append(dict(case=name,passed=True,returncode=0))
    # These mutations preserve the final electrical trees. The independent
    # schedule/work verifier must nevertheless reject them.
    d,cmd=rescue_cases['joint_rescue']
    for file,field,where in [('corridor_runs.csv','fallback_mode',1),('corridor_trace.csv','search_status',0),('corridor_runs.csv','joint_expanded',0)]:
        path=d/'route'/file;original=path.read_bytes()
        with path.open() as f:records=list(csv.DictReader(f))
        records[where][field]='0' if field=='fallback_mode' else str(int(records[where][field])+1)
        with path.open('w') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
        rejected=False
        try:verify_trace(d,{'command':cmd})
        except AssertionError:rejected=True
        finally:path.write_bytes(original)
        assert rejected,field
    cases.append(dict(case='rescue_schedule_and_work_corruption',passed=True,returncode=0))
    (out/'tests.json').write_text(json.dumps(dict(passed=True,cases=cases),indent=2)+'\n');print(f'{len(cases)} native cohort consumer cases passed')
if __name__=='__main__':main()
