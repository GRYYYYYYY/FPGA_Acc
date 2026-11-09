"""Target-label-free fixed-score closed choices over admitted full candidate banks."""
import json,time,xml.parsers.expat as expat
from pathlib import Path
from array import array
from collections import Counter
from maximum_weight_NET_closure_v1 import solve,verify
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]


def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2)


def main():
    start=time.perf_counter();protocol=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';plan=json.loads(protocol.read_text());out=R/'experiments/mmc_input_only_closed_choice_v1_2026-10-19';out.mkdir(exist_ok=False)
    cp=R/'experiments/maximum_weight_NET_closure_contract_v1_2026-10-19/verification.json';contract=json.loads(cp.read_text());assert contract['status']=='EXHAUSTIVE_AND_RANDOM_CLOSURE_OPTIMA_FLOW_CUT_CERTIFICATES_TIES_AND_CORRUPTION_PASS' and all(sha(p)==h for p,h in contract['bindings'].items())
    bindings={str(p):sha(p) for p in [protocol,cp,Path(__file__).resolve(),R/'tools/maximum_weight_NET_closure_v1.py']}
    # Pinned RR metadata is a declared inference input. No target-route,
    # native-occupancy, oracle-choice or label-seeded review file is opened.
    graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)=='8d13c26981fbc46df4ae4584b848863cff89f711e6f2b30f396638fd8d7db131';bindings[str(graph)]=sha(graph)
    caps=array('I');channel=bytearray();stack=[]
    class Done(Exception):pass
    def opening(tag,a):
        if tag=='node' and stack and stack[-1]=='rr_nodes':
            assert int(a['id'])==len(caps);c=int(a['capacity']);caps.append(c);channel.append(c>0 and a['type'] in ['CHANX','CHANY'])
        stack.append(tag)
    def closing(tag):
        assert stack.pop()==tag
        if tag=='rr_nodes':raise Done()
    parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
    try:
        with graph.open('rb') as f:
            for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
    except Done:pass
    assert len(caps)==904438 and sum(channel)==258720;setup=time.perf_counter()-start;rows=[]
    source=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'
    for case in plan['cases']:
        begin=time.perf_counter();directory=out/case;directory.mkdir();gp=source/case/'graph.json';bp=source/case/'banks.jsonl'
        for p in [gp,bp]:assert plan['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p)
        g=json.loads(gp.read_text());N=len(g['nodes']);assert N==55300;groups=g['components'];component={net:i for i,group in enumerate(groups) for net in group};assert set(component)==set(g['nodes'])
        weights={};features={};seen=set();bank=[]
        for x in map(json.loads,bp.open()):
            net=x['net_id'];assert net not in seen;seen.add(net);a=sum(channel[n] for n in x['A']);b=sum(channel[n] for n in x['B']);gain=a-b
            features[net]=dict(net_id=net,A_CHANNELs=a,B_CHANNELs=b,gain=gain,encoded=(N+1)*gain-1);weights[net]=features[net]['encoded'];bank.append(x)
        assert seen==set(g['nodes']);cw={i:sum(weights[n] for n in group) for i,group in enumerate(groups)};edges=[tuple(x) for x in g['condensation_edges']];prepared=time.perf_counter()-begin
        t=time.perf_counter();certificate=solve(cw,edges);solver_seconds=time.perf_counter()-t;t=time.perf_counter();verify(cw,edges,certificate);certificate_seconds=time.perf_counter()-t
        selected={n for i in certificate['selected'] for n in groups[i]};assert all(x['source'] not in selected or x['target'] in selected for x in g['edges'])
        ledger=Counter();gain=sum(features[n]['gain'] for n in selected)
        for x in bank:ledger.update(x['B'] if x['net_id'] in selected else x['A'])
        assert certificate['objective']==(N+1)*gain-len(selected) and certificate['objective']>=0
        assert all(ledger[n]<=1 for n in g['eligible_resources']);overflow=sum(max(0,v-caps[n]) for n,v in ledger.items());selection=directory/'choices.jsonl'
        with selection.open('x') as f:
            for net in sorted(features):f.write(json.dumps(dict(features[net],pick='B' if net in selected else 'A'),separators=(',',':'))+'\n')
        save(directory/'flow_cut_certificate.json',certificate);save(directory/'ledger.json',dict(ledger));elapsed=time.perf_counter()-begin
        rows.append(dict(case=case,NETs=N,B_NETs=len(selected),CHANNEL_demand_reduction=gain,encoded_objective=certificate['objective'],overflow_units=overflow,protected_domain_overflow=0,bank_read_and_score_seconds=prepared,solver_seconds=solver_seconds,certificate_seconds=certificate_seconds,case_component_seconds=elapsed,eligible_for_legal_route_commit=False))
        for p in [selection,directory/'flow_cut_certificate.json',directory/'ledger.json']:bindings[str(p)]=sha(p)
        print('INPUT_ONLY_CLOSED_CHOICE',case,'B',len(selected),'gain',gain,'overflow',overflow,'solver_seconds',solver_seconds,flush=True)
    save(out/'receipt.json',dict(status='ALL3_INPUT_ONLY_FIXED_SCORE_CLOSED_CHOICES_PRODUCED',rows=rows,bindings=bindings,shared_RR_metadata_and_preflight_seconds=setup,producer_seconds=time.perf_counter()-start,target_labels_read=False,
        scope='Fixed input-derived score; no target routes, native occupancy or oracle choices accessed. Existing graph/bank physical proofs inherited through frozen protocol. Bank production ~460s/case plus A/setup/audits is not free; no full-flow, quality, heldout or global-legal-route claim.'))


if __name__=='__main__':main()
