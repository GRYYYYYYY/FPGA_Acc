#pragma once
#include "../net_conditioned_hint_contract_v2/query_cost_frame.h"
#include <functional>
#include <istream>
#include <map>
#include <string>
namespace routecast_import_v1 {
using routecast_v2::FrameClaim;
using routecast_v2::FrameError;
struct Context {
    std::string graph_sha256;
    uint32_t node_count;
    uint64_t epoch;
    std::vector<std::string> net_names;
    std::vector<bool> ignored;
    std::map<uint32_t,uint32_t> expected_hint_bits;
    std::function<bool(uint32_t)> is_unit_channel;
};
inline bool sha(const std::string& s) {
    return s.size()==64 && s.find_first_not_of("0123456789abcdef")==std::string::npos;
}
inline uint64_t number(const std::string& s) {
    if(s.empty() || (s.size()>1 && s[0]=='0'))throw FrameError("noncanonical integer");
    uint64_t n=0;
    for(char c:s) {if(c<'0'||c>'9'||n>(UINT64_MAX-uint64_t(c-'0'))/10)throw FrameError("integer overflow/domain");n=n*10+uint64_t(c-'0');}
    return n;
}
inline std::string hex_name(const std::string& s) {
    static const char* digits="0123456789abcdef";std::string out;
    for(unsigned char c:s) {out+=digits[c>>4];out+=digits[c&15];}return out;
}
inline std::vector<FrameClaim> read(std::istream& in,const Context& ctx) {
    if(!sha(ctx.graph_sha256)||!ctx.node_count||!ctx.epoch||ctx.net_names.empty()||ctx.net_names.size()!=ctx.ignored.size()||!ctx.is_unit_channel)throw FrameError("invalid caller context");
    auto token=[&](){std::string s;if(!(in>>s))throw FrameError("truncated claims");return s;};
    if(token()!="RCPREF2"||token()!=ctx.graph_sha256)throw FrameError("schema/graph mismatch");
    if(number(token())!=ctx.node_count||number(token())!=ctx.net_names.size()||number(token())!=ctx.epoch)throw FrameError("namespace/epoch mismatch");
    auto count=number(token()),owners=number(token());
    if(count!=ctx.expected_hint_bits.size()||count>ctx.node_count||owners>ctx.net_names.size()||owners>count)throw FrameError("count mismatch");
    std::map<uint32_t,bool> named;uint64_t prior=0;
    for(uint64_t i=0;i<owners;++i) {
        if(token()!="N")throw FrameError("expected owner row");
        auto net=number(token());auto name=token();
        if(net>=ctx.net_names.size()||(i&&net<=prior)||ctx.ignored[net]||name!=hex_name(ctx.net_names[net]))throw FrameError("owner identity/order/ignored");
        named.emplace(uint32_t(net),false);prior=net;
    }
    std::vector<FrameClaim> claims;claims.reserve(count);prior=0;
    for(uint64_t i=0;i<count;++i) {
        if(token()!="C")throw FrameError("expected claim row");
        auto node=number(token()),net=number(token()),bits=number(token());
        if(node>=ctx.node_count||net>=ctx.net_names.size()||bits>UINT32_MAX||(i&&node<=prior))throw FrameError("claim bounds/order");
        auto owner=named.find(uint32_t(net));auto hint=ctx.expected_hint_bits.find(uint32_t(node));
        if(owner==named.end()||hint==ctx.expected_hint_bits.end()||hint->second!=bits||!ctx.is_unit_channel(uint32_t(node)))throw FrameError("claim context mismatch");
        float value;uint32_t word=uint32_t(bits);std::memcpy(&value,&word,4);
        if(!std::isfinite(value)||value<=1.f)throw FrameError("hint value");
        owner->second=true;claims.push_back({uint32_t(node),uint32_t(net),word});prior=node;
    }
    for(auto entry:named)if(!entry.second)throw FrameError("unused owner");
    std::string extra;if(in>>extra)throw FrameError("trailing claims");if(!in.eof())throw FrameError("input IO failure");
    return claims;
}
}
