"""Target-free per-CHANNEL categorical historical/early-router context."""
import json,sys,xml.parsers.expat as expat
from pathlib import Path
from array import array
from pre_route_endpoints import sha
from versioned_digest_cache_v1 import Cache

R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/mmc_resource_context_v1_2026-10-19';out.mkdir(exist_ok=False)
    protocol=dict(cases=['case_01','case_02','case_03'],context=['previous_native occupancy0/1','candidate A occupancy0/1/2plus','candidate B occupancy0/1/2plus','native first-iteration occupancy0/1/2plus','graph-only direction/segment group'],
        code='((old*27+A*9+B*3+prefix)*G+group), where G=number of sorted(type,segment) groups. UInt16 in declared native byteorder, same ascending CHANNEL node order.',
        forbidden='No target final route/occupancy, NET owner labels, oracle masks or learned scores. No fitting, probabilities or quality evaluation.',
        prefix_scope='First-iteration input-derived context only, not an admitted route candidate: original quality and V2raw budgets failed. All prior failures retained. Capture input identity and originalXML uniqueNET occupancy proof required.',
        scope='Old exposed MMC development layouts; no new native captures. Prefix ~27s/case plus full A/B costs remains paid, not free.')
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');prefixroot=R/'experiments/mmc_native_first_iteration_v1_2026-10-18';pp=prefixroot/'physical_and_budget_verification_v1.json';ip=prefixroot/'input_identity_verification_v1.json';pv=json.loads(pp.read_text());iv=json.loads(ip.read_text());assert pv['status']=='all3_first_iteration_full_XML_physical_identity_and_budget_diagnostics_complete' and iv['status']=='all3_native_capture_inputs_current_endpoint_and_native_manifest_bindings_verified'
    original=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(original.read_text());old=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';op=old.parent/'independent_xml_verification_v1.json';ov=json.loads(op.read_text());assert ov['all_native_paths_exact'] and ov['bindings'][str(old)]==sha(old)
    bindings={str(p):sha(p) for p in [pp,ip,original,old,op,Path(__file__).resolve()]};cache=Cache()
    with cache.installed():
        graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)=='8d13c26981fbc46df4ae4584b848863cff89f711e6f2b30f396638fd8d7db131';nodes=[];groups=[];stack=[];node=None
        class Done(Exception):pass
        def opening(tag,a):
            nonlocal node
            if tag=='node' and stack and stack[-1]=='rr_nodes':node=dict(a)
            elif tag=='segment' and stack and stack[-1]=='node':node['segment']=int(a['segment_id'])
            stack.append(tag)
        def closing(tag):
            if tag=='node' and stack[-2]=='rr_nodes' and node['type'] in ['CHANX','CHANY'] and int(node['capacity'])>0:
                assert int(node['capacity'])==1;nodes.append(int(node['id']));groups.append((node['type'],node.get('segment',-1)))
            assert stack.pop()==tag
            if tag=='rr_nodes':raise Done()
        parser=expat.ParserCreate();parser.StartElementHandler=opening;parser.EndElementHandler=closing
        try:
            with graph.open('rb') as f:
                for b in iter(lambda:f.read(1<<20),b''):parser.Parse(b,False)
        except Done:pass
        assert len(nodes)==258720 and nodes==sorted(nodes);group_names=sorted(set(groups));G=len(group_names);assert G==4;group_ids={g:i for i,g in enumerate(group_names)};group_values=[group_ids[g] for g in groups];nodepath=out/'CHANNEL_ids.u32';nodepath.write_bytes(array('I',nodes).tobytes());meta=out/'domain.json';meta.write_text(json.dumps(dict(nodes=258720,groups=group_names,byteorder=sys.byteorder,codes=54*G),indent=2)+'\n');bindings.update({str(p):sha(p) for p in [graph,nodepath,meta]});past={int(n):v for n,v in json.loads(old.read_text())['ledger'].items()};assert all(past.get(n,0) in [0,1] for n in nodes);rows=[]
        for item in plan['cases']:
            case=item['case'];a=Path(item['candidate_A']);b=Path(item['candidate_B']);prefix=prefixroot/case/'diagnostic_sketch_v1.json';receipt=prefixroot/case/'receipt.json';r=json.loads(receipt.read_text());state=prefixroot/case/'states/round_1.tsv'
            for p in [a,b]:assert plan['bindings'][str(p)]==sha(p)
            assert pv['bindings'][str(prefix)]==sha(prefix) and pv['bindings'][str(state)]==sha(state) and r['header']==['H','1','0','0'];assert r['files'][str(state)]==sha(state)
            physical=next(x for x in pv['cases'] if x['case']==case);identity=next(x for x in iv['cases'] if x['case']==case);assert physical['all115572_current_CID_paths_and_original_XML_parent_switch_arcs_pass'] and physical['all_native_N_occupancies_equal_full_T_uniqueNET_ledger'] and identity['native_executed_inputs_equal_current_staged_target'];assert physical['all_original_V2_budgets_pass'] is False
            ledgers=[{int(n):v for n,v in json.loads(p.read_text())['ledger'].items()} for p in [a,b,prefix]];codes=array('H')
            for n,g in zip(nodes,group_values):
                A,B,P=[min(2,L.get(n,0)) for L in ledgers];codes.append((past.get(n,0)*27+A*9+B*3+P)*G+g)
            assert len(codes)==258720 and max(codes)<216;target=out/(case+'.u16');target.write_bytes(codes.tobytes());rows.append(dict(case=case,resources=len(codes),observed_categories=len(set(codes)),prefix_native_process_seconds=r['complete_native_process_seconds'],prefix_original_budgets_pass=False))
            bindings.update({str(p):sha(p) for p in [a,b,prefix,receipt,state,target]});print('RESOURCE_CONTEXT_BUILT',case,len(codes),len(set(codes)),flush=True)
        (out/'receipt.json').write_text(json.dumps(dict(status='ALL3_LABEL_FREE_RESOURCE_CONTEXT_CODES_PRODUCED',rows=rows,bindings=bindings,target_final_labels_read=False,independent_verification_pending=True,scope=protocol['scope']),indent=2)+'\n')


if __name__=='__main__':main()
