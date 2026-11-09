"""Frozen first-case pressure consumer checks and descriptive native feedback trial."""
import json,os,re,shutil,subprocess,time,resource
from pathlib import Path
from prepared_csr import read
from pre_route_endpoints import sha


def main():
    base=Path('experiments');design='adder_tree_2L_032bits'
    front=base/'adder_tree_family_endpoints_2026-10-06'/design
    fp=json.loads((front/'protocol.json').read_text());inputs=fp['inputs'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
    parent=base/'adder_tree_family_predictions_2026-10-06'/design/'sparse_reset';pr=json.loads((parent/'receipt.json').read_text());assert sha(parent/'prediction.json')==pr['prediction_sha256']
    p=json.loads((parent/'protocol.json').read_text());assert p['inputs']['graph']==inputs['rr_graph']
    prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design;assert sha(prepared/'csr/manifest.json')==p['csr_manifest_sha256']
    m,f=read(prepared/'csr',inputs['rr_graph']['sha256'])
    build=Path('build/native_pressure_feedback_v2_2026-10-06');binary=(build/'routecast_pressure_vpr').resolve();br=json.loads((build/'receipt.json').read_text());assert sha(binary)==br['binary_sha256']
    out=base/'native_pressure_payload_trial_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
    work=Path('work/native_pressure_payload_trial_2026-10-06');work.mkdir()
    occ=json.loads((parent/'prediction.json').read_text())['node_occupancy'];channels=[n for n in range(m['nodes']) if f['types'][n] in (4,5) and f['capacities'][n]>0]
    pressure=[(n,f['capacities'][n],1+max(0,occ.get(str(n),0)-f['capacities'][n])/f['capacities'][n]) for n in channels if occ.get(str(n),0)>f['capacities'][n]]
    header=f"ROUTECAST_PRESSURE_V1 {m['nodes']} {inputs['rr_graph']['sha256']}\n"
    payloads={'off':None,'neutral':header,'on':header+''.join(f'{n} {cap} {value:.9g}\n' for n,cap,value in pressure),
              'bad_digest':header.replace(inputs['rr_graph']['sha256'],'0'*64),
              'bad_type':header+f"0 {f['capacities'][0]} 2\n",
              'duplicate':header+f'{channels[0]} {f["capacities"][channels[0]]} 2\n'*2,
              'bad_capacity':header+f'{channels[0]} {f["capacities"][channels[0]]+1} 2\n',
              'bad_value':header+f'{channels[0]} {f["capacities"][channels[0]]} 0.5\n'}
    protocol={'inputs':inputs,'prediction_receipt_sha256':sha(parent/'receipt.json'),'binary_sha256':sha(binary),'source_sha256':sha(__file__),'pressure_rule':'channel acc_cost=1+max(0,predicted distinct-net occupancy-capacity)/capacity; coefficient1 frozen, pins excluded','pressure_nodes':len(pressure),'order':list(payloads),'scope':'first development readiness case, no native-label pressure tuning; off/neutral/on descriptive and malformed-input rejection only; not paired total-time gain'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
    for name,text in payloads.items():
        wd=work/name;wd.mkdir()
        for key,file in [('atom','design.blif'),('packed_netlist','design.net'),('reference_place','design.place')]:shutil.copyfile(inputs[key]['path'],wd/file)
        env=dict(os.environ)
        for key in ('ROUTECAST_PRESSURE_FILE','ROUTECAST_EXPECT_GRAPH_SHA256'):env.pop(key,None)
        if text is not None:
            file=out/(name+'.pressure');file.write_text(text);env['ROUTECAST_PRESSURE_FILE']=str(file.resolve());env['ROUTECAST_EXPECT_GRAPH_SHA256']=inputs['rr_graph']['sha256']
        command=[str(binary),inputs['architecture']['path'],'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',inputs['rr_graph']['path'],'--route_chan_width','300','--num_workers','1','--seed','1','--max_router_iterations','100']
        (out/(name+'_command.json')).write_text(json.dumps({'command':command,'cwd':str(wd.resolve())},indent=2)+'\n');start=time.monotonic()
        def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        with (out/(name+'.log')).open('w') as log:code=subprocess.run(command,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60,preexec_fn=no_core).returncode
        logtext=(out/(name+'.log')).read_text();good=name in ('off','neutral','on')
        if good:
            assert code==0 and 'VPR succeeded' in logtext
            if name!='off':assert f'RouteCast pressure applied: {len(pressure) if name=="on" else 0} channel nodes' in logtext
        else:assert code!=0 and 'RouteCast pressure applied' not in logtext and not (wd/'design.route').exists()
        row={'case':name,'exit_code':code,'wall_s':time.monotonic()-start,'pressure_applied': 'RouteCast pressure applied' in logtext,'log_sha256':sha(out/(name+'.log'))}
        if good:row.update(route_sha256=sha(wd/'design.route'),cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',logtext)[1]),wirelength=int(re.search(r'Total wirelength:\s*(\d+)',logtext)[1]))
        results.append(row);print(json.dumps(row),flush=True)
    assert results[0]['route_sha256']==results[1]['route_sha256']
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values()) and sha(binary)==br['binary_sha256']
    receipt={'protocol_sha256':sha(out/'protocol.json'),'results':results,'neutral_route_byte_parity':True,'malformed_cases_rejected':5,'pressure_nodes':len(pressure),'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':main()
