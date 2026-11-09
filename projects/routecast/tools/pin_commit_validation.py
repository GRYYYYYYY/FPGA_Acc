"""Validate assignment/cohort/equivalence before any ledger publication."""
def validate(chosen,paths,checks,endpoints):
    by_id={str(c['cid']):c for c in checks}
    expected={str(r['connection_id']):r for r in endpoints}
    if len(by_id)!=len(checks) or len(expected)!=len(endpoints):raise ValueError('duplicate identity')
    if set(chosen)!=set(paths) or not set(chosen)<=set(by_id)&set(expected):raise ValueError('cohort mismatch')
    used=set()
    for cid,pin in chosen.items():
        if type(pin) is not list or len(pin)!=2 or any(type(n) is not int or n<0 for n in pin):raise ValueError('invalid physical pin')
        sink,ptc=pin;check=by_id[cid]
        if sink!=expected[cid]['sink'] or check.get('sink_class',sink)!=sink:raise ValueError('wrong class')
        if check['equivalent'] not in {'full','none'} or ptc not in check['physical_members']:raise ValueError('unsupported equivalence/member')
        if check['equivalent']=='none' and len(check['physical_members'])!=1:raise ValueError('non-equivalent relaxation')
        if tuple(pin) in used:raise ValueError('pin shared by requests')
        used.add(tuple(pin))
        if str(ptc) not in paths[cid]['paths']:raise ValueError('missing selected path')
    return True
