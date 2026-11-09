"""Independent layered span/capacity oracle for the native label metric domain."""
import json
import tempfile
from pathlib import Path
from pre_route_endpoints import sha
from stream_metric_domain_layered_v1 import metric_domain
from stream_metric_domain import metric_domain as legacy_domain


def main():
    nodes = [(0,0,'CHANX',2,0,2,0,0,1),(1,1,'CHANX',4,0,2,0,0,1),(2,0,'CHANY',3,1,1,0,2,2),(3,0,'CHANX',0,0,0,0,0,1),(4,0,'CHANX',6,1,2,0,0,1)]
    pv={'0':2,'2':1,'4':3};tv={'1':3,'2':2,'4':2}
    xml='<rr_graph><rr_nodes>'+''.join(f'<node id="{i}" type="{kind}" capacity="{cap}"><loc layer="{layer}" xlow="{xl}" xhigh="{xh}" ylow="{yl}" yhigh="{yh}"/><segment segment_id="{seg}"/></node>' for i,layer,kind,cap,xl,xh,yl,yh,seg in nodes)+'</rr_nodes></rr_graph>'
    expected_p={};expected_t={};sums={}
    for i,layer,kind,cap,xl,xh,yl,yh,seg in nodes:
        if cap==0:continue
        expected_p[str(i)]=pv.get(str(i),0)/cap;expected_t[str(i)]=tv.get(str(i),0)/cap
        for x in range(xl,xh+1):
            for y in range(yl,yh+1):
                key=f'{layer},{x},{y},{kind},{seg}'
                a,b,c=sums.get(key,(0,0,0));sums[key]=(a+pv.get(str(i),0),b+tv.get(str(i),0),c+cap)
    with tempfile.TemporaryDirectory() as tmp:
        graph=Path(tmp)/'graph.xml';graph.write_text(xml)
        rp,rt,sp,st,_,_=metric_domain(graph,pv,tv)
        assert rp==expected_p and rt==expected_t
        assert sp=={k:a/c for k,(a,b,c) in sums.items()}
        assert st=={k:b/c for k,(a,b,c) in sums.items()}
        assert sp['0,1,0,CHANX,1']==5/8
        assert st['0,1,0,CHANX,1']==2/8
        single=Path(tmp)/'single.xml'
        single.write_text(xml.replace('layer="1"','layer="0"'))
        a=metric_domain(single,pv,tv);b=legacy_domain(single,pv,tv)
        assert a[:2]==b[:2]
        for index in (2,3):
            assert {key.split(',',1)[1]:value for key,value in a[index].items()}==b[index]
        assert a[4:]==b[4:]
        for bad in ({'0':-1},{'0':1.5},{'0':True}):
            try:metric_domain(graph,bad,tv)
            except ValueError:pass
            else:raise AssertionError('invalid occupancy accepted')
    out=Path(__file__).resolve().parents[1]/'experiments/layered_metric_domain_contract_v1_2026-10-14'
    out.mkdir(exist_ok=True)
    report=dict(all_pass=True,channel_resources=len(rp),spatial_bins=len(sp),invalid_occupancy_rejections=3,single_layer_legacy_projection_equal=True,bindings={str(Path(__file__).resolve()):sha(__file__),str(Path(__file__).with_name('stream_metric_domain_layered_v1.py').resolve()):sha(Path(__file__).with_name('stream_metric_domain_layered_v1.py')),str(Path(__file__).with_name('stream_metric_domain.py').resolve()):sha(Path(__file__).with_name('stream_metric_domain.py')),str(Path(__file__).with_name('pre_route_endpoints.py').resolve()):sha(Path(__file__).with_name('pre_route_endpoints.py'))},scope='Synthetic metric-domain contract only; no native neuron labels or prediction-quality claim.')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='bindings'}))

if __name__=='__main__':main()
