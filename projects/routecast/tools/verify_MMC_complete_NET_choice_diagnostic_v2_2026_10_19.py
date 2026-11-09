"""Independent cardinality/intersection choices, ownership and histogram metrics."""
import json,re,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from audit_native_route import NODE
from verify_MMC_complete_static_criticality_metrics_v2_2026_10_19 import verify_metric

R=Path(__file__).resolve().parents[1]


def main():
    root=R/'experiments/mmc_complete_NET_choice_diagnostic_v1_2026-10-19';rp=root/'results.json';result=json.loads(rp.read_text());assert all(sha(p)==h for p,h in result['bindings'].items())
    pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text())
    graph=Path(json.loads(Path(plan['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);dest=array('I');caps=array('I');channel={};bin_caps=Counter();stack=[];node=None
    def opening(tag,a):
        nonlocal node
        parent=stack[-1] if stack else None
        if tag=='node' and parent=='rr_nodes':node=dict(a);caps.append(int(a['capacity']))
        elif tag=='loc' and parent=='node':node.update(a)
        elif tag=='segment' and parent=='node':node['segment']=int(a['segment_id'])
        elif tag=='edge' and parent=='rr_edges':dest.append(int(a['sink_node']))
        stack.append(tag)
    def closing(tag):
        if tag=='node' and stack[-2]=='rr_nodes' and node['type'] in ['CHANX','CHANY'] and int(node['capacity'])>0:
            n=int(node['id']);keys=[]
            for x in range(int(node['xlow']),int(node['xhigh'])+1):
                for y in range(int(node['ylow']),int(node['yhigh'])+1):
                    key=(int(node.get('layer',0)),x,y,node['type'],node.get('segment',-1));keys.append(key);bin_caps[key]+=caps[n]
            channel[n]=keys
        assert stack.pop()==tag
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    with graph.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    parser.Parse(b'',True);assert len(dest)==8097539 and len(channel)==258720 and len(bin_caps)==17160
    channel_ids=set(channel)
    header=re.compile(r'^\s*Net\s+\d+\s+\((.*)\)(.*)$');rows=[]
    for item in plan['cases']:
        case=item['case'];reported=next(x for x in result['cases'] if x['case']==case);meta=json.loads(Path(item['endpoint']).read_text());names={name:int(net) for net,name in meta['net_names'].items()};native=defaultdict(set);current=None
        route=Path(item['native_label']).parent/'output.route'
        for line in route.open():
            m=header.match(line)
            if m:current=names.get(m[1]) if not m[2].strip() else None;continue
            m=NODE.match(line)
            if m:assert current is not None;native[current].add(int(m[1]))
        pools=[]
        for kind in ['candidate_A','candidate_B']:
            owned=defaultdict(set)
            for x in json.loads(Path(item[kind]).read_text())['records']:
                owned[x['net_id']].add(x['source'])
                for eid in x['answer']['physical_edge_ids']:owned[x['net_id']].add(dest[eid])
            pools.append(owned)
        assert set(pools[0])==set(pools[1])==set(native) and len(native)==55300
        ledger=Counter();choices=Counter();errors=Counter();seen=set()
        for line in (root/case/'choices.jsonl').open():
            x=json.loads(line);net=x['net_id'];assert net not in seen;seen.add(net);t=native[net].intersection(channel_ids);a=pools[0][net].intersection(channel_ids);b=pools[1][net].intersection(channel_ids)
            ea=len(a)+len(t)-2*len(a.intersection(t));eb=len(b)+len(t)-2*len(b.intersection(t));pick='A' if ea<=eb else 'B'
            assert (x['pick'],x['A_error'],x['B_error'])==(pick,ea,eb)
            owned=pools[pick=='B'][net];assert set(x['owned'])==owned and len(x['owned'])==len(owned);ledger.update(owned);choices[pick]+=1;errors.update(A=ea,B=eb,chosen=min(ea,eb))
        assert seen==set(native) and dict(choices)==reported['choices'] and dict(errors)==reported['per_NET_CHANNEL_errors']
        assert dict(ledger)=={int(n):v for n,v in json.loads((root/case/'ledger.json').read_text()).items()}
        truth=Counter(n for nodes in native.values() for n in nodes);sp,st=Counter(),Counter()
        for n,keys in channel.items():
            for key in keys:sp[key]+=ledger[n];st[key]+=truth[n]
        verify_metric({n:Fraction(ledger[n],caps[n]) for n in channel},{n:Fraction(truth[n],caps[n]) for n in channel},12936,reported['metrics']['concrete'])
        verify_metric({k:Fraction(sp[k],cap) for k,cap in bin_caps.items()},{k:Fraction(st[k],cap) for k,cap in bin_caps.items()},20,reported['metrics']['spatial'])
        old=json.loads(Path(item['quality_reference_protocol']).with_name('comparison.json').read_text())
        for control,comparison in reported['comparisons'].items():
            flags=[]
            for c in comparison['checks']:
                a=reported['metrics'][c['scope']][c['metric']];b=old['metrics']['cold'][control][c['scope']][c['metric']];eps=1e-12 if c['metric']=='spearman' else 0
                assert (a,b)==(c['candidate'],c['reference']);nr,strict=a>=b-eps,a>b+eps;assert (nr,strict)==(c['nonregression'],c['strict']);flags.append((nr,strict))
            assert comparison['pass_comparison']==(all(a for a,b in flags) and any(b for a,b in flags))
        assert sum(max(0,v-caps[n]) for n,v in ledger.items())==reported['overflow_units'] and reported['eligible_for_legal_route_commit'] is False
        rows.append(dict(case=case,NETs=len(seen),metric_vectors=2));print('COMPLETE_NET_CHOICE_INDEPENDENT_PASS',case,flush=True)
    with (root/'independent_verification_v1.json').open('x') as f:
        json.dump(dict(status='ALL3_COMPLETE_NET_CHOICES_LEDGER_OVERFLOW_SIX_METRICS_AND_COMPARISONS_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [rp,Path(__file__).resolve(),R/'tools/verify_MMC_complete_static_criticality_metrics_v2_2026_10_19.py']},scope='Independent joins, accounting and metrics. Original physical path proofs transferred, no new native route or deployable prediction.'),f,indent=2)


if __name__=='__main__':main()
