"""Complete wide-payload input loading, old XTEA parity, rejected proof domains."""
import json
import struct
import sys
from pathlib import Path
from pre_route_endpoints import sha
from load_design_routing_inputs_wide_v1 import load
from load_design_routing_inputs_v1 import load as legacy_load

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def main():
    out=R/'experiments/design_wide_input_contract_v1_2026-10-13';out.mkdir(exist_ok=False)
    bindings=closure([Path(__file__)]);results={}
    specs=[('xtea','freecores_native_demand_v1_2026-10-08/xtea/endpoints.json',
            'xtea_node_base_wide_v1_2026-10-13','xtea_retained_native_inputs_v1_2026-10-13'),
           ('neuron','titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json',
            'titan23_neuron_node_base_wide_v1_2026-10-13','titan23_neuron_native_inputs_v1_2026-10-13')]
    for name,ep,basedir,capturedir in specs:
        ep=R/'experiments'/ep;basedir=R/'experiments'/basedir;crit=R/'experiments'/capturedir/'criticality'
        bp=basedir/'verification.json';proof=json.loads(bp.read_text())
        ap=basedir/'independent_verification.json';audit=json.loads(ap.read_text())
        assert audit['all_pass'] and audit['independent_XML_float32_bits_and_payload_all_entries_equal']
        assert audit['bindings'][str(bp)]==sha(bp)
        assert all(sha(p)==h for p,h in audit['bindings'].items())
        values,cs,admitted=load(ep,bp,crit,proof['nodes'],proof['scale'])
        bindings.update(admitted);bindings.update(audit['bindings']);bindings[str(ap)]=sha(ap)
        assert len(values)==proof['nodes'] and len(cs)==len(json.loads(ep.read_text())['connections'])
        results[name]=dict(nodes=len(values),connections=len(cs),scale=proof['scale'],maximum_node_base=max(values),
                           nodes_exceeding_u64=sum(v>=2**64 for v in values))
        if name=='xtea':
            old=R/'experiments/xtea_retained_node_base_v1_2026-10-13/verification.json'
            old_values,old_cs,old_bindings=legacy_load(ep,old,crit,len(values),proof['scale'])
            assert values==old_values and cs==old_cs;bindings.update(old_bindings)
            results[name]['all_node_values_and_criticalities_equal_legacy']=True
            rejected=[]
            cases=[('wrong_nodes',dict(nodes=len(values)+1)),('wrong_scale',dict(scale=proof['scale']+1)),
                   ('wrong_format',dict(payload_format='native_u64')),('wrong_filename',dict(payload_file='node_base.u64')),
                   ('unbound_endpoint',dict(bindings={k:v for k,v in proof['bindings'].items() if k!=str(ep)}))]
            for case,changes in cases:
                p=out/(case+'.json');p.write_text(json.dumps(dict(proof,**changes)))
                try:load(ep,p,crit,len(values),proof['scale'])
                except ValueError as e:rejected.append(dict(case=case,error=str(e)))
                else:raise AssertionError(case+' accepted')
            results[name]['domain_rejections']=rejected
        del values,cs
    assert all(sha(p)==h for p,h in bindings.items())
    result=dict(bindings=bindings,all_pass=True,designs=results,
                scope='Complete authenticated wide-cost input admission and old XTEA scalar/identity parity. Titan full search, state/event audits, QoR and memory residency are separate gates.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(results,indent=2),flush=True)

if __name__=='__main__':main()
