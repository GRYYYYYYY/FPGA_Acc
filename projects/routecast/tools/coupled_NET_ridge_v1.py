"""Fixed alpha=1 ridge; preprocessing and labels are training-fold arguments only."""
import math


def predict(model,values):
    if len(values)!=len(model['coefficients']) or any(not math.isfinite(v) for v in values):raise ValueError('feature domain')
    return model['target_mean']+math.fsum(b*(x-m)/s for b,x,m,s in zip(model['coefficients'],values,model['means'],model['scales']))


def fit(X,y):
    if not X or len(X)!=len(y):raise ValueError('training rows')
    n=len(X);d=len(X[0])
    if any(len(row)!=d or any(not math.isfinite(v) for v in row) for row in X) or any(not math.isfinite(v) for v in y):raise ValueError('training domain')
    means=[math.fsum(row[j] for row in X)/n for j in range(d)]
    scales=[math.sqrt(math.fsum((row[j]-means[j])**2 for row in X)/n) or 1. for j in range(d)]
    ym=math.fsum(y)/n;Z=[[(x-m)/s for x,m,s in zip(row,means,scales)] for row in X];yc=[v-ym for v in y]
    gram=[[0.]*d for _ in range(d)]
    for i in range(d):
        for j in range(i+1):
            value=math.fsum(row[i]*row[j] for row in Z)+(1. if i==j else 0.)
            gram[i][j]=gram[j][i]=value
    rhs=[math.fsum(row[j]*target for row,target in zip(Z,yc)) for j in range(d)]
    L=[[0.]*d for _ in range(d)]
    for i in range(d):
        for j in range(i+1):
            value=gram[i][j]-math.fsum(L[i][k]*L[j][k] for k in range(j))
            if i==j:
                if value<=0:raise ValueError('nonpositive ridge Cholesky diagonal')
                L[i][j]=math.sqrt(value)
            else:L[i][j]=value/L[j][j]
    z=[]
    for i in range(d):z.append((rhs[i]-math.fsum(L[i][k]*z[k] for k in range(i)))/L[i][i])
    beta=[0.]*d
    for i in reversed(range(d)):beta[i]=(z[i]-math.fsum(L[k][i]*beta[k] for k in range(i+1,d)))/L[i][i]
    residual=max((abs(math.fsum(a*b for a,b in zip(row,beta))-target)/(1+abs(target)+math.fsum(abs(a*b) for a,b in zip(row,beta))) for row,target in zip(gram,rhs)),default=0.)
    if not residual<1e-8:raise ValueError('ridge normal-equation residual')
    return dict(means=means,scales=scales,target_mean=ym,coefficients=beta,training_rows=n,alpha=1,normal_equation_relative_residual=residual)


def fit_fold(feature_tables,label_tables,training_cases,evaluation_case):
    cases=tuple(sorted(training_cases))
    if not cases or len(set(cases))!=len(cases) or evaluation_case in cases:raise ValueError('fold separation')
    X=[];y=[];rows=[]
    for case in cases:
        features=feature_tables[case];labels=label_tables[case]
        if set(features)!=set(labels):raise ValueError('training NET domain')
        for net in sorted(features):X.append(features[net]);y.append(labels[net])
        rows.append(dict(case=case,NETs=len(features)))
    model=fit(X,y);model.update(training_cases=list(cases),evaluation_case=evaluation_case,training_namespaces=rows)
    return model
