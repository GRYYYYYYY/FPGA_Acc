"""Post-hoc frozen-map diagnostics; never change primary metric or model."""
import json
import shutil
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha


def boundary(values,k):
    ordered=sorted(values,key=lambda key:(-values[key],key));chosen=ordered[:k]
    cutoff=values[chosen[-1]]
    strict={key for key in values if values[key]>cutoff}
    tied={key for key in values if values[key]==cutoff}
    return chosen,strict,tied,cutoff


def rank_interval(values,key):
    value=values[key]
    greater=sum(v>value for v in values.values());equal=sum(v==value for v in values.values())
    return [greater+1,greater+equal]


def main():
    base=Path('experiments');comparison=base/'adder_tree_family_model_comparison_2026-10-06'
    receipt=json.loads((comparison/'receipt.json').read_text());assert sha(comparison/'report.json')==receipt['report_sha256']
    summary=json.loads((comparison/'report.json').read_text());assert receipt['complete_fixed_cohort']
    out=base/'adder_tree_family_hotspot_diagnosis_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
    inputs={str(comparison/'report.json'):sha(comparison/'report.json')};records=[]
    for design in summary['cohort']:
        for model in ('sparse_reset','bbox3'):
            folder=base/'adder_tree_family_evaluation_2026-10-06'/design/model
            er=json.loads((folder/'receipt.json').read_text());assert sha(folder/'protocol.json')==er['protocol_sha256']
            maps=folder/'spatial_maps.json';assert sha(maps)==er['spatial_maps_sha256']
            inputs[str(maps)]=sha(maps);inputs[str(folder/'receipt.json')]=sha(folder/'receipt.json')
            data=json.loads(maps.read_text());p=data['prediction'];t=data['native'];assert set(p)==set(t)
            k=er['reports']['spatial']['k'];pt,ps,pe,pc=boundary(p,k);tt,ts,te,tc=boundary(t,k)
            assert len(set(pt)&set(tt))/k==er['reports']['spatial']['precision_at_k']
            allowed_overlap=(ps|pe)&(ts|te)
            truth_rows=[{'id':key,'native':t[key],'predicted':p[key],'prediction_rank_interval':rank_interval(p,key)} for key in tt]
            pred_rows=[{'id':key,'predicted':p[key],'native':t[key],'native_rank_interval':rank_interval(t,key)} for key in pt]
            def centroid(keys,values):
                weight=sum(values[key] for key in keys)
                assert weight>0
                return [sum(int(key.split(',')[axis])*values[key] for key in keys)/weight for axis in (0,1)]
            result={'design':design,'model':model,'k':k,'deterministic_hits':len(set(pt)&set(tt)),
                    'prediction_boundary':{'score':pc,'strict_count':len(ps),'tied_count':len(pe)},
                    'native_boundary':{'score':tc,'strict_count':len(ts),'tied_count':len(te)},
                    'any_hit_possible_by_boundary_tie_reordering':bool(allowed_overlap),
                    'shared_allowed_top_k_ids':sorted(allowed_overlap),
                    'native_top_rows':truth_rows,'prediction_top_rows':pred_rows,
                    'top_weighted_centroids':{'prediction':centroid(pt,p),'native':centroid(tt,t)},
                    'native_top_axis_segment_counts':dict(Counter(','.join(key.split(',')[2:]) for key in tt)),
                    'prediction_top_axis_segment_counts':dict(Counter(','.join(key.split(',')[2:]) for key in pt))}
            records.append(result)
    assert all(sha(path)==h for path,h in inputs.items())
    report={'inputs_sha256':inputs,'source_sha256':sha(__file__),'records':records,
            'scope':'post-hoc descriptive mismatch diagnosis from authenticated maps; primary k/tie/model unchanged',
            'limitations':['centroid shift is not a causal explanation','tie support intersection only tests possibility of any hit, not maximum/minimum overlap','native labels reserved for diagnosis, not predictor tuning or unseen proof']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'records':len(records),'primary_metric_unchanged':True},indent=2)+'\n')
    print(json.dumps([{'design':r['design'],'model':r['model'],'hits':r['deterministic_hits'],'any_tie_hit_possible':r['any_hit_possible_by_boundary_tie_reordering'],'native_top_prediction_rank_min':min(v['prediction_rank_interval'][0] for v in r['native_top_rows']),'centroids':r['top_weighted_centroids']} for r in records]),flush=True)


if __name__=='__main__':main()
