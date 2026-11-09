"""Admission-aware fixed external forecast comparison; no label selection."""
import argparse,json,time
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from external_forecast_metrics_v1 import vectors,metrics,gate

def evaluate(specification,output):
    begin=time.perf_counter();specification=Path(specification).resolve();s=json.loads(specification.read_text())
    if s['schema']!='ROUTECAST_EXTERNAL_TEMPORAL_PRIOR_SCORE_CASE_V1':raise ValueError('specification schema')
    bindings={str(specification):sha(specification),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
    def admit(path):
        path=Path(path).resolve();d=json.loads(path.read_text())
        for p,h in d['bindings'].items():
            if p in bindings and bindings[p]!=h:raise ValueError('conflicting evidence')
            if sha(p)!=h:raise ValueError('admission binding changed')
            bindings[p]=h
        bindings[str(path)]=sha(path);return d
    domain=admit(s['domain_proof']);ind=admit(s['domain_independent_proof'])
    if ind['status']!='ALL3_EXPAT_RESOURCE_IDENTITIES_INCLUSIVE_BINS_CAPACITIES_AND_K_EXACT':raise ValueError('domain audit')
    ep_path=Path(s['endpoint']).resolve();ep=json.loads(ep_path.read_text());bindings[str(ep_path)]=sha(ep_path)
    if domain['graph_sha256']!=ep['graph_sha256']:raise ValueError('domain graph epoch')
    for v in ep['inputs'].values():
        if sha(v['path'])!=v['sha256']:raise ValueError('endpoint dependency changed')
        bindings[v['path']]=v['sha256']
    folder=Path(s['domain_proof']).resolve().parent
    resources=[json.loads(line) for line in (folder/'resources.jsonl').read_text().splitlines()]
    bins=json.loads((folder/'spatial_bins.json').read_text())
    if len(resources)!=domain['resources'] or len(bins)!=domain['spatial_bins']:raise ValueError('domain counts')
    def frame(path,proof):
        path=Path(path).resolve()
        if proof['bindings'].get(str(path))!=sha(path):raise ValueError('frame not certified by proof')
        f=json.loads(path.read_text())
        if f['graph_sha256']!=ep['graph_sha256'] or f['completed_connections']!=f['required_connections'] or f['completed_connections']!=len(ep['connections']):raise ValueError('frame graph/coverage')
        return f
    source=admit(s['source_proof'])
    if source['status']!='SOURCE_XML_FRACTION_PATH_BUDGET_LEDGER_AUDIT_PASS':raise ValueError('source admission')
    previous=frame(s['source_frame'],source)
    expected_identity={q['connection_id']:q['net_id'] for q in ep['connections']}
    if {q['connection_id']:q['net_id'] for q in previous['records']}!=expected_identity:raise ValueError('previous CID/NET identity')
    predictions={'previous_native':previous}
    for method in ('native_retained_on','raw_min_on'):
        arm=s['predictions'][method];proof=admit(arm['proof'])
        if proof['bindings'].get(str(ep_path))!=sha(ep_path):raise ValueError('prediction proof target mismatch')
        if proof.get('all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass') is not True:raise ValueError('complete prediction audit required')
        f=frame(arm['frame'],proof)
        expected={q['connection_id']:(q['net_id'],q['source'],q['sink']) for q in ep['connections']}
        observed={q['connection_id']:(q['net_id'],q['source'],q['sink']) for q in f['records']}
        if observed!=expected or len(f['records'])!=len(expected):raise ValueError('prediction endpoint/CID mismatch')
        predictions[method]=f
    label=admit(s['label_proof'])
    if label['case']!=s['case']:raise ValueError('native label case mismatch')
    if label['status']!='FULL_PHYSICAL_AND_CANONICAL_PASS' or label['canonical'].get('semantic_consistency_gate_pass') is not True:raise ValueError('native label admission')
    payload=Path(s['label_physical_audit']).resolve()
    if label['bindings'].get(str(payload))!=sha(payload):raise ValueError('uncertified native label')
    physical=json.loads(payload.read_text())
    if physical['inputs_sha256']['graph']!=ep['graph_sha256'] or physical['overflow_units']!=0:raise ValueError('native graph/capacity')
    truth=vectors(resources,bins,{int(n):v for n,v in physical['node_occupancy'].items()},domain['graph_nodes'],truth=True)
    from zero_rc_budget_certificate_graph_v1 import load_graph
    from temporal_prior_utilization_score_v1 import score_vectors
    graph=load_graph(ep['inputs']['graph']['path'])
    temporal,weights=score_vectors(resources,bins,previous['records'],predictions['native_retained_on']['records'],graph['vs'])
    results={}
    for method,f in predictions.items():
        v=temporal if method=='native_retained_on' else vectors(resources,bins,{int(n):v for n,v in f['ledger'].items()},domain['graph_nodes'])
        results[method]=metrics(v,truth,domain['resource_k'],domain['spatial_k'])
    checks={method:gate(results['native_retained_on'],results[method]) for method in ('previous_native','raw_min_on')}
    if not all(sha(p)==h for p,h in bindings.items()):raise ValueError('evidence changed during evaluation')
    result=dict(status='COMPLETE_FIXED_CASE_FORECAST_COMPARISON',case=s['case'],bindings=bindings,metrics=results,checks=checks,pass_case_gate=all(c['pass_primary_gate'] for c in checks.values()),component_seconds=time.perf_counter()-begin,score_head='TEMPORAL_PRIOR_V1: pin-edit mixture and independent NET support union; uncalibrated score',raw_audited_ledger_changed=False,scope='Explicit temporal-prior score over historical support and current A* forecast, not the original direct-demand score. Raw physical ledger/path audit remains unchanged. Same truth/domain/K/four metric comparisons and controls; no reinterpretation of original model failures, full9 availability, native utility, matched total time or strict family status.')
    result['pin_edit_weights']={str(n):[v.numerator,v.denominator] for n,v in weights.items()}
    result['score_vectors']={scope:[[key,[v.numerator,v.denominator]] for key,v in sorted(values.items())] for scope,values in temporal.items()}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f:json.dump(result,f,indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator) if isinstance(x,Fraction) else None)
    return result['pass_case_gate']
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('specification');p.add_argument('output');a=p.parse_args();print('CASE_GATE',evaluate(a.specification,a.output))
