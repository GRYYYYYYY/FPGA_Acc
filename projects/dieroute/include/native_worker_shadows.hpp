#pragma once
#include "native_route_state.hpp"
#include <array>
namespace dieroute {
struct NativeSummary {
    std::uint64_t occupancy=0,history=0,version=0;
    bool operator==(const NativeSummary& b)const{return std::tie(occupancy,history,version)==std::tie(b.occupancy,b.history,b.version);}
};
struct NativeSummaryPacket {
    std::array<std::uint64_t,8> words{};
    std::uint64_t session()const{return words[0];}
    std::uint32_t node()const{return words[1];}
    std::uint32_t owner()const{return (words[1]>>32)&255;}
    std::uint32_t worker()const{return (words[1]>>40)&255;}
    std::uint32_t kind()const{return (words[1]>>48)&255;} // 1 fetch, 2 reply, 3 update
    NativeSummary value()const{return {words[2],words[3],words[4]};}
    std::uint64_t serial()const{return words[5];}
    static NativeSummaryPacket make(std::uint64_t session,std::uint64_t serial,std::uint32_t n,std::uint32_t owner,std::uint32_t worker,std::uint32_t kind,NativeSummary s={}){
        NativeSummaryPacket p;p.words={session,std::uint64_t(n)|(std::uint64_t(owner)<<32)|(std::uint64_t(worker)<<40)|(std::uint64_t(kind)<<48),s.occupancy,s.history,s.version,serial,0,0};return p;
    }
    auto encode()const{std::array<unsigned char,64> b{};for(unsigned w=0;w<8;++w)for(unsigned i=0;i<8;++i)b[w*8+i]=static_cast<unsigned char>(words[w]>>(8*i));return b;}
    static NativeSummaryPacket decode(const unsigned char* b){NativeSummaryPacket p;for(unsigned w=0;w<8;++w)for(unsigned i=0;i<8;++i)p.words[w]|=std::uint64_t(b[w*8+i])<<(8*i);return p;}
};
static_assert(sizeof(NativeSummaryPacket)==64,"fixed summary wire payload");
struct NativeShadowRead {std::size_t branch=0;std::uint32_t worker=0,node=0;NativeSummary seen;bool hit=false;};
// One lane owns these non-authoritative receiver caches. The coordinator may
// refresh them only between joined search phases; a lane queries only its own
// cache during parallel search. Authority is never changed by delivery.
class NativeWorkerShadows {
    NativeOwnerLayout layout_;
    std::array<std::map<std::uint32_t,NativeSummary>,8> cache_;
    std::uint64_t session_=0,serial_=0;
    std::vector<NativeSummaryPacket> messages_;
    static void require(bool yes,const char* why){if(!yes)throw std::logic_error(why);}
    void endpoint(std::uint32_t worker,std::uint32_t n)const{
        auto mask=layout_.membership(n);require(worker<layout_.count()&&(mask&(1u<<worker))&&worker!=layout_.owner(n)&&(mask&(mask-1)),"invalid shadow endpoint");
    }
    void packet(const NativeSummaryPacket& p)const{
        require(p.words[1]>>56==0&&p.words[6]==0&&p.words[7]==0&&p.serial()>0,"malformed summary packet");
        endpoint(p.worker(),p.node());require(p.owner()==layout_.owner(p.node()),"wrong summary owner");
    }
    auto next(){if(serial_==UINT64_MAX)throw std::overflow_error("summary serial exhausted");return ++serial_;}
    static NativeSummaryPacket wire(const NativeSummaryPacket& p){auto b=p.encode();return NativeSummaryPacket::decode(b.data());}
public:
    struct Metrics {std::uint64_t fetches=0,hits=0,updates=0,scans=0,received=0,stale=0,duplicates=0;};
    Metrics metrics;
    virtual ~NativeWorkerShadows()=default;
    static NativeSummary authority(const NativeRouteState& state,std::uint32_t n){auto u=state.find_use(n);return u?NativeSummary{u->nets.size(),u->history,u->version}:NativeSummary{};}
    static std::uint64_t cost(NativeSummary s,bool own,std::uint64_t present){
        const auto others=s.occupancy-(own&&s.occupancy?1:0);
        if(s.history>=UINT64_MAX-1||(others&&present>(UINT64_MAX-2-s.history)/others))throw std::overflow_error("persistent shadow cost overflow");
        return 1+s.history+present*others;
    }
    virtual void reset(NativeOwnerLayout layout,std::uint64_t session){
        require(session>session_,"summary session must increase");layout_=std::move(layout);session_=session;serial_=0;metrics={};messages_.clear();for(auto& c:cache_)c.clear();
    }
    virtual std::size_t size()const{std::size_t n=0;for(const auto& c:cache_)n+=c.size();return n;}
    virtual std::vector<NativeSummaryPacket> take_messages(){auto out=std::move(messages_);messages_.clear();return out;}
    virtual bool receive(const NativeSummaryPacket& p){
        packet(p);require(p.kind()==2||p.kind()==3,"summary receive opcode");
        if(p.session()!=session_){++metrics.stale;return false;}
        auto& c=cache_[p.worker()];auto found=c.find(p.node());auto s=p.value();
        require(s.history<UINT64_MAX,"nonfinite summary history");
        if(found!=c.end()){
            if(s.version<found->second.version){++metrics.stale;return false;}
            if(s.version==found->second.version){require(s==found->second,"summary value changed without version");++metrics.duplicates;return false;}
        }
        c[p.node()]=s;++metrics.received;return true;
    }
    NativeSummaryPacket serve(const NativeSummaryPacket& request,const NativeRouteState& state)const{
        packet(request);require(request.session()==session_&&request.kind()==1&&request.words[2]==0&&request.words[3]==0&&request.words[4]==0&&layout_.same(state.layout()),"invalid summary fetch request");
        return NativeSummaryPacket::make(session_,request.serial(),request.node(),request.owner(),request.worker(),2,authority(state,request.node()));
    }
    virtual std::pair<NativeSummary,bool> query(const NativeRouteState& snapshot,std::uint32_t worker,std::uint32_t n){
        require(layout_.same(snapshot.layout()),"summary layout changed");endpoint(worker,n);auto& c=cache_[worker];auto found=c.find(n);
        if(found!=c.end()){++metrics.hits;return {found->second,true};}
        auto request=wire(NativeSummaryPacket::make(session_,next(),n,layout_.owner(n),worker,1));messages_.push_back(request);
        auto reply=wire(serve(request,snapshot));messages_.push_back(reply);require(receive(reply),"fresh summary fetch rejected");++metrics.fetches;return {reply.value(),false};
    }
    // Refresh subscribed entries only. Dropping a tail publication is not a
    // communication saving; the driver explicitly drains at each repeat end.
    virtual std::vector<NativeSummaryPacket> refresh(const NativeRouteState& state){
        require(layout_.same(state.layout())&&messages_.empty(),"summary refresh phase/context");
        for(std::uint32_t worker=0;worker<layout_.count();++worker)for(const auto& [n,old]:cache_[worker]){
            ++metrics.scans;auto current=authority(state,n);
            require(current.version>=old.version,"authority version regressed; reset shadow session");
            if(!(current==old)){
                auto update=wire(NativeSummaryPacket::make(session_,next(),n,layout_.owner(n),worker,3,current));
                require(receive(update),"current summary publication rejected");messages_.push_back(update);++metrics.updates;
            }
        }
        return take_messages();
    }
};
}
