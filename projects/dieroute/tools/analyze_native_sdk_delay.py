#!/usr/bin/env python3
"""Evaluate SDK helper components and grouped affine fits, never routing decisions."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import shutil
from analyze_native_delay_features import CORNERS,fold_for,metrics,predict,ridge_fit
from analyze_native_path_model_limits import directed_path
from audit_native_timing_feedback import read_state
from run_native_case import sha256


def main():
    if not __debug__:raise RuntimeError('analysis requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('node-run','feature-audit','feedback-run','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();node_run=a.node_run.resolve();feature=a.feature_audit.resolve();feedback=a.feedback_run.resolve()
    nm=json.loads((node_run/'manifest.json').read_text());am=json.loads((feature/'audit.json').read_text())
    fm=json.loads((feedback/'manifest.json').read_text())
    assert nm['status']=='passed' and nm['inputs_unchanged'] and nm['sdk_unchanged']
    assert am['status']=='analyzed' and am['inputs_unchanged']
    assert nm['inputs'][str(feedback/'manifest.json')]==am['inputs'][str(feedback/'manifest.json')]==sha256(feedback/'manifest.json')
    inputs={}
    def add(path,value):
        path=str(Path(path).resolve());assert path not in inputs or inputs[path]==value
        inputs[path]=value
    for directory,record,name in ((node_run,nm,'manifest.json'),(feature,am,'audit.json')):
        add(directory/name,sha256(directory/name))
        for path,value in {**record['inputs'],**record.get('sdk',{})}.items():add(path,value)
        for rel,value in record['artifacts'].items():add(directory/rel,value)
    for path,value in inputs.items():assert sha256(path)==value,path
    expected={int(r['node']):r for r in csv.DictReader((node_run/'nodes.tsv').open(),delimiter='\t')}
    raw=list(csv.DictReader((node_run/'export/node_delays.tsv').open(),delimiter='\t'))
    nodes={int(r['node']):r for r in raw};assert len(nodes)==len(raw)==nm['nodes'] and nodes.keys()==expected.keys()
    for n,r in nodes.items():
        assert all(r[k]==expected[n][k] for k in ('node','tile','wire','membership'))
        assert r['exit_node'] in ('true','false') and r['long_node'] in ('true','false')
        assert r['status'] in ('resolved','helper_zero_unmodeled','uturn_penalty','unsupported')
        if r['status']!='unsupported':
            assert int(r['helper_delay_ps'])>=0
            assert int(r['extra_if_long_parent_ps'])==(45 if r['long_node']=='true' else 0)
        if r['status']=='helper_zero_unmodeled':assert r['exit_node']=='false' and r['helper_delay_ps']=='0'
    trees={label:read_state(feedback/'prepared'/state)[0] for label,state in (('original','baseline'),('proposal','proposal'))}
    route=Path(next(s for s in fm['steps'] if s['name']=='prepared')['command'][6])
    assert inputs[str(route/'selection.csv')]==fm['inputs'][str(route/'selection.csv')]
    tasks={int(r['task']):{k:int(v) for k,v in r.items()} for r in csv.DictReader((route/'selection.csv').open())}
    dataset=json.loads((feature/'dataset.json').read_text());records=[]
    for sample in dataset:
        net=sample['net'];task=tasks[sample['task']];assert task['net']==net
        tree=trees[sample['stages'][0]][net]
        identity=hashlib.sha256(json.dumps(sorted(tree.items()),separators=(',',':')).encode()).hexdigest()
        assert identity==sample['tree_sha256'] and sample['fold']==fold_for(net)
        path=directed_path(tree,task['source'],task['sink'])
        status=Counter(nodes[dst]['status'] for src,dst,key in path)
        usable=not(status['unsupported'] or status['uturn_penalty'])
        nominal=sum(int(nodes[dst]['helper_delay_ps'])+(int(nodes[dst]['extra_if_long_parent_ps']) if nodes[src]['long_node']=='true' else 0)
                    for src,dst,key in path) if usable else None
        sll=sum(int(nodes[dst]['membership']).bit_count()>1 for src,dst,key in path)
        records.append({**{k:sample[k] for k in ('net','task','to_pin','tree_sha256','stages','fold','observed_ps')},
                        'sdk_helper_sum_ps':nominal,'multi_slr_nodes':sll,'node_status_counts':dict(status)})
    eligible=[r for r in records if r['sdk_helper_sum_ps'] is not None]
    assert eligible
    predictions=[];models={};splits=[]
    def add_predictions(name,r,values):
        for k,corner in enumerate(CORNERS):
            predictions.append(dict(model=name,fold=r['fold'],net=r['net'],task=r['task'],to_pin=r['to_pin'],tree_sha256=r['tree_sha256'],
                                    corner=corner,observed_ps=r['observed_ps'][k],prediction_ps=values[k]))
    for r in eligible:add_predictions('raw_sdk_helper',r,[r['sdk_helper_sum_ps']]*4)
    for fold in range(5):
        train=[r for r in eligible if r['fold']!=fold];test=[r for r in eligible if r['fold']==fold]
        assert train and test and not {r['net'] for r in train}&{r['net'] for r in test}
        splits.append(dict(fold=fold,training_nets=sorted({r['net'] for r in train}),validation_nets=sorted({r['net'] for r in test}),training_rows=len(train),validation_rows=len(test)))
        for name,fields in (('affine_sdk',('sdk_helper_sum_ps',)),('affine_sdk_sll',('sdk_helper_sum_ps','multi_slr_nodes'))):
            fitted=ridge_fit([[r[f] for f in fields] for r in train],[r['observed_ps'] for r in train],1.0)
            models[f'{name}_{fold}']=dict(features=fields,**fitted)
            for r in test:add_predictions(name,r,predict(fitted,[r[f] for f in fields]))
    results={name:{corner:metrics([r for r in predictions if r['model']==name and r['corner']==corner]) for corner in CORNERS}
             for name in ('raw_sdk_helper','affine_sdk','affine_sdk_sll')}
    for path,value in inputs.items():assert sha256(path)==value,path
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'analyzer.py')
    for name,value in (('dataset.json',records),('models.json',models),('folds.json',splits)):(out/name).write_text(json.dumps(value,indent=2)+'\n')
    with (out/'predictions.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(predictions[0]));w.writeheader();w.writerows(predictions)
    result=dict(schema='dieroute.native_sdk_delay_diagnostic.v1',status='analyzed',inputs=inputs,inputs_unchanged=True,
                nodes=len(nodes),node_status_counts=dict(Counter(r['status'] for r in nodes.values())),
                multi_slr_node_status_counts=dict(Counter(r['status'] for r in nodes.values() if int(r['membership']).bit_count()>1)),
                tree_load_rows=len(records),eligible_rows=len(eligible),excluded_rows=len(records)-len(eligible),
                results=results,policy=dict(ridge_penalty=1.0,folds=5,whole_net_split=True,weighting='equal unique tree/load rows'),
                artifacts={p.name:sha256(p) for p in out.iterdir() if p.is_file()},board_result=False,routing_cost_ready=False,
                limits=['The raw helper sum is a component approximation, not a complete RWRoute timing model or a process-corner estimate.',
                        'Helper zeros, including cross-SLR resources, do not assert physical zero delay. U-turn penalties and unsupported nodes are explicitly excluded from numeric fits.',
                        'Exploratory grouped validation uses the same previously studied single-design development cohort; no independent held-out performance claim.',
                        'Affine fits lack complete branch-loading, buffering and site models, guaranteed error bounds, timing acceptance and joint route QoR.'])
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','nodes','node_status_counts','multi_slr_node_status_counts','eligible_rows','excluded_rows','results')}))


if __name__=='__main__':main()
