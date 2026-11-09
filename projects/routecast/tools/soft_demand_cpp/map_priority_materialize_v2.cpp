// Exact staged binary32 interpolation and ceil integer priority conversion.
#include <cstdint>
#include <cstring>
#include <cmath>
#include <cfenv>
extern "C" int rc_map_materialize(uint64_t n,const float* endpoints,const unsigned char* allowed,const unsigned char* terminal,uint32_t criticality_bits,uint64_t scale,uint64_t denominator,uint64_t* words) {
    if(!n||!scale||!denominator||std::fegetround()!=FE_TONEAREST)return -1;
    float c;std::memcpy(&c,&criticality_bits,4);
    if(!std::isfinite(c)||c<0.f||c>1.f)return -2;
    volatile float complement=1.f-c;
    for(uint64_t u=0;u<n;++u) {
        if(allowed[u]>1||terminal[u]>1)return -3;
        words[2*u]=words[2*u+1]=0;
        if(!allowed[u])continue;
        float zero=endpoints[2*u],one=endpoints[2*u+1];
        if(!std::isfinite(zero)||!std::isfinite(one)||zero<0.f||one<0.f)return -4;
        float expected;
        if(terminal[u]) {if(zero!=one)return -5;expected=zero;}
        else {volatile float a=c*one;volatile float b=complement*zero;volatile float sum=a+b;expected=sum;}
        volatile float weighted=1.2f*expected;
        if(!std::isfinite(weighted)||weighted<0.f)return -6;
        uint32_t bits;float value=weighted;std::memcpy(&bits,&value,4);
        uint32_t exp=(bits>>23)&255,mant=bits&0x7fffff;
        int power=-149;if(exp){mant|=0x800000;power=int(exp)-150;}
        using Wide=unsigned __int128;
        Wide product=Wide(scale)*denominator;
        Wide a=Wide(uint64_t(product))*mant;
        Wide b=Wide(uint64_t(product>>64))*mant+(a>>64);
        uint64_t limbs[3]={uint64_t(a),uint64_t(b),uint64_t(b>>64)};
        uint64_t lo=0,hi=0;bool remainder=false;
        for(int bit=0;bit<192;++bit)if((limbs[bit/64]>>(bit%64))&1) {
            int dest=bit+power;
            if(dest<0)remainder=true;
            else if(dest>=128)return -7;
            else if(dest<64)lo|=uint64_t(1)<<dest;
            else hi|=uint64_t(1)<<(dest-64);
        }
        if(remainder) {if(++lo==0) {if(++hi==0)return -7;}}
        words[2*u]=lo;words[2*u+1]=hi;
    }
    return 0;
}
