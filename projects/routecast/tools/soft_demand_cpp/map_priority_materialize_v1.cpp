// Exact staged binary32 interpolation and ceil integer priority conversion.
#include <cstdint>
#include <cstring>
#include <cmath>
#include <cfenv>
#include <boost/multiprecision/cpp_int.hpp>
using boost::multiprecision::uint256_t;
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
        uint256_t numerator=uint256_t(mant)*scale*denominator,result;
        if(power>=0) {
            if(power>=128 || numerator>=(uint256_t(1)<<(128-power)))return -7;
            result=numerator<<power;
        } else {unsigned shift=-power;result=(numerator+((uint256_t(1)<<shift)-1))>>shift;}
        if(result>=(uint256_t(1)<<128))return -7;
        words[2*u]=static_cast<uint64_t>(result&0xffffffffffffffffULL);
        words[2*u+1]=static_cast<uint64_t>(result>>64);
    }
    return 0;
}
