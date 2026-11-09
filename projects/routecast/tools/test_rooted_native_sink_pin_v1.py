import json
from pathlib import Path
from rooted_native_sink_pin_v1 import resolve
from pre_route_endpoints import sha

def main():
    grid={(4,y,0):(7,0,y-10) for y in range(10,13)}
    classes={7:{100:3,101:3,102:4}}
    def node(kind,y,ptc):return dict(type=kind,loc=dict(xlow='4',xhigh='4',ylow=str(y),yhigh=str(y),layer='0',ptc=str(ptc)))
    row=dict(pins=[dict(index=0),dict(index=1,x=4,y=10,layer=0,physical_pin=101,**{'class':3}),
                   dict(index=2,x=4,y=10,layer=0,physical_pin=100,**{'class':3})])
    sink=node('SINK',12,3);ipin=node('IPIN',11,100)
    assert resolve(row,ipin,sink,grid,classes)==2
    # Same class/root with equivalent physical pins is disambiguated by IPIN.
    assert resolve(row,node('IPIN',12,101),sink,grid,classes)==1
    assert resolve(row,node('IPIN',10,100),node('SINK',10,3),grid,classes)==2
    rejected=0
    cases=[(row,node('OPIN',11,100),sink,grid,classes),
           (row,node('IPIN',11,102),sink,grid,classes),
           (row,ipin,sink,{**grid,(4,12,0):(7,0,0)},classes),
           (dict(pins=row['pins']+[dict(row['pins'][2],index=3)]),ipin,sink,grid,classes),
           (dict(pins=row['pins'][:2]),ipin,sink,grid,classes)]
    for args in cases:
        try:resolve(*args)
        except ValueError:rejected+=1
        else:raise AssertionError('invalid physical pin witness accepted')
    out=Path(__file__).resolve().parents[1]/'experiments/rooted_native_sink_pin_contract_v1_2026-10-13';out.mkdir(exist_ok=False)
    sources=[Path(__file__),Path(__file__).with_name('rooted_native_sink_pin_v1.py')]
    result=dict(bindings={str(p.resolve()):sha(p) for p in sources},all_pass=True,valid=3,rejected=rejected,
                scope='Rooted multiheight and equivalent-pin resolver fixtures; actual routed original XML/native pin agreement and canonical VPR reload remain separate gates.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('ROOTED NATIVE PIN RESOLVER PASS',3,rejected)

if __name__=='__main__':main()
