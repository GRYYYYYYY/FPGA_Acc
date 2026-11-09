"""Fixed empirical frequency model and exact ties-even probability quantization."""
SCALE=10**6


def project(code,with_prefix=True):
    if type(code) is not int or not 0<=code<216:raise ValueError('context code')
    return code if with_prefix else (code//12)*4+code%4


def quantize(numerator,denominator):
    if type(numerator) is not int or type(denominator) is not int or not 0<=numerator<=denominator or denominator<=0:raise ValueError('probability fraction')
    q,r=divmod(SCALE*numerator,denominator)
    return q+int(2*r>denominator or 2*r==denominator and q%2==1)


def fit(contexts,labels,training_cases,evaluation_case,with_prefix=True):
    cases=sorted(training_cases)
    if not cases or len(cases)!=len(set(cases)) or evaluation_case in cases:raise ValueError('fold separation')
    size=216 if with_prefix else 72;N=[0]*size;S=[0]*size
    for case in cases:
        codes=contexts[case];ys=labels[case]
        if len(codes)!=len(ys):raise ValueError('resource domain')
        for code,y in zip(codes,ys):
            if type(y) is not int or y not in [0,1]:raise ValueError('binary training label')
            group=project(code,with_prefix);N[group]+=1;S[group]+=y
    return dict(with_prefix=with_prefix,training_cases=cases,evaluation_case=evaluation_case,counts=N,occupied=S,
                probability_int=[quantize(s+1,n+2) for s,n in zip(S,N)],scale=SCALE)


def predict(model,codes):
    return [model['probability_int'][project(code,model['with_prefix'])] for code in codes]
