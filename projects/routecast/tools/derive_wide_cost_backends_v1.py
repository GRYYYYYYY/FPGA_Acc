"""Reproducible storage/ABI widening; certified legacy sources stay immutable."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R = Path(__file__).resolve().parents[1]
D = R / 'tools/soft_demand_cpp'

def replace(s, old, new, count):
    assert s.count(old) == count, (old, s.count(old), count)
    return s.replace(old, new)

def derive():
    forward = D / 'tree_workspace_radix_v3.cpp'
    bidi = D / 'bidirectional_workspace_v2.cpp'
    word = '''
// Public ABI is two ordered uint64_t limbs, never a platform __int128 ABI.
struct Word {
 U lo,hi;
 Word(Wide value=0):lo(U(value)),hi(U(value>>64)){}
 operator Wide() const {return Wide(lo)|(Wide(hi)<<64);}
};
static_assert(sizeof(Word)==16 && alignof(Word)==8,"two-limb ABI");
'''
    s = forward.read_text()
    s = replace(s, 'using U=uint64_t;using Wide=unsigned __int128;', 'using U=uint64_t;using Wide=unsigned __int128;'+word, 1)
    s = replace(s, 'U initial,U weight,', 'const Word* initial_arg,const Word* weight_arg,', 2)
    s = replace(s, 'const U* inc', 'const Word* inc', 2)
    s = replace(s, 'const U* price,U* raw', 'const Word* price,Word* raw', 2)
    s = replace(s, ' try {', ' try {\n  if(!initial_arg||!weight_arg)return -1;\n  const Wide initial=*initial_arg,weight=*weight_arg;', 2)
    s = replace(s, 'U *owner_raw=nullptr,*owner_pn=nullptr,*owner_pe=nullptr;', 'Word *owner_raw=nullptr;U *owner_pn=nullptr,*owner_pe=nullptr;', 1)
    s = replace(s, 'std::fill(raw,raw+n,none)', 'std::fill(raw,raw+n,Word(~Wide(0)))', 2)
    s = replace(s, 'raw[node]=pn[node]=pe[node]=none;', 'raw[node]=~Wide(0);pn[node]=pe[node]=none;', 1)
    s = replace(s, 'if(nextRaw>=none)', 'if(nextRaw>=infinity)', 2)
    s = replace(s, 'raw[v]=U(nextRaw)', 'raw[v]=nextRaw', 2)
    out_forward = D / 'tree_workspace_radix_wide_v1.cpp'
    t = bidi.read_text()
    t = replace(t, '#include "tree_workspace_radix_stats_v4.cpp"', '#include "tree_workspace_radix_wide_v1.cpp"', 1)
    t = replace(t, 'std::vector<U> row,dest,inc,cap,rr,rd,re;', 'std::vector<U> row,dest,cap,rr,rd,re;\n std::vector<Word> inc;', 1)
    t = replace(t, 'const U* i,', 'const Word* i,', 1)
    t = replace(t, 'const U* inc', 'const Word* inc', 1)
    t = replace(t, 'U initial,U weight,const U* price', 'const Word* initial_arg,const Word* weight_arg,const Word* price', 1)
    t = replace(t, 'U* count,U* raw,', 'U* count,Word* raw,', 1)
    t = replace(t, '  auto* w=static_cast<Bidi*>(handle);', '  if(!initial_arg||!weight_arg)return -1;\n  const Wide initial=*initial_arg,weight=*weight_arg;\n  auto* w=static_cast<Bidi*>(handle);', 1)
    t = replace(t, 'original>=std::numeric_limits<U>::max()', 'original>=w->inf', 1)
    t = replace(t, '*raw=U(original)', '*raw=original', 1)
    out_bidi = D / 'bidirectional_workspace_wide_v1.cpp'
    for p, content in ((out_forward,s),(out_bidi,t)):
        if p.exists():assert p.read_text()==content, 'refuse to overwrite changed derivation'
        else:p.write_text(content)
    return dict(bindings={str(p):sha(p) for p in (Path(__file__),forward,bidi,out_forward,out_bidi)},
                scope='Only cost storage, sentinel and ABI widened; search and tie control flow unchanged. Requires numerical and full-model validation.')

if __name__=='__main__':print(json.dumps(derive(),indent=2))
