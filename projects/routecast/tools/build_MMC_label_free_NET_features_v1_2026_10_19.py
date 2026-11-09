"""Fixed timing/competition/geometry features; no target routes or oracle files."""
import json,math,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from load_explicit_timing_epoch_v1 import load as load_timing
from versioned_digest_cache_v1 import Cache

R=Path(__file__).resolve().parents[1]
FEATURES=['fanout','changed_connections','endpoint_move_L1','bbox_width','bbox_height','criticality_min','criticality_mean','criticality_max','budget_mean_ns',
          'A_CHANNELs','B_CHANNELs','B_minus_A_CHANNELs','A_CHANNEL_span','B_CHANNEL_span','B_minus_A_span','bank_CHANNEL_Jaccard',
          'A_base_sum_ns','B_base_sum_ns','B_minus_A_base_sum_ns','A_raw_mean_ns','B_raw_mean_ns','B_minus_A_raw_mean_ns',
          'A_max_budget_fraction','B_max_budget_fraction','A_overused_CHANNELs','B_overused_CHANNELs','A_mean_other_CHANNEL_occupancy','B_mean_other_CHANNEL_occupancy',
          'implication_outdegree','implication_indegree','SCC_size']


def main():
    out=R/'experiments/mmc_label_free_NET_features_v1_2026-10-19';out.mkdir(exist_ok=False)
    # Freeze names and input roles before extracting any values. NET IDs are
    # join metadata only, never feature values. Absolute coordinates omitted.
    spec=dict(feature_names=FEATURES,cases=['case_01','case_02','case_03'],
        allowlist='A/B complete candidate inputs, candidate ownership banks/graph, current endpoints, explicit pre-move timing remap and before endpoints, admitted structural node-base and original RR metadata.',
        forbidden='Target native routes/occupancy, native perNET unions, label-guided choices/closures/errors; no normalization, training or evaluation.',
        timing_scope='Use exactly the original candidate-producing frozen pre-move timing epoch, remapped to current endpoints. Not fresh post-placement or final target STA.',
        scope='All3 old exposed MMC development layouts; same NET IDs across layouts. No unseen-family claim. Values remain raw; future standardization must be fitted on training folds only.')
    (out/'protocol.json').write_text(json.dumps(spec,indent=2)+'\n')
    bindings={str(Path(__file__).resolve()):sha(__file__)};cache=Cache()
    with cache.installed():
        graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)=='8d13c26981fbc46df4ae4584b848863cff89f711e6f2b30f396638fd8d7db131'
        xcoord=array('i');ycoord=array('i');caps=array('I');span=array('I');stack=[];node=None
        class Done(Exception):pass
        def opening(tag,a):
            nonlocal node
            parent=stack[-1] if stack else None
            if tag=='node' and parent=='rr_nodes':node=dict(a);assert int(a['id'])==len(caps)
            elif tag=='loc' and parent=='node':node.update(a)
            stack.append(tag)
        def closing(tag):
            if tag=='node' and stack[-2]=='rr_nodes':
                caps.append(int(node['capacity']));xcoord.append(int(node['xlow']));ycoord.append(int(node['ylow']));span.append(max(int(node['xhigh'])-int(node['xlow']),int(node['yhigh'])-int(node['ylow']))+1 if node['type'] in ['CHANX','CHANY'] and int(node['capacity'])>0 else 0)
            assert stack.pop()==tag
            if tag=='rr_nodes':raise Done()
        parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
        try:
            with graph.open('rb') as f:
                for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
        except Done:pass
        assert len(caps)==904438 and sum(v>0 for v in span)==258720;bindings[str(graph)]=sha(graph);rows=[]
        ownerroot=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'
        for case in spec['cases']:
            source=R/'experiments/mmc_all_NET_feedback_v1_2026-10-18'/case;producer=source/'protocol.json';p=json.loads(producer.read_text());ep=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';meta=json.loads(ep.read_text());queries={q['connection_id']:q for q in meta['connections']};assert len(queries)==115572
            timing_proof=Path(p['criticality_input_proof']);tp=json.loads(timing_proof.read_text());assert tp['schema']=='ROUTECAST_FROZEN_TIMING_REMAP_V1' and Path(tp['after_endpoint']).resolve()==ep.resolve();critical=load_timing(timing_proof.parent)
            before=Path(tp['before_endpoint']);old={q['connection_id']:q for q in json.loads(before.read_text())['connections']};assert set(old)==set(queries)==set(critical)
            baseproof=Path(p['structural_node_base_proof']);baseinfo=json.loads(baseproof.read_text());basefile=baseproof.parent/'node_base.u64';assert baseinfo['bindings'][str(ep)]==sha(ep) and baseinfo['bindings'][str(basefile)]==sha(basefile);base=array('Q');base.frombytes(basefile.read_bytes());assert len(base)==len(caps) and baseinfo['scale']==10**18
            a=R/'experiments/mmc_multiplacement_models_v1_2026-10-18'/case/'feedback_on/native_retained/sketch.json';b=source/'sketch.json';frames=[json.loads(q.read_text()) for q in [a,b]];maps=[{r['connection_id']:r for r in f['records']} for f in frames];ledgers=[{int(n):v for n,v in f['ledger'].items()} for f in frames]
            gp=ownerroot/case/'graph.json';bankfile=ownerroot/case/'banks.jsonl';g=json.loads(gp.read_text());outdegree=Counter(e['source'] for e in g['edges']);indegree=Counter(e['target'] for e in g['edges']);sizes={n:len(c) for c in g['components'] for n in c};groups=defaultdict(list)
            for cid,q in queries.items():
                c=critical[cid];assert (c['net'],c['source_rr'],c['target_rr'])==(q['net_id'],q['source'],q['sink']);groups[q['net_id']].append(cid)
                assert all(m[cid][k]==v for m in maps for k,v in q.items());assert maps[0][cid]['budget_integer']==maps[1][cid]['budget_integer']
            target=out/(case+'.jsonl');seen=set()
            with target.open('x') as f:
                for bank in map(json.loads,bankfile.open()):
                    net=bank['net_id'];assert net not in seen;seen.add(net);ids=groups[net];qs=[queries[cid] for cid in ids];cvals=[critical[cid]['criticality'] for cid in ids];fanout=len(ids);budgets=[maps[0][cid]['budget_integer'] for cid in ids]
                    changed=sum((old[cid]['source'],old[cid]['sink'])!=(queries[cid]['source'],queries[cid]['sink']) for cid in ids)
                    movement=sum(abs(xcoord[old[cid][end]]-xcoord[queries[cid][end]])+abs(ycoord[old[cid][end]]-ycoord[queries[cid][end]]) for cid in ids for end in ['source','sink'])
                    endpoints={q[end] for q in qs for end in ['source','sink']};width=max(xcoord[n] for n in endpoints)-min(xcoord[n] for n in endpoints);height=max(ycoord[n] for n in endpoints)-min(ycoord[n] for n in endpoints)
                    owned=[set(bank[key]) for key in ['A','B']];chans=[{n for n in nodes if span[n]>0} for nodes in owned];counts=list(map(len,chans));spans=[sum(span[n] for n in nodes) for nodes in chans];costs=[sum(base[n] for n in nodes-{qs[0]['source']})/1e9 for nodes in owned];raw=[sum(m[cid]['answer']['delay'] for cid in ids)/fanout/1e9 for m in maps];fractions=[max(m[cid]['answer']['delay']/m[cid]['budget_integer'] for cid in ids) for m in maps]
                    crowded=[sum(ledgers[i][n]>caps[n] for n in chans[i]) for i in range(2)];other=[sum(ledgers[i][n]-1 for n in chans[i])/max(1,len(chans[i])) for i in range(2)];union=chans[0]|chans[1]
                    values=[fanout,changed,movement,width,height,min(cvals),sum(cvals)/fanout,max(cvals),sum(budgets)/fanout/1e9,*counts,counts[1]-counts[0],*spans,spans[1]-spans[0],len(chans[0]&chans[1])/len(union) if union else 1.,*costs,costs[1]-costs[0],*raw,raw[1]-raw[0],*fractions,*crowded,*other,outdegree[net],indegree[net],sizes[net]]
                    assert len(values)==len(FEATURES) and all(math.isfinite(v) for v in values);f.write(json.dumps(dict(net_id=net,values=values),separators=(',',':'))+'\n')
            assert seen==set(groups)==set(g['nodes']) and len(seen)==55300
            paths=[producer,ep,timing_proof,timing_proof.parent/'remapped_criticalities.json',before,baseproof,basefile,a,b,gp,bankfile,target]
            bindings.update({str(q):sha(q) for q in paths});rows.append(dict(case=case,NETs=len(seen),connections=len(queries),features=len(FEATURES),timing_epoch=tp['timing_epoch_sha256']));print('LABEL_FREE_FEATURES_BUILT',case,len(seen),len(FEATURES),flush=True)
        (out/'receipt.json').write_text(json.dumps(dict(status='ALL3_LABEL_FREE_NET_FEATURE_TABLES_PRODUCED',rows=rows,bindings=bindings,target_labels_read=False,independent_verification_pending=True,scope=spec['scope']),indent=2)+'\n')


if __name__=='__main__':main()
