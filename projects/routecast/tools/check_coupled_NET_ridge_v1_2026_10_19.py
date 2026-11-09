"""Closed-form toy solutions and inaccessible held-out-label/feature guards."""
import json,math,copy
from pathlib import Path
from coupled_NET_ridge_v1 import fit,predict,fit_fold
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]


def main():
    out=R/'experiments/coupled_NET_ridge_contract_v1_2026-10-19';out.mkdir(exist_ok=False)
    model=fit([[-1.],[1.]],[-2.,2.]);assert model['means']==[0.] and model['scales']==[1.] and model['target_mean']==0.;assert math.isclose(model['coefficients'][0],4/3,abs_tol=1e-14)
    assert math.isclose(predict(model,[3.]),4.,abs_tol=1e-13)
    m=fit([[5.,-1.],[5.,1.]],[8.,12.]);assert m['scales'][0]==1 and m['coefficients'][0]==0 and m['target_mean']==10.
    assert math.isclose(m['coefficients'][1],4/3,abs_tol=1e-14)
    # Correlated columns: ridge solution is symmetric and exactly0.8 per beta.
    m=fit([[-1.,-1.],[1.,1.]],[-2.,2.]);assert all(math.isclose(b,.8,abs_tol=1e-14) for b in m['coefficients'])
    class Guard(dict):
        def __getitem__(self,key):
            if key=='test':raise AssertionError('held-out data read during fitting')
            return super().__getitem__(key)
    features=Guard(a={0:[-1.],1:[1.]},b={0:[0.],1:[2.]},test={0:[1e20]});labels=Guard(a={0:-2.,1:2.},b={0:0.,1:4.},test={0:-1e30})
    first=fit_fold(features,labels,['a','b'],'test');labels['test']={0:1e30};features['test']={0:[-1e20]};second=fit_fold(features,labels,['b','a'],'test');assert first==second
    assert first['means']==[.5] and math.isclose(first['scales'][0],math.sqrt(1.25),abs_tol=1e-15)
    for invalid in [(['a','test'],'test'),(['a','a'],'test')]:
        try:fit_fold(features,labels,*invalid)
        except ValueError:pass
        else:raise AssertionError('invalid fold admitted')
    for X,y in [([],[]),([[1.]],[]),([[float('nan')]],[0.]),([[1.],[1.,2.]],[0.,1.])]:
        try:fit(X,y)
        except ValueError:pass
        else:raise AssertionError('invalid training data admitted')
    paths=[Path(__file__).resolve(),R/'tools/coupled_NET_ridge_v1.py'];(out/'verification.json').write_text(json.dumps(dict(status='RIDGE_CLOSED_FORM_CONSTANT_CORRELATED_COLUMNS_TRAIN_ONLY_SCALING_AND_HELDOUT_NONINTERFERENCE_PASS',bindings={str(p):sha(p) for p in paths},scope='Numerical and namespace core only, no real fold fit or prediction-quality proof.'),indent=2)+'\n');print('RIDGE_CORE_CONTRACT_PASS',flush=True)


if __name__=='__main__':main()
