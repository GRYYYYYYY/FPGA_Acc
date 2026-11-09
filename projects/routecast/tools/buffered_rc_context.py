"""Authenticated reader for separately prepared exact RC context."""
from array import array
from pre_route_endpoints import sha

def load(root,graph_sha256):
    import json,sys
    from pathlib import Path
    from fractions import Fraction
    root=Path(root);receipt=json.loads((root/'receipt.json').read_text())
    if receipt['protocol_sha256']!=sha(root/'protocol.json'):raise ValueError('changed protocol')
    for name in ('node_rc_class_ids.bin','electrical_context.json'):
        if sha(root/name)!=receipt['outputs'][name]:raise ValueError('changed electrical payload')
    data=json.loads((root/'electrical_context.json').read_text())
    if data['schema']!='ROUTECAST_EXACT_BUFFERED_RC_CLASSES_V1' or data['byteorder']!='little' or data['graph_sha256']!=graph_sha256:raise ValueError('incompatible electrical context')
    n=data['node_count']
    if type(n) is not int or n<1 or (root/'node_rc_class_ids.bin').stat().st_size!=8*n:raise ValueError('invalid node count/payload size')
    if data['node_class_ids_sha256']!=receipt['outputs']['node_rc_class_ids.bin']:raise ValueError('class payload binding mismatch')
    def fraction(v):
        if not isinstance(v,list) or len(v)!=2 or any(type(x) is not int for x in v) or v[0]<0 or v[1]<=0:raise ValueError('invalid exact fraction')
        result=Fraction(*v)
        if [result.numerator,result.denominator]!=v:raise ValueError('fraction not normalized')
        return result
    def pair(v):
        if not isinstance(v,list) or len(v)!=2:raise ValueError('invalid electrical pair')
        return tuple(fraction(x) for x in v)
    classes=[pair(v) for v in data['node_rc_classes']]
    switches={}
    for k,v in data['switches'].items():
        if not isinstance(k,str) or not k.isdigit() or str(int(k))!=k:raise ValueError('invalid switch identity')
        switches[int(k)]=pair(v)
    if not classes or not switches:raise ValueError('empty electrical context')
    ids=array('Q')
    with (root/'node_rc_class_ids.bin').open('rb') as f:ids.fromfile(f,n)
    if sys.byteorder!='little':ids.byteswap()
    if any(v>=len(classes) for v in ids):raise ValueError('unknown node RC class')
    return ids,classes,switches
