"""Exact rational rounding, category projection and held-out label guards."""
from pathlib import Path
from fractions import Fraction
import json
from resource_occupancy_frequency_v1 import project,quantize,fit,predict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/resource_occupancy_frequency_contract_v1_2026-10-19';out.mkdir(exist_ok=False);checks=0
    for denominator in range(1,160):
        for numerator in range(denominator+1):assert quantize(numerator,denominator)==round(Fraction(10**6*numerator,denominator));checks+=1
    assert quantize(1,2000000)==0 and quantize(3,2000000)==2
    for old in range(2):
        for A in range(3):
            for B in range(3):
                for group in range(4):
                    values=[project((old*27+A*9+B*3+prefix)*4+group,False) for prefix in range(3)];assert len(set(values))==1 and values[0]==(old*9+A*3+B)*4+group
    class Guard(dict):
        def __getitem__(self,key):
            if key=='test':raise AssertionError('heldout data touched during fit')
            return super().__getitem__(key)
    contexts=Guard(a=[0,0,1],b=[0,1,1],test=[215]);labels=Guard(a=[1,0,1],b=[1,0,1],test=[0]);model=fit(contexts,labels,['a','b'],'test');assert model['counts'][0]==3 and model['occupied'][0]==2 and model['probability_int'][0]==600000 and model['probability_int'][215]==500000
    labels['test']=[1];contexts['test']=[0];assert model==fit(contexts,labels,['b','a'],'test');assert predict(model,[215])==[500000]
    for cases in [['a','test'],['a','a']]:
        try:fit(contexts,labels,cases,'test')
        except ValueError:pass
        else:raise AssertionError('bad fold accepted')
    paths=[Path(__file__).resolve(),R/'tools/resource_occupancy_frequency_v1.py'];(out/'verification.json').write_text(json.dumps(dict(status='EXACT_PROBABILITY_QUANTIZATION_PREFIX_PROJECTION_AND_TRAIN_ONLY_FREQUENCY_PASS',rounding_checks=checks,bindings={str(p):sha(p) for p in paths}),indent=2)+'\n');print('RESOURCE_FREQUENCY_CONTRACT_PASS',checks,flush=True)


if __name__=='__main__':main()
