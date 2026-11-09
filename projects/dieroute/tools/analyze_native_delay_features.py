#!/usr/bin/env python3
"""Development-only grouped prediction diagnostic; never supplies routing costs.

No-op and repaired observations are controls, not additional training samples.
The entire net is assigned to one fold across all routes and logical loads.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
import mmap
from pathlib import Path
import shutil
import struct
from analyze_native_path_model_limits import directed_path
from audit_native_timing_feedback import read_state
from run_native_case import sha256

CORNERS=('FAST_MIN','FAST_MAX','SLOW_MIN','SLOW_MAX')


def fold_for(net):
    return int(hashlib.sha256(f'dieroute.delay.dev.v1:{net}'.encode()).hexdigest(),16)%5


def ridge_fit(x,y,penalty=1.0):
    """Training-only normalization, unpenalized intercept, Cholesky solve."""
    assert x and len(x)==len(y) and penalty>0
    n=len(x);width=len(x[0]);outputs=len(y[0])
    assert width and outputs and all(len(r)==width for r in x) and all(len(r)==outputs for r in y)
    assert all(math.isfinite(v) for row in x+y for v in row)
    means=[sum(row[j] for row in x)/n for j in range(width)]
    scales=[math.sqrt(sum((row[j]-means[j])**2 for row in x)/n) or 1.0 for j in range(width)]
    z=[[1.0]+[(v-m)/s for v,m,s in zip(row,means,scales)] for row in x]
    p=width+1;gram=[[0.0]*p for _ in range(p)];rhs=[[0.0]*outputs for _ in range(p)]
    for row,target in zip(z,y):
        for i,v in enumerate(row):
            for j in range(i+1):gram[i][j]+=v*row[j]
            for k,t in enumerate(target):rhs[i][k]+=v*t
    for i in range(1,p):gram[i][i]+=penalty
    lower=[[0.0]*p for _ in range(p)]
    for i in range(p):
        for j in range(i+1):
            value=gram[i][j]-sum(lower[i][k]*lower[j][k] for k in range(j))
            if i==j:
                assert value>0 and math.isfinite(value)
                lower[i][j]=math.sqrt(value)
            else:lower[i][j]=value/lower[j][j]
    coefficients=[[0.0]*outputs for _ in range(p)]
    for k in range(outputs):
        forward=[]
        for i in range(p):forward.append((rhs[i][k]-sum(lower[i][j]*forward[j] for j in range(i)))/lower[i][i])
        for i in range(p-1,-1,-1):
            coefficients[i][k]=(forward[i]-sum(lower[j][i]*coefficients[j][k] for j in range(i+1,p)))/lower[i][i]
    return dict(means=means,scales=scales,coefficients=coefficients,penalty=penalty,training_rows=n)


def predict(model,row):
    assert len(row)==len(model['means'])
    z=[1.0]+[(v-m)/s for v,m,s in zip(row,model['means'],model['scales'])]
    return [sum(z[i]*model['coefficients'][i][k] for i in range(len(z))) for k in range(len(model['coefficients'][0]))]


def metrics(rows):
    errors=[r['prediction_ps']-r['observed_ps'] for r in rows];absolute=sorted(abs(v) for v in errors)
    nets=defaultdict(list)
    for r,e in zip(rows,errors):nets[r['net']].append(abs(e))
    return dict(rows=len(rows),nets=len(nets),mae_ps=sum(absolute)/len(rows),
                net_macro_mae_ps=sum(sum(v)/len(v) for v in nets.values())/len(nets),
                rmse_ps=math.sqrt(sum(e*e for e in errors)/len(rows)),
                p95_absolute_error_ps=absolute[math.ceil(.95*len(rows))-1],maximum_absolute_error_ps=absolute[-1],
                minimum_signed_error_ps=min(errors),maximum_signed_error_ps=max(errors),
                negative_predictions=sum(r['prediction_ps']<0 for r in rows))


def main():
    if not __debug__:raise RuntimeError('analysis requires assertions')
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('control-audit','feedback-run','mapping-audit','output'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();control=a.control_audit.resolve();feedback=a.feedback_run.resolve();mapping=a.mapping_audit.resolve()
    cm=json.loads((control/'audit.json').read_text());fm=json.loads((feedback/'manifest.json').read_text())
    mm=json.loads((mapping/'audit.json').read_text())
    assert cm['schema']=='dieroute.native_delay_control_audit.v2' and cm['inputs_unchanged'] and mm['passed']
    assert cm['inputs'][str(feedback/'manifest.json')]==sha256(feedback/'manifest.json')
    assert fm['context']['mapping_audit_sha256']==sha256(mapping/'audit.json')
    inputs=dict(cm['inputs']);inputs[str(control/'audit.json')]=sha256(control/'audit.json')
    for name,digest in cm['artifacts'].items():inputs[str(control/name)]=digest
    inputs[str(mapping/'audit.json')]=sha256(mapping/'audit.json')
    inputs[str(mapping/'mapping.json')]=mm['artifacts']['mapping.json']
    prepared=next(step for step in fm['steps'] if step['name']=='prepared')['command']
    graph=Path(prepared[1]);selection=Path(prepared[6])/'selection.csv'
    inputs[str(graph/'nodes.bin')]=fm['inputs'][str(graph/'nodes.bin')]
    inputs[str(selection)]=fm['inputs'][str(selection)]
    graph_manifest=graph.parent/'manifest.json';inputs[str(graph_manifest)]=fm['inputs'][str(graph_manifest)]
    gm=json.loads(graph_manifest.read_text());inputs[str(graph/'intents.csv')]=gm['artifacts']['graph/intents.csv']
    for path,digest in inputs.items():assert sha256(path)==digest,path
    trees={label:read_state(feedback/'prepared'/state)[0] for label,state in (('original','baseline'),('proposal','proposal'))}
    tasks={int(r['task']):{k:int(v) for k,v in r.items()} for r in csv.DictReader(selection.open())}
    loads=[r for r in json.loads((mapping/'mapping.json').read_text()) if r['task'] is not None]
    assert {r['task'] for r in loads}==tasks.keys()
    delays={(int(r['net_id']),r['to_pin']):r for r in csv.DictReader((control/'four_stage_delays.csv').open()) if r['mode']=='interconnect'}
    intents=[int(r['id']) for r in csv.DictReader((graph/'intents.csv').open())]
    assert len(set(intents))==len(intents)
    basic=['hops','node_span_x','node_span_y','multi_slr_nodes']
    path_features=['path_'+n for n in basic]+['path_intent_'+str(i) for i in intents]
    tree_features=path_features+['tree_'+n for n in basic]+['tree_intent_'+str(i) for i in intents]+[
        'tree_branch_nodes','tree_leaves','tree_physical_loads','path_off_path_descendants']
    with (graph/'nodes.bin').open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as raw:
        assert len(raw)%64==0
        def node(n):
            r=struct.unpack_from('<16I',raw,n*64);assert r[0]==n and r[7] in intents
            assert r[11]>=r[9] and r[12]>=r[10]
            return r
        def aggregate(nodes):
            records=[node(n) for n in nodes];counts=Counter(r[7] for r in records)
            return [len(records),sum(r[11]-r[9] for r in records),sum(r[12]-r[10] for r in records),
                    sum(r[5].bit_count()>1 for r in records)]+[counts[i] for i in intents]
        records=[];seen={};tree_cache={}
        for label in ('original','proposal'):
            for load in loads:
                net=load['net_id'];task=tasks[load['task']];tree=trees[label][net]
                assert task['net']==net
                key=(label,net)
                if key not in tree_cache:
                    canonical=json.dumps(sorted(tree.items()),separators=(',',':'))
                    identity=hashlib.sha256(canonical.encode()).hexdigest()
                    children=Counter(v[0] for n,v in tree.items() if n!=task['source'])
                    descendants={n:0 for n in tree}
                    for n,v in sorted(tree.items(),key=lambda x:x[1][2],reverse=True):
                        if n!=task['source']:descendants[v[0]]+=1+descendants[n]
                    tree_cache[key]=(identity,aggregate(n for n in tree if n!=task['source']),children,descendants)
                identity,tree_values,children,descendants=tree_cache[key]
                unique=(net,identity,load['to_pin']);target=[int(delays[net,load['to_pin']][f'{label}_{corner}_ps']) for corner in CORNERS]
                if unique in seen:
                    assert seen[unique]['observed_ps']==target
                    seen[unique]['stages'].append(label);continue
                path=directed_path(tree,task['source'],task['sink']);vertices=[task['source']]+[e[1] for e in path]
                off_path=sum(descendants[n]-(len(vertices)-i-1) for i,n in enumerate(vertices))
                assert off_path>=0
                values=aggregate(e[1] for e in path)+tree_values+[
                    sum(v>1 for v in children.values()),sum(n not in children for n in tree),
                    len({t['sink'] for t in tasks.values() if t['net']==net}),off_path]
                assert len(values)==len(tree_features)
                record=dict(net=net,task=load['task'],to_pin=load['to_pin'],tree_sha256=identity,stages=[label],
                            fold=fold_for(net),features=values,observed_ps=target)
                records.append(record);seen[unique]=record
    models={};predictions=[];folds=[]
    for fold in range(5):
        train=[r for r in records if r['fold']!=fold];test=[r for r in records if r['fold']==fold]
        train_nets={r['net'] for r in train};test_nets={r['net'] for r in test}
        assert train and test and not train_nets&test_nets
        ranges=[]
        for j,feature in enumerate(tree_features):
            low=min(r['features'][j] for r in train);high=max(r['features'][j] for r in train)
            outside=[r for r in test if not low<=r['features'][j]<=high]
            ranges.append(dict(feature=feature,training_minimum=low,training_maximum=high,
                               validation_rows_outside=len(outside),validation_nets_outside=sorted({r['net'] for r in outside})))
        folds.append(dict(fold=fold,training_nets=sorted(train_nets),validation_nets=sorted(test_nets),
                          training_rows=len(train),validation_rows=len(test),feature_ranges=ranges))
        for name,width in (('path',len(path_features)),('tree',len(tree_features))):
            fitted=ridge_fit([r['features'][:width] for r in train],[r['observed_ps'] for r in train]);models[f'{name}_{fold}']=fitted
            for r in test:
                values=predict(fitted,r['features'][:width]);assert all(math.isfinite(v) for v in values)
                for k,corner in enumerate(CORNERS):
                    predictions.append(dict(model=name,fold=fold,net=r['net'],task=r['task'],to_pin=r['to_pin'],tree_sha256=r['tree_sha256'],
                                            corner=corner,observed_ps=r['observed_ps'][k],prediction_ps=values[k]))
    results={name:{corner:metrics([r for r in predictions if r['model']==name and r['corner']==corner]) for corner in CORNERS} for name in ('path','tree')}
    by_net={name:{str(net):{corner:metrics([r for r in predictions if r['model']==name and r['corner']==corner and r['net']==net])
                          for corner in CORNERS} for net in sorted({r['net'] for r in records})} for name in ('path','tree')}
    inversions={}
    for name in ('path','tree'):
        groups=defaultdict(dict)
        for r in predictions:
            if r['model']==name:groups[r['net'],r['tree_sha256'],r['to_pin']][r['corner']]=r['prediction_ps']
        inversions[name]={corner:sum(v[corner+'_MIN']>v[corner+'_MAX'] for v in groups.values()) for corner in ('FAST','SLOW')}
    for path,digest in inputs.items():assert sha256(path)==digest,path
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'analyzer.py')
    for name,value in (('dataset.json',records),('models.json',models),('folds.json',folds),('per_net_metrics.json',by_net)):
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    with (out/'predictions.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(predictions[0]));writer.writeheader();writer.writerows(predictions)
    result=dict(schema='dieroute.native_delay_feature_diagnostic.v1',status='analyzed',inputs=inputs,inputs_unchanged=True,
                physical_tasks=len(tasks),logical_loads=len(loads),unique_tree_load_rows=len(records),nets=len({r['net'] for r in records}),
                repeated_tree_load_rows_removed=2*len(loads)-len(records),features=dict(path=path_features,tree=tree_features),
                policy=dict(folds=5,fold_key='sha256(dieroute.delay.dev.v1:<net>) mod 5',ridge_penalty=1.0,weighting='equal unique tree/load rows',
                            normalization='training fold only',controls_used_for_fitting=False,predictions_clipped=False),
                results=results,predicted_corner_order_inversions=inversions,
                artifacts={p.name:sha256(p) for p in out.iterdir() if p.is_file()},board_result=False,routing_cost_ready=False,
                limits=['Development-only grouped cross-validation within one previously studied design and prefix-selected net cohort; not a representative held-out benchmark.',
                        'Tile spans, intent counts and descendant counts are features, not calibrated wire length, capacitance or an admissible search heuristic.',
                        'Site-internal load differences and buffering are not fully represented. No guaranteed timing-error bound, setup/hold acceptance or route QoR follows.',
                        'No-op and repaired snapshots provide controls only. Existing C++ routing and native acceptance are unchanged.'])
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','unique_tree_load_rows','nets','results','predicted_corner_order_inversions')}))


if __name__=='__main__':main()
