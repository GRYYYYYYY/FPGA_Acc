#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
namespace dieroute {
enum class LabelOp:std::uint8_t {probe=1,probe_reply=2,relax=3,relax_reply=4,trace=5,trace_reply=6};
enum class LabelStatus:std::uint8_t {ok=0,accepted=1,stale=2,protected_label=3,dominated=4,budget=5,epoch=6,overflow=7};
// One 512-bit little-endian payload, without compiler padding or host pointers.
// words: epoch, request id, {node,op,from,to,status}, cost, priority,
// {hops,parent}, {edge,flags}, observed/current version.
struct LabelPacket {
    std::array<std::uint64_t,8> words{};
    static constexpr std::uint32_t present=1,closed=2,root=4,created=8,controller=8;
    std::uint64_t epoch()const{return words[0];}
    std::uint64_t id()const{return words[1];}
    std::uint32_t node()const{return std::uint32_t(words[2]);}
    LabelOp op()const{return LabelOp((words[2]>>32)&255);}
    std::uint32_t from()const{return (words[2]>>40)&255;}
    std::uint32_t to()const{return (words[2]>>48)&255;}
    LabelStatus status()const{return LabelStatus(words[2]>>56);}
    std::uint64_t cost()const{return words[3];}
    std::uint64_t priority()const{return words[4];}
    std::uint32_t hops()const{return std::uint32_t(words[5]);}
    std::uint32_t parent()const{return words[5]>>32;}
    std::uint32_t edge()const{return std::uint32_t(words[6]);}
    std::uint32_t flags()const{return words[6]>>32;}
    std::uint64_t version()const{return words[7];}
    static LabelPacket message(std::uint64_t epoch,std::uint64_t id,std::uint32_t node,LabelOp op,std::uint32_t from,std::uint32_t to,LabelStatus status=LabelStatus::ok){
        if(from>controller||to>controller)throw std::invalid_argument("label packet endpoint");
        LabelPacket p;p.words[0]=epoch;p.words[1]=id;p.words[2]=node|(std::uint64_t(op)<<32)|(std::uint64_t(from)<<40)|(std::uint64_t(to)<<48)|(std::uint64_t(status)<<56);return p;
    }
    void value(std::uint64_t cost,std::uint64_t priority,std::uint32_t hops,std::uint32_t parent,std::uint32_t edge,std::uint32_t flags,std::uint64_t version){
        words[3]=cost;words[4]=priority;words[5]=hops|(std::uint64_t(parent)<<32);words[6]=edge|(std::uint64_t(flags)<<32);words[7]=version;
    }
    std::array<unsigned char,64> encode()const{
        std::array<unsigned char,64> b{};for(unsigned w=0;w<8;++w)for(unsigned i=0;i<8;++i)b[w*8+i]=static_cast<unsigned char>(words[w]>>(8*i));return b;
    }
    static LabelPacket decode(const unsigned char* b){
        LabelPacket p;for(unsigned w=0;w<8;++w)for(unsigned i=0;i<8;++i)p.words[w]|=std::uint64_t(b[w*8+i])<<(8*i);return p;
    }
    static void match(const LabelPacket& request,const LabelPacket& reply){
        const auto expected=request.op()==LabelOp::probe?LabelOp::probe_reply:request.op()==LabelOp::trace?LabelOp::trace_reply:LabelOp::relax_reply;
        if(reply.epoch()!=request.epoch()||reply.id()!=request.id()||reply.node()!=request.node()||reply.from()!=request.to()||reply.to()!=request.from()||reply.op()!=expected)
            throw std::logic_error("mismatched label response");
        auto require=[](bool ok){if(!ok)throw std::logic_error("malformed label response payload");};
        require(std::uint32_t(reply.status())<=std::uint32_t(LabelStatus::overflow));
        if(reply.status()==LabelStatus::epoch){for(unsigned i=3;i<8;++i)require(reply.words[i]==0);return;}
        if(request.op()==LabelOp::relax){
            require(reply.status()!=LabelStatus::ok&&reply.words[3]==0&&reply.words[4]==0&&reply.words[5]==0&&reply.edge()==0);
            if(reply.status()==LabelStatus::accepted)require((reply.flags()&~created)==0&&request.version()<UINT64_MAX&&reply.version()==request.version()+1);
            else require(reply.flags()==0);
        }else{
            require(reply.status()==LabelStatus::ok&&reply.priority()==0&&(reply.flags()&~(present|closed|root))==0);
            if(reply.flags()&present)require(reply.version()>0&&reply.cost()<UINT64_MAX);
            else require(reply.flags()==0&&reply.version()==0&&reply.cost()==UINT64_MAX&&reply.hops()==UINT32_MAX&&reply.parent()==UINT32_MAX&&reply.edge()==UINT32_MAX);
        }
    }
};
static_assert(sizeof(LabelPacket)==64,"fixed label payload");
}
