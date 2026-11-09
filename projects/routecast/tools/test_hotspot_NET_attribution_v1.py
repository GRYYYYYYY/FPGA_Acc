"""Independent branch-union oracle with original unsorted physical edge IDs."""
import json
from pathlib import Path
import tempfile
from hotspot_NET_attribution_v1 import domain,model_owners,native_owners,incidences,components


def main():
    with tempfile.TemporaryDirectory() as t:
        p=Path(t);graph=p/'graph.xml'
        graph.write_text('<rr_graph><segments><segment id="1" name="long"/></segments><rr_nodes>'+''.join(
            f'<node id="{i}" type="{kind}" capacity="{cap}"><loc xlow="0" xhigh="1" ylow="0" yhigh="0"/><segment segment_id="1"/></node>'
            for i,kind,cap in [(0,'SOURCE',1),(1,'CHANX',1),(2,'SINK',1),(3,'SOURCE',1),(4,'SINK',1),(5,'CHANX',0)])+
            '</rr_nodes><rr_edges>'+''.join(f'<edge src_node="{a}" sink_node="{b}" switch_id="0"/>' for a,b in [(3,1),(0,1),(1,2),(1,4)])+'</rr_edges></rr_graph>')
        keys={'0,0,0,CHANX,1','0,1,0,CHANX,1'};d=domain(graph,keys)
        assert d['counts']==dict(nodes=6,edges=4) and d['members']=={1:keys}
        assert d['edge_sink']=={0:1,1:1} and d['bin_capacities']=={k:1 for k in keys}
        frame=p/'frame.json';rows=[dict(connection_id=i,net_id=net,answer=dict(physical_edge_ids=path)) for i,net,path in [(0,8,[1,2]),(1,8,[1,3]),(2,9,[0,3])]]
        frame.write_text(json.dumps(dict(records=rows,ledger={'1':2})))
        owners,connections,fanout,n=model_owners(frame,d)
        assert owners=={8:{1},9:{1}} and connections=={8:{0,1},9:{2}} and fanout=={8:2,9:1} and n==3
        bins=incidences(owners,d['members']);assert bins=={8:{k:1 for k in keys},9:{k:1 for k in keys}}
        assert all(sum(c[k] for c in bins.values())==2 for k in keys)
        route=p/'native.route';route.write_text('Net 0 (a(b))\nNode: 1 CHANX Switch: 0\nNode: 1 CHANX Switch: 0\nNet 1 (gnd): global net connecting:\nNet 2 (c)\nNode: 1 CHANX Switch: 0\n')
        actual,headers=native_owners(route,{1});assert headers==3 and actual=={'a(b)':{1},'c':{1}}
        assert components(keys,d['members'])==[sorted(keys)]
        frame.write_text(json.dumps(dict(records=rows+[rows[0]])))
        try:model_owners(frame,d)
        except ValueError:pass
        else:raise AssertionError('duplicate connection accepted')
    print('PASS original edge IDs, zero-cap exclusion, NET-union shared branches, span conservation and duplicate rejection')


if __name__=='__main__':main()
