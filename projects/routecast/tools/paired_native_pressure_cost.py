"""Two ABBA cycles with live fresh predictor cost for a fixed arithmetic placement."""
import json,os,re,shutil,subprocess,sys,time
from pathlib import Path
from prepared_csr import read
from pre_route_endpoints import sha


def main():
    base=Path('experiments');design='adder_tree_2L_032bits';front=base/'adder_tree_family_endpoints_2026-10-06'/design
    inputs=json.loads((front/'protocol.json').read_text())['inputs'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
    baseline=base/'adder_tree_family_predictions_2026-10-06'/design/'sparse_reset';reference=json.loads((baseline/'receipt.json').read_text());assert sha(baseline/'prediction.json')==reference['prediction_sha256']
    prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design;prep=json.loads((prepared/'receipt.json').read_text())
    build=Path('build/native_pressure_feedback_v2_2026-10-06');binary=(build/'routecast_pressure_vpr').resolve();br=json.loads((build/'receipt.json').read_text());assert sha(binary)==br['binary_sha256']
    out=base/'native_pressure_paired_cached_cost_2026-10-06';out.mkdir();(out/'source').mkdir();work=Path('work/native_pressure_paired_cached_cost_2026-10-06');work.mkdir()
    names=['paired_native_pressure_cost.py','replay_adder_tree_prediction.py','prepared_csr.py','pre_route_endpoints.py'];sources={n:sha(Path('tools')/n) for n in names}
    for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
    sequence=['off','on','on','off']*2
    protocol={'inputs':inputs,'binary_sha256':sha(binary),'sources':sources,'baseline_receipt_sha256':sha(baseline/'receipt.json'),'csr_receipt_sha256':sha(prepared/'receipt.json'),'sequence':sequence,'pressure_rule':'same coefficient1 normalized channel overuse; freshly recomputed sparse-reset prediction every on run','scope':'single-design two ABBA cycles, cached authenticated CSR and pre-route endpoints; timed on includes fresh estimator/payload/full native routing; offline validation and initial packing/placement/endpoint extraction/cache construction excluded','cold_conversion_archived_s':prep['wall_s'],'limitations':'concurrent host workload and one design; cached and cold accounting kept separate; not hardware or unseen-family result'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
    for i,mode in enumerate(sequence):
        tag=f'{i:02d}_{mode}';wd=work/tag;wd.mkdir();env=dict(os.environ)
        for key in ('ROUTECAST_PRESSURE_FILE','ROUTECAST_EXPECT_GRAPH_SHA256'):env.pop(key,None)
        # Common immutable input staging is outside both timed paths.
        for key,name in [('atom','design.blif'),('packed_netlist','design.net'),('reference_place','design.place')]:shutil.copyfile(inputs[key]['path'],wd/name)
        estimator_s=payload_s=0;nodes=0;start=time.monotonic()
        if mode=='on':
            prediction=out/(tag+'_prediction');command=[sys.executable,'tools/replay_adder_tree_prediction.py','--output',str(prediction),design,'sparse_reset'];step=time.monotonic()
            with (out/(tag+'_estimator.log')).open('w') as log:code=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
            assert code==0;estimator_s=time.monotonic()-step
            r=json.loads((prediction/'receipt.json').read_text());assert r['failed']==0 and sha(prediction/'prediction.json')==r['prediction_sha256']==reference['prediction_sha256']
            step=time.monotonic();m,f=read(prepared/'csr',inputs['rr_graph']['sha256']);occ=json.loads((prediction/'prediction.json').read_text())['node_occupancy'];payload=out/(tag+'.pressure')
            rows=[(n,f['capacities'][n],1+max(0,occ.get(str(n),0)-f['capacities'][n])/f['capacities'][n]) for n in range(m['nodes']) if f['types'][n] in (4,5) and f['capacities'][n]>0 and occ.get(str(n),0)>f['capacities'][n]]
            payload.write_text(f"ROUTECAST_PRESSURE_V1 {m['nodes']} {inputs['rr_graph']['sha256']}\n"+''.join(f'{n} {cap} {v:.9g}\n' for n,cap,v in rows));nodes=len(rows);env['ROUTECAST_PRESSURE_FILE']=str(payload.resolve());env['ROUTECAST_EXPECT_GRAPH_SHA256']=inputs['rr_graph']['sha256'];payload_s=time.monotonic()-step
        command=[str(binary),inputs['architecture']['path'],'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',inputs['rr_graph']['path'],'--route_chan_width','300','--num_workers','1','--seed','1','--max_router_iterations','100']
        (out/(tag+'_command.json')).write_text(json.dumps({'command':command,'cwd':str(wd.resolve())},indent=2)+'\n');step=time.monotonic()
        with (out/(tag+'.log')).open('w') as log:code=subprocess.run(command,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
        native_s=time.monotonic()-step;total_s=time.monotonic()-start;assert code==0
        text=(out/(tag+'.log')).read_text();assert 'VPR succeeded' in text
        assert ('RouteCast pressure applied' in text)==(mode=='on')
        if mode=='on':assert f'RouteCast pressure applied: {nodes} channel nodes' in text
        row={'run':i,'mode':mode,'estimator_s':estimator_s,'payload_s':payload_s,'native_route_s':native_s,'cached_pipeline_s':total_s,'pressure_nodes':nodes,'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1]),'wirelength':int(re.search(r'Total wirelength:\s*(\d+)',text)[1]),'route_sha256':sha(wd/'design.route'),'log_sha256':sha(out/(tag+'.log'))};results.append(row);print(json.dumps(row),flush=True)
    assert all(sha(v['path'])==v['sha256'] for v in inputs.values()) and all(sha(Path('tools')/n)==h for n,h in sources.items())
    groups={mode:[r for r in results if r['mode']==mode] for mode in ('off','on')}
    for rows in groups.values():assert len({r['route_sha256'] for r in rows})==1 and len({(r['cpd_ns'],r['wirelength']) for r in rows})==1
    means={mode:sum(r['cached_pipeline_s'] for r in rows)/len(rows) for mode,rows in groups.items()}
    receipt={'protocol_sha256':sha(out/'protocol.json'),'results':results,'mean_cached_pipeline_s':means,'cached_off_over_on_ratio':means['off']/means['on'],'within_mode_route_byte_repeatable':True,'scope':protocol['scope'],'cold_pipeline_measured':False,'unseen_family_claim':False}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ('mean_cached_pipeline_s','cached_off_over_on_ratio')}),flush=True)


if __name__=='__main__':main()
