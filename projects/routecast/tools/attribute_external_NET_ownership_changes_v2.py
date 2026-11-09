"""Retrospective attribution on exposed cases; no candidate or threshold search."""
import json,xml.etree.ElementTree as ET
from array import array
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    decision=D/'research_decision_v1.json';assert read(decision)['status']=='FIXED_SUPPLEMENTARY_STUDY_COMPLETE_QUALITY_AND_UTILITY_FAILED_NOT_PROMOTED'
    out=R/'experiments/prospective_external_family_NET_attribution_v2_2026-10-19';out.mkdir(exist_ok=False)
    spec=read(D/'specifications/w160/episode_01/comparison_spec.json');ep=read(spec['endpoint']);graph=Path(ep['inputs']['graph']['path']);domain=Path(spec['domain_proof']);dp=read(domain);channels={r['id']:r['capacity'] for r in map(json.loads,(domain.parent/'resources.jsonl').read_text().splitlines())};assert set(channels.values())=={1}
    dest=array('I');stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='edge' and parent=='rr_edges':dest.append(int(e.get('sink_node')))
        if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
        stack.pop()
    bindings={str(p):sha(p) for p in [decision,graph,domain,domain.parent/'resources.jsonl',Path(__file__).resolve()]};bindings.update(dp['bindings']);rows=[]
    def frame(path):
        path=Path(path);f=read(path);bindings[str(path)]=sha(path);assert f['graph_sha256']==ep['graph_sha256'];groups=defaultdict(set)
        for rec in f['records']:
            used=groups[rec['net_id']]
            if rec['source'] in channels:used.add(rec['source'])
            for eid in rec['answer']['physical_edge_ids']:
                n=dest[eid]
                if n in channels:used.add(n)
        ledger=Counter(n for ns in groups.values() for n in ns);assert dict(ledger)=={int(n):v for n,v in f['ledger'].items() if int(n) in channels}
        return dict(groups),ledger
    source,sl=frame(spec['source_frame']);nets=set(source)
    def ledger(groups):return Counter(n for ns in groups.values() for n in ns)
    def error(counts,truth):return sum(abs(counts[n]-truth[n]) for n in channels)
    for episode in range(1,4):
        case=f'w160/episode_{episode:02d}';spec_path=D/'specifications'/case/'comparison_spec.json';s=read(spec_path);comparison=read(D/'predictions'/case/'comparison.json');current=read(s['endpoint']);assert current['graph_sha256']==ep['graph_sha256']
        warm_dir=D/'predictions'/case/'warm/native_retained';warm,wl=frame(warm_dir/'initial.json');final,fl=frame(s['predictions']['native_retained_on']['frame']);wp=read(warm_dir/'verification.json');dirty=set(wp['dirty_nets'])
        truth={net:set() for net in nets};byname={current['net_names'][str(net)]:net for net in nets};route=Path(s['label_physical_audit']).parent/'output.route';net=None
        for line in route.read_text().splitlines():
            match=NET.match(line)
            if match:net=byname.get(match[2])
            node=NODE.match(line)
            if node and int(node[1]) in channels:
                assert net is not None;truth[net].add(int(node[1]))
        tl=ledger(truth);physical=read(s['label_physical_audit']);assert dict(tl)=={int(n):v for n,v in physical['node_occupancy'].items() if int(n) in channels};assert set(warm)==set(final)==nets
        detail=[];groups={}
        for flag in (False,True):
            selected={n for n in nets if (n in dirty)==flag};name='endpoint_dirty' if flag else 'endpoint_clean';changes=Counter();ownership_delta=0
            for net in sorted(selected):
                a,b,c,t=source[net],warm[net],final[net],truth[net]
                if not flag:assert a==b
                rec=dict(net_id=net,dirty=flag,source_CHANNELs=len(a),warm_CHANNELs=len(b),final_CHANNELs=len(c),target_CHANNELs=len(t),warm_changed_from_source=a!=b,feedback_changed_from_warm=b!=c,final_changed_from_source=a!=c,target_changed_from_source=a!=t,owner_error_source=len(a^t),owner_error_warm=len(b^t),owner_error_final=len(c^t))
                detail.append(rec)
                for key in ('warm_changed_from_source','feedback_changed_from_warm','final_changed_from_source','target_changed_from_source'):changes[key]+=rec[key]
                ownership_delta+=len(c^t)-len(a^t)
            groups[name]=dict(NETs=len(selected),**changes,additive_NET_CHANNEL_ownership_error_final_minus_source=ownership_delta)
        hybrid={n:final[n] if n in dirty else source[n] for n in nets};hl=ledger(hybrid)
        # Explicit density counterfactual for attribution, not a new model/route.
        k=dp['resource_k'];ids=sorted(channels);tops={name:set(sorted(ids,key=lambda n:(-counts[n],n))[:k]) for name,counts in [('source',sl),('warm',wl),('final',fl),('truth',tl)]};target=tops['truth'];entered=tops['final']-tops['source'];left=tops['source']-tops['final'];hit_delta=len(entered&target)-len(left&target)
        assert hit_delta==comparison['metrics']['native_retained_on']['resource']['top_k_hits']-comparison['metrics']['previous_native']['resource']['top_k_hits']
        owner_errors={state:sum(len(states[n]^truth[n]) for n in nets) for state,states in [('source',source),('warm',warm),('final',final)]}
        agg_errors={'source':error(sl,tl),'warm':error(wl,tl),'final':error(fl,tl)}
        cancellation={name:owner_errors[name]-agg_errors[name] for name in owner_errors}
        assert all(v>=0 for v in cancellation.values())
        stages=[]
        for before,after in [('source','warm'),('warm','final')]:
            added=tops[after]-tops[before];removed=tops[before]-tops[after]
            stages.append(dict(before=before,after=after,entered=len(added),left=len(removed),entered_truth_topK=len(added&target),left_truth_topK=len(removed&target),hit_delta=len(added&target)-len(removed&target)))
        assert sum(x['hit_delta'] for x in stages)==hit_delta
        overused={n for n in channels if fl[n]>channels[n]}
        row=dict(case=case,aggregate_vs_owner_error=dict(owner_L1=owner_errors,aggregate_L1=agg_errors,crossNET_cancellation=cancellation,owner_delta=owner_errors['final']-owner_errors['source'],aggregate_delta=agg_errors['final']-agg_errors['source'],cancellation_delta=cancellation['final']-cancellation['source']),topK_stage_changes=stages,entered_final_overused=len(entered&overused),entered_final_not_overused=len(entered-overused),groups=groups,aggregate_CHANNEL_L1={'source':error(sl,tl),'warm':error(wl,tl),'final':error(fl,tl),'density_only_final_dirty_plus_source_clean':error(hl,tl)},topK=dict(k=k,entered=len(entered),left=len(left),entered_truth_topK=len(entered&target),left_truth_topK=len(left&target),net_hit_delta=hit_delta,final_overused_resources=sum(fl[n]>channels[n] for n in channels),final_overused_in_topK=sum(fl[n]>channels[n] for n in tops['final']),source_hits=len(tops['source']&target),final_hits=len(tops['final']&target)))
        detail_file=out/f'episode_{episode:02d}_NETs.json';detail_file.write_text(json.dumps(sorted(detail,key=lambda x:x['net_id']),separators=(',',':'))+'\n');bindings[str(detail_file)]=sha(detail_file)
        for p in [spec_path,Path(s['endpoint']),warm_dir/'verification.json',Path(s['predictions']['native_retained_on']['proof']),Path(s['label_proof']),route,D/'predictions'/case/'comparison.json']:bindings[str(p)]=sha(p)
        rows.append(row);print('NET_ATTRIBUTION',json.dumps(row),flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'verification.json').write_text(json.dumps(dict(status='ALL3_EXPOSED_CASE_SOURCE_WARM_FINAL_NATIVE_CHANNEL_OWNER_ATTRIBUTIONS_COMPLETE',bindings=bindings,rows=rows,scope='Retrospective diagnostic only. Additive perNET ownership error is distinct from aggregate occupancy error; density-only hybrid is an attribution counterfactual, not an executed model or joint legal route. No causal conclusion, gate replacement, candidate promotion or strict unseen evidence.'),indent=2)+'\n')
if __name__=='__main__':main()
