"""Post-label full-domain hotspot/tie diagnosis; frozen primary metrics stay intact."""
from collections import defaultdict
import json
from pathlib import Path
import resource
import sys
import time
from xml.parsers import expat

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare


def tie_diagnosis(p,t,k):
    ordered=sorted(t,key=lambda n:(-t[n],n));cut=t[ordered[k-1]]
    selected=set(sorted(p,key=lambda n:(-p[n],n))[:k])
    strict={n for n in t if t[n]>cut};tied={n for n in t if t[n]==cut}
    slots=k-len(strict);fixed=len(selected&strict);eligible=len(selected&tied)
    return dict(truth_boundary=cut,strictly_above_boundary=len(strict),truth_boundary_ties=len(tied),
                slots_at_boundary=slots,selected_predicted_resources_on_truth_boundary=eligible,
                fixed_predicted_selection_precision_min_over_truth_ties=(fixed+max(0,slots-(len(tied)-eligible)))/k,
                fixed_predicted_selection_precision_max_over_truth_ties=(fixed+min(slots,eligible))/k,
                predicted_top_k_positive_truth_fraction=sum(t[n]>0 for n in selected)/k,
                scope='Descriptive sensitivity to truth tie selection with fixed predicted top-k. Primary preregistered lexical tie rule is unchanged; not a replacement metric.')


def main():
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));tick=time.perf_counter()
    out=R/'experiments/neuron_certified_native_metrics_v1_2026-10-15'
    primary=json.loads((out/'prediction_metrics.json').read_text());assert json.loads((out/'label_admission.json').read_text())['label_accepted']
    for p,h in primary['bindings'].items():assert sha(p)==h,p
    model=R/'experiments/titan23_neuron_compact_wide_retained_pipeline_v3_2026-10-13/model'
    pv=[]
    for name in ['initial','sketch']:
        d=json.loads((model/(name+'.json')).read_text());pv.append(d['ledger'])
    truth=json.loads((R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15/physical_audit.json').read_text())['node_occupancy']
    command=json.loads((R/'experiments/titan23_neuron_native_label_prereg_v2_2026-10-13/protocol.json').read_text())['native_command']
    graph=Path(command[command.index('--read_rr_graph')+1])
    # Accumulate all three integer occupancy vectors and complete capacities in
    # one separate Expat pass, stopping only after the full original rr_nodes.
    capacity=defaultdict(int);sp=[defaultdict(int),defaultdict(int),defaultdict(int)]
    cp=[{},{}];ct={};overflow_channels=defaultdict(int);stack=[];node=[None]
    class Finished(Exception):pass
    def start(tag,a):
        parent=stack[-1] if stack else None
        if tag=='node' and parent=='rr_nodes':node[0]=dict(a)
        if parent=='node' and tag in ['loc','segment']:node[0][tag]=dict(a)
        stack.append(tag)
    def end(tag):
        parent=stack[-2] if len(stack)>1 else None
        if tag=='node' and parent=='rr_nodes':
            n=node[0];kind=n['type'];cap=int(n['capacity'])
            if kind in ['CHANX','CHANY'] and cap>0:
                nid=n['id'];a=pv[0].get(nid,0);b=pv[1].get(nid,0);t=truth.get(nid,0)
                cp[0][nid]=a/cap;cp[1][nid]=b/cap;ct[nid]=t/cap
                loc=n['loc'];seg=n['segment']['segment_id'];layer=loc.get('layer','0')
                for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
                    for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
                        key=f'{layer},{x},{y},{kind},{seg}'
                        capacity[key]+=cap;sp[0][key]+=a;sp[1][key]+=b;sp[2][key]+=t
                        overflow_channels[key]+=b>cap
        assert stack.pop()==tag
        if tag=='rr_nodes':raise Finished()
    parser=expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
    with graph.open('rb') as f:
        try:parser.ParseFile(f)
        except Finished:pass
    bins=[{k:s[k]/c for k,c in capacity.items()} for s in sp]
    replay={};ties={}
    for i,name in enumerate(['initial','sketch']):
        k=primary['metrics'][name]['concrete']['k']
        replay[name]=dict(concrete=compare(cp[i],ct,k),spatial=compare(bins[i],bins[2],20))
        assert replay[name]['concrete']==primary['metrics'][name]['concrete']
        assert replay[name]['spatial']==primary['metrics'][name]['spatial']
        ties[name]=dict(concrete=tie_diagnosis(cp[i],ct,k),spatial=tie_diagnosis(bins[i],bins[2],20))
    predicted=sorted(capacity,key=lambda k:(-bins[1][k],k))[:20]
    actual=sorted(capacity,key=lambda k:(-bins[2][k],k))[:20]
    def row(k):return dict(bin=k,capacity=capacity[k],initial_utilization=bins[0][k],
                          sketch_utilization=bins[1][k],native_utilization=bins[2][k],
                          over_capacity_sketch_channels=overflow_channels[k])
    result=dict(bindings={**closure([Path(__file__)]),**{str(p):sha(p) for p in [out/'prediction_metrics.json',out/'label_admission.json',graph]}},
                all_primary_metrics_exactly_reproduced_by_independent_Expat_domain=True,
                primary_metrics_unchanged=True,post_label_diagnostic=True,
                complete_channel_universe=len(ct),complete_spatial_universe=len(capacity),ties=ties,
                sketch_top20=[row(k) for k in predicted],native_top20=[row(k) for k in actual],
                sketch_top20_native_top20_overlap=len(set(predicted)&set(actual)),
                sketch_top20_predicted_over_capacity=sum(bins[1][k]>1 for k in predicted),
                sketch_top20_above_or_equal_truth_boundary=sum(bins[2][k]>=bins[2][actual[-1]] for k in predicted),
                seconds=time.perf_counter()-tick,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='Complete-domain exact primary-metric reproduction plus post-label hotspot/tie explanation. No primary tie/threshold change, new candidate selection, heldout or performance benefit.')
    for p,h in result['bindings'].items():assert sha(p)==h,p
    with (out/'hotspot_diagnosis.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','sketch_top20','native_top20')},indent=2),flush=True)


if __name__=='__main__':main()
