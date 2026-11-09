"""Label-guided whole-NET bank diagnostic; never a deployable predictor."""
import json,re,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from fractions import Fraction
from pre_route_endpoints import sha
from prediction_metrics import compare
from versioned_digest_cache_v1 import Cache
from audit_native_route import NODE

R=Path(__file__).resolve().parents[1]
HEADER=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)(.*)$')


def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,default=lambda v:str(v) if isinstance(v,Fraction) else None)


def main():
    pp=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(pp.read_text())
    out=R/'experiments/mmc_complete_NET_choice_diagnostic_v1_2026-10-19';out.mkdir(exist_ok=False)
    cache=Cache()
    with cache.installed():
        assert all(sha(p)==h for p,h in plan['bindings'].items())
        bindings={str(pp):sha(pp),str(Path(__file__).resolve()):sha(__file__)}
        graph=Path(json.loads(Path(plan['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);dest=array('I');caps=array('I');channels={};bins=Counter();stack=[];node=None
        def opening(tag,a):
            nonlocal node
            parent=stack[-1] if stack else None
            if tag=='node' and parent=='rr_nodes':node=dict(a);assert int(a['id'])==len(caps);caps.append(int(a['capacity']))
            elif tag=='loc' and parent=='node':node['loc']=dict(a)
            elif tag=='segment' and parent=='node':node['segment']=int(a['segment_id'])
            elif tag=='edge' and parent=='rr_edges':dest.append(int(a['sink_node']))
            stack.append(tag)
        def closing(tag):
            nonlocal node
            if tag=='node' and stack[-2]=='rr_nodes':
                if node['type'] in ['CHANX','CHANY'] and int(node['capacity'])>0:
                    loc=node['loc'];keys=[(int(loc.get('layer','0')),x,y,node['type'],node.get('segment',-1)) for x in range(int(loc['xlow']),int(loc['xhigh'])+1) for y in range(int(loc['ylow']),int(loc['yhigh'])+1)]
                    channels[int(node['id'])]=keys
                    for key in keys:bins[key]+=int(node['capacity'])
                node=None
            assert stack.pop()==tag
        parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
        parser.Parse(b'',True);assert len(caps)==904438 and len(dest)==8097539 and len(channels)==258720 and len(bins)==17160;bindings[str(graph)]=sha(graph)
        rows=[]
        for item in plan['cases']:
            case=item['case'];ep=Path(item['endpoint']);meta=json.loads(ep.read_text());assert meta['graph_sha256']==sha(graph);queries={q['connection_id']:q for q in meta['connections']};assert len(queries)==115572
            qprotocol=Path(item['quality_reference_protocol']);qp=json.loads(qprotocol.read_text());quality=qprotocol.parent/'comparison.json';qproof=qprotocol.parent/'verification.json';prior=json.loads(quality.read_text());pv=json.loads(qproof.read_text());assert pv['status']=='pass' and pv['bindings'][str(quality)]==sha(quality)
            native_path=Path(item['native_label']);native_audit=json.loads(native_path.read_text());route=native_path.parent/'output.route';assert native_audit['all_printed_branch_arc_switch_and_union_checks_pass'] and native_audit['overflow_units']==0 and native_audit['inputs_sha256']['route']==sha(route)
            names={meta['net_names'][str(q['net_id'])]:q['net_id'] for q in queries.values()};native=defaultdict(set);net=None
            for line in route.open():
                m=HEADER.match(line)
                if m:net=names.get(m[2]) if not m[3].strip() else None;continue
                m=NODE.match(line)
                if m:assert net is not None;native[net].add(int(m[1]))
                elif line.lstrip().startswith('Node:'):raise ValueError('unparsed native node')
            truth=Counter(n for nodes in native.values() for n in nodes);assert dict(truth)=={int(n):v for n,v in native_audit['node_occupancy'].items()}
            frames=[];owners=[];recordmaps=[]
            aproof=Path(qp['model_directory'])/'feedback_audits/native_retained_sketch.json';pa=json.loads(aproof.read_text());pb=json.loads(Path(item['candidate_B_physical_proof']).read_text())
            for key,proof in [('candidate_A',pa),('candidate_B',pb)]:
                p=Path(item[key]);assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and proof['bindings'][str(p)]==sha(p)
                frame=json.loads(p.read_text());records={x['connection_id']:x for x in frame['records']};assert len(records)==len(frame['records'])==115572 and set(records)==set(queries)
                owned=defaultdict(set)
                for cid,x in records.items():
                    q=queries[cid];assert all(x[k]==v for k,v in q.items());owned[q['net_id']].add(q['source']);owned[q['net_id']].update(dest[e] for e in x['answer']['physical_edge_ids'])
                ledger=Counter(n for nodes in owned.values() for n in nodes);assert dict(ledger)=={int(n):v for n,v in frame['ledger'].items()}
                frames.append(frame);owners.append(owned);recordmaps.append(records)
            for cid in queries:assert all(recordmaps[0][cid][k]==recordmaps[1][cid][k] for k in ['floor_integer','budget_integer'])
            assert set(owners[0])==set(owners[1])==set(native) and len(native)==55300
            directory=out/case;directory.mkdir();choice=directory/'choices.jsonl';ledger=Counter();count=Counter();errors=Counter()
            with choice.open('x') as f:
                for net in sorted(native):
                    target=native[net]&channels.keys();a=owners[0][net]&channels.keys();b=owners[1][net]&channels.keys();ea=len(a^target);eb=len(b^target);pick=int(eb<ea);selected=owners[pick][net];ledger.update(selected);count['B' if pick else 'A']+=1;errors['A']+=ea;errors['B']+=eb;errors['chosen']+=min(ea,eb)
                    f.write(json.dumps(dict(net_id=net,pick='B' if pick else 'A',A_error=ea,B_error=eb,owned=sorted(selected)),separators=(',',':'))+'\n')
            def metrics(occupancy):
                span=Counter();truth_span=Counter()
                for n,keys in channels.items():
                    for key in keys:span[key]+=occupancy.get(n,0);truth_span[key]+=truth.get(n,0)
                return dict(concrete=compare({n:Fraction(occupancy.get(n,0),caps[n]) for n in channels},{n:Fraction(truth.get(n,0),caps[n]) for n in channels},12936),spatial=compare({k:Fraction(span[k],v) for k,v in bins.items()},{k:Fraction(truth_span[k],v) for k,v in bins.items()},20))
            scored=metrics(ledger);comparisons={}
            for control in ['previous_native','raw_min_on','native_retained_on','all_NET_on']:
                checks=[]
                for scope in ['concrete','spatial']:
                    for metric in ['spearman','precision_at_k']:
                        a=scored[scope][metric];b=prior['metrics']['cold'][control][scope][metric];eps=1e-12 if metric=='spearman' else 0;checks.append(dict(scope=scope,metric=metric,candidate=a,reference=b,nonregression=a>=b-eps,strict=a>b+eps))
                comparisons[control]=dict(checks=checks,pass_comparison=all(x['nonregression'] for x in checks) and any(x['strict'] for x in checks))
            overflow=sum(max(0,v-caps[n]) for n,v in ledger.items());save(directory/'ledger.json',dict(ledger));rows.append(dict(case=case,NETs=len(native),connections=len(queries),choices=dict(count),per_NET_CHANNEL_errors=dict(errors),metrics=scored,comparisons=comparisons,overflow_units=overflow,eligible_for_legal_route_commit=False))
            for p in [ep,qprotocol,quality,qproof,native_path,route,aproof,Path(item['candidate_A']),Path(item['candidate_B']),Path(item['candidate_B_physical_proof']),choice,directory/'ledger.json']:bindings[str(p)]=sha(p)
            print('LABEL_GUIDED_NET_CHOICE',case,dict(count),{k:v['pass_comparison'] for k,v in comparisons.items()},'overflow',overflow,flush=True)
        save(out/'results.json',dict(status='ALL3_LABEL_GUIDED_COMPLETE_NET_CHOICES_SCORED_INDEPENDENT_VERIFICATION_PENDING',cases=rows,bindings=bindings,scope='Retrospective label-guided bank diagnostic, not deployable, no global metric upper bound or prediction promotion.'))


if __name__=='__main__':main()
