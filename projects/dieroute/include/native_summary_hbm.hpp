#pragma once
#include "native_worker_shadows.hpp"
#include "owner_publish_hbm.hpp"
#include <mutex>
#include <optional>
namespace dieroute {
// Shared CPU orchestration around the synthesizable endpoint. Mutable owner
// mirrors are installed only between joined proposal phases. A CU serializes
// calls; each lane has its own queue tickets, making independent query phases
// canonically recordable without claiming an asynchronous memory protocol.
class NativeSummaryHbm {
public:
    struct Frame {std::uint32_t die;std::array<SummaryWord,5> words;std::uint32_t reason=UINT32_MAX;};
private:
    struct Ring {SummaryWord commands[16]={},responses[16]={};std::uint64_t ticket=0;};
    struct Actor {std::array<Ring,8> rings;std::vector<Frame> frames;};
    struct Die {
        std::vector<SummaryWord> owners,shadows,registry;
        std::vector<std::uint32_t> dirty;
        SummaryWord control={},updates[16]={};std::uint64_t update_ticket=0;
        std::mutex mutex;
    };
    NativeOwnerLayout layout_;
    std::vector<std::uint32_t> nodes_;
    std::vector<std::uint64_t> topology_;
    std::array<Die,8> dies_;
    std::vector<Actor> actors_;
    std::vector<std::optional<NativeSummary>> published_;
    std::uint32_t lanes_;
    bool push_;
    std::uint32_t dirty_capacity_=1;
    std::uint64_t session_=0;
    static void require(bool v,const char* why){if(!v)throw std::logic_error(why);}
    std::size_t slot(std::uint32_t node)const{auto i=std::lower_bound(nodes_.begin(),nodes_.end(),node);require(i!=nodes_.end()&&*i==node,"missing HBM boundary slot");return i-nodes_.begin();}
    static SummaryWord word(const NativeSummaryPacket& p){SummaryWord w={};std::copy(p.words.begin(),p.words.end(),w.w);return w;}
    static NativeSummaryPacket packet(const SummaryWord& w){NativeSummaryPacket p;std::copy(w.w,w.w+8,p.words.begin());return p;}
    std::pair<NativeSummaryPacket,std::uint64_t> submit(std::uint32_t actor,std::uint32_t die,std::uint32_t lane,std::uint32_t op,const NativeSummaryPacket& p,std::uint64_t expected=0){
        require(session_&&actor<actors_.size()&&die<layout_.count(),"HBM command context");
        auto& a=actors_[actor];auto& ring=a.rings[die];require(ring.ticket<UINT64_MAX,"HBM queue ticket exhausted");
        const auto index=(ring.ticket&7)*2;SummaryWord descriptor={};descriptor.w[0]=op|(std::uint64_t(lane)<<32);descriptor.w[1]=slot(p.node());descriptor.w[2]=expected;
        ring.commands[index]=word(p);ring.commands[index+1]=descriptor;SummaryWord done={};
        {
            std::lock_guard<std::mutex> lock(dies_[die].mutex);
            auto& device=dies_[die];
            if(push_&&(op==owner_install||op==owner_subscribe||op==owner_validate)){
                dieroute_owner_publish_hbm(ring.commands,topology_.data(),device.owners.data(),device.registry.data(),device.dirty.data(),
                    ring.responses,device.updates,&device.control,&done,nodes_.size(),lanes_,die,layout_.count(),session_,8,8,8,dirty_capacity_,
                    ring.ticket,ring.ticket+1,ring.ticket,ring.ticket,device.update_ticket,device.update_ticket,1,0,0,0);
                require(done.w[0]==ring.ticket+1&&done.w[1]==ring.ticket+1&&done.w[2]==device.update_ticket&&done.w[3]==1&&done.w[4]==0&&done.w[5]==0&&done.w[6]==0&&done.w[7]==session_,"HBM publisher command completion");
            }else{
                dieroute_summary_hbm(ring.commands,topology_.data(),device.owners.data(),device.shadows.data(),ring.responses,&done,
                    nodes_.size(),lanes_,die,layout_.count(),session_,8,8,ring.ticket,ring.ticket+1,ring.ticket,ring.ticket,1);
                require(done.w[0]==ring.ticket+1&&done.w[1]==ring.ticket+1&&done.w[2]==1&&done.w[3]==0&&done.w[6]==session_&&done.w[7]==0,"HBM endpoint completion");
            }
        }
        auto reply=ring.responses[index],receipt=ring.responses[index+1];
        require(receipt.w[1]==ring.ticket&&receipt.w[2]==descriptor.w[0]&&receipt.w[3]==descriptor.w[1]&&receipt.w[5]==0&&receipt.w[6]==0&&receipt.w[7]==0,"HBM endpoint receipt");
        a.frames.push_back({die,{ring.commands[index],descriptor,reply,receipt,done}});++ring.ticket;
        return {packet(reply),receipt.w[0]};
    }
public:
    NativeSummaryHbm(NativeOwnerLayout layout,std::vector<std::uint32_t> nodes,std::uint32_t lanes,bool push=false):layout_(std::move(layout)),nodes_(std::move(nodes)),actors_(lanes+1),published_(nodes_.size()),lanes_(lanes),push_(push){
        require(lanes&&lanes<=8&&std::is_sorted(nodes_.begin(),nodes_.end())&&std::adjacent_find(nodes_.begin(),nodes_.end())==nodes_.end(),"HBM topology/lane domain");
        if(push_){while(dirty_capacity_<nodes_.size()){require(dirty_capacity_<=UINT32_MAX/2,"HBM dirty capacity overflow");dirty_capacity_*=2;}require(dirty_capacity_<=UINT32_MAX/65,"HBM pump visit budget overflow");}
        for(auto n:nodes_){auto mask=layout_.membership(n);require(mask&(mask-1),"HBM interior slot");topology_.push_back(n|(std::uint64_t(mask)<<32));}
        for(unsigned d=0;d<layout_.count();++d){dies_[d].owners.resize(nodes_.size());dies_[d].shadows.resize(nodes_.size()*lanes);if(push_){dies_[d].registry.resize(nodes_.size());dies_[d].dirty.resize(dirty_capacity_);}}
    }
    bool push_enabled()const{return push_;}
    std::uint32_t controller()const{return lanes_;}
    std::uint64_t session()const{return session_;}
    const auto& topology()const{return topology_;}
    auto take_frames(std::uint32_t actor){auto result=std::move(actors_.at(actor).frames);actors_[actor].frames.clear();return result;}
    void reset(std::uint64_t session){
        require(session>session_,"HBM session must increase");for(auto& a:actors_){require(a.frames.empty(),"undrained HBM frames");for(auto& r:a.rings)r=Ring{};}
        session_=session;for(auto& p:published_)p.reset();
        for(auto& d:dies_)d.update_ticket=0;
    }
    void publish(const NativeRouteState& state){
        require(layout_.same(state.layout()),"HBM publication layout");
        for(std::size_t s=0;s<nodes_.size();++s){const auto n=nodes_[s];auto value=NativeWorkerShadows::authority(state,n);
            if(published_[s]&&*published_[s]==value)continue;
            auto owner=layout_.owner(n),mask=layout_.membership(n);unsigned worker=0;while(worker==owner||!(mask&(1u<<worker)))++worker;
            auto p=NativeSummaryPacket::make(session_,s+1,n,owner,worker,3,value);
            auto response=submit(controller(),owner,0,owner_install,p,published_[s]?published_[s]->version:0);
            require(response.second==summary_ok,"HBM owner publication rejected");published_[s]=value;
        }
    }
    // Install only values exported by the whole-net authority. The initial
    // batch is a projection of its sparse zero/session state; later batches
    // contain unchanged kernel deltas, coalesced by node between barriers.
    void publish_deltas(const std::vector<SummaryWord>& deltas){
        std::uint64_t previous=UINT64_MAX;
        for(const auto& d:deltas){auto n=std::uint32_t(d.w[1]);auto s=slot(n);auto owner=layout_.owner(n),mask=layout_.membership(n);
            require(d.w[0]==session_&&d.w[1]==(n|(std::uint64_t(owner)<<32))&&d.w[6]==mask&&!d.w[7]&&(previous==UINT64_MAX||previous<n),"HBM hardware publication identity");previous=n;
            NativeSummary value{d.w[2],d.w[3],d.w[4]};if(published_[s]&&*published_[s]==value)continue;
            unsigned worker=0;while(worker==owner||!(mask&(1u<<worker)))++worker;
            auto packet=NativeSummaryPacket::make(session_,s+1,n,owner,worker,3,value);
            auto response=submit(controller(),owner,0,owner_install,packet,published_[s]?published_[s]->version:0);
            require(response.second==summary_ok,"HBM hardware owner publication rejected");published_[s]=value;
        }
    }
    NativeSummaryPacket fetch(std::uint32_t lane,const NativeSummaryPacket& request){auto r=submit(lane,request.owner(),push_?lane:0,push_?owner_subscribe:owner_fetch,request);require(r.second==summary_ok,"HBM owner fetch rejected");return r.first;}
    std::vector<NativeSummaryPacket> drain(std::uint32_t lane){
        require(push_&&lane<lanes_&&session_,"HBM publisher drain context");std::vector<NativeSummaryPacket> result;
        if(nodes_.empty())return result;
        std::uint64_t filter=0;for(unsigned worker=0;worker<layout_.count();++worker)filter|=UINT64_C(1)<<(worker*8+lane);
        auto& actor=actors_[lane];
        for(unsigned die=0;die<layout_.count();++die){
            auto& device=dies_[die];auto& ring=actor.rings[die];std::lock_guard<std::mutex> lock(device.mutex);
            for(;;){
                require(device.update_ticket<=UINT64_MAX-8,"HBM publication ticket exhausted");
                auto before=device.control;SummaryWord done={},config={};
                config.w[0]=filter;config.w[1]=8;config.w[2]=dirty_capacity_*65;config.w[3]=config.w[4]=device.update_ticket;config.w[5]=ring.ticket;
                dieroute_owner_publish_hbm(ring.commands,topology_.data(),device.owners.data(),device.registry.data(),device.dirty.data(),ring.responses,
                    device.updates,&device.control,&done,nodes_.size(),lanes_,die,layout_.count(),session_,8,8,8,dirty_capacity_,
                    ring.ticket,ring.ticket,ring.ticket,ring.ticket,device.update_ticket,device.update_ticket,0,8,dirty_capacity_*65,filter);
                require(done.w[0]==ring.ticket&&done.w[1]==ring.ticket&&done.w[2]>=device.update_ticket&&done.w[2]-device.update_ticket==done.w[4]&&done.w[3]==0&&done.w[4]<=8&&done.w[5]<config.w[2]&&done.w[6]==0&&done.w[7]==session_,"HBM publisher pump completion");
                actor.frames.push_back({die,{config,before,device.control,done,{}},4});
                for(auto t=device.update_ticket;t<done.w[2];++t){
                    auto value=device.updates[(t&7)*2],metadata=device.updates[(t&7)*2+1];
                    require(metadata.w[0]==lane&&metadata.w[1]<nodes_.size()&&metadata.w[2]==value.w[4],"HBM publication metadata");
                    for(unsigned i=3;i<8;++i)require(metadata.w[i]==0,"HBM publication reserved metadata");
                    auto p=packet(value);require(p.session()==session_&&p.owner()==die&&p.kind()==3&&p.node()==nodes_[metadata.w[1]]&&value.w[5]==t+1,"HBM publication identity");
                    actor.frames.push_back({die,{value,metadata,{},{},{}},5});result.push_back(p);
                }
                device.update_ticket=done.w[2];if(done.w[4]<8)break;
            }
        }
        std::sort(result.begin(),result.end(),[](const auto& a,const auto& b){return std::make_pair(a.worker(),a.node())<std::make_pair(b.worker(),b.node());});
        return result;
    }
    template<class Visitor>void subscriptions(Visitor visit)const{
        if(!push_)return;
        for(std::size_t s=0;s<nodes_.size();++s){auto n=nodes_[s],die=layout_.owner(n);const auto& r=dies_[die].registry[s];
            require(r.w[0]==session_&&r.w[2]==0&&r.w[3]==0,"HBM final subscription tail");visit(die,n,r.w[1],r.w[2],r.w[3]);}
        for(unsigned die=0;die<layout_.count();++die)require(nodes_.empty()||(dies_[die].control.w[0]==session_&&dies_[die].control.w[1]==dies_[die].control.w[2]),"HBM final dirty queue not empty");
    }
    NativeSummary inspect(std::uint32_t lane,const NativeSummaryPacket& request){auto r=submit(lane,request.worker(),lane,shadow_inspect,request);require(r.second==summary_ok,"HBM subscribed cache lookup failed");return r.first.value();}
    std::uint64_t receive(std::uint32_t lane,const NativeSummaryPacket& p){return submit(lane,p.worker(),lane,shadow_receive,p).second;}
    std::vector<std::size_t> validate(std::uint32_t lane,const std::vector<NativeShadowRead>& reads){
        std::vector<std::size_t> stale;
        for(std::size_t i=0;i<reads.size();++i){const auto& r=reads[i];auto p=NativeSummaryPacket::make(session_,i+1,r.node,layout_.owner(r.node),r.worker,2,r.seen);
            auto reply=submit(lane,p.owner(),0,owner_validate,p);require(reply.second==summary_ok||reply.second==summary_stale,"HBM validation failed");if(reply.second==summary_stale)stale.push_back(i);}
        return stale;
    }
    template<class Owner,class Cache>void inventory(Owner owner,Cache cache)const{
        for(std::size_t s=0;s<nodes_.size();++s){auto n=nodes_[s],die=layout_.owner(n);const auto& r=dies_[die].owners[s];require(r.w[0]==session_&&r.w[4]==topology_[s],"HBM final owner missing");owner(die,n,NativeSummary{r.w[1],r.w[2],r.w[3]});
            for(unsigned d=0;d<layout_.count();++d)for(unsigned lane=0;lane<lanes_;++lane){const auto& c=dies_[d].shadows[lane*nodes_.size()+s];if(c.w[0]==session_){require(c.w[4]==topology_[s],"HBM final cache identity");cache(lane,d,n,NativeSummary{c.w[1],c.w[2],c.w[3]});}}
        }
    }
};
// CPU keeps subscription keys and accounting only. Every cached value used by
// the search/refresh comes from the endpoint, never from a host value cache.
class NativeHbmShadows final : public NativeWorkerShadows {
    NativeSummaryHbm& fabric_;std::uint32_t lane_;
    NativeOwnerLayout layout_;std::uint64_t session_=0,serial_=0;
    std::array<std::set<std::uint32_t>,8> subscriptions_;
    std::vector<NativeSummaryPacket> messages_;
    static void require(bool x,const char* why){if(!x)throw std::logic_error(why);}
    std::uint64_t next(){if(serial_==UINT64_MAX)throw std::overflow_error("HBM shadow serial exhausted");return ++serial_;}
    NativeSummaryPacket request(std::uint32_t worker,std::uint32_t node,std::uint64_t serial)const{return NativeSummaryPacket::make(session_,serial,node,layout_.owner(node),worker,1);}
public:
    NativeHbmShadows(NativeSummaryHbm& fabric,std::uint32_t lane):fabric_(fabric),lane_(lane){}
    void reset(NativeOwnerLayout layout,std::uint64_t session)override{
        NativeWorkerShadows::reset(layout,session);require(session==fabric_.session(),"HBM cache session mismatch");layout_=std::move(layout);session_=session;serial_=0;messages_.clear();for(auto& s:subscriptions_)s.clear();
    }
    std::size_t size()const override{std::size_t n=0;for(const auto& s:subscriptions_)n+=s.size();return n;}
    std::vector<NativeSummaryPacket> take_messages()override{auto r=std::move(messages_);messages_.clear();return r;}
    bool receive(const NativeSummaryPacket& p)override{
        auto status=fabric_.receive(lane_,p);
        if(status==summary_stale){++metrics.stale;return false;}
        if(status==summary_duplicate){++metrics.duplicates;return false;}
        require(status==summary_ok,"HBM summary delivery rejected");subscriptions_.at(p.worker()).insert(p.node());++metrics.received;return true;
    }
    std::pair<NativeSummary,bool> query(const NativeRouteState& snapshot,std::uint32_t worker,std::uint32_t n)override{
        require(layout_.same(snapshot.layout())&&worker<layout_.count(),"HBM query context");
        if(subscriptions_[worker].count(n)){++metrics.hits;return {fabric_.inspect(lane_,request(worker,n,std::max<std::uint64_t>(1,serial_))),true};}
        auto req=request(worker,n,next()),reply=fabric_.fetch(lane_,req);messages_.push_back(req);messages_.push_back(reply);
        require(receive(reply),"HBM cold reply rejected");++metrics.fetches;return {reply.value(),false};
    }
    std::vector<NativeSummaryPacket> refresh(const NativeRouteState& state)override{
        require(layout_.same(state.layout())&&messages_.empty(),"HBM refresh context");
        if(fabric_.push_enabled()){
            for(auto p:fabric_.drain(lane_)){p.words[5]=next();require(subscriptions_.at(p.worker()).count(p.node())&&receive(p),"HBM push delivery rejected");messages_.push_back(p);++metrics.updates;}
            return take_messages();
        }
        for(unsigned worker=0;worker<layout_.count();++worker)for(auto n:subscriptions_[worker]){++metrics.scans;
            auto req=request(worker,n,std::max<std::uint64_t>(1,serial_));auto old=fabric_.inspect(lane_,req),current=fabric_.fetch(lane_,req).value();
            require(current.version>=old.version,"HBM authority regressed");
            if(!(current==old)){auto p=NativeSummaryPacket::make(session_,next(),n,layout_.owner(n),worker,3,current);require(receive(p),"HBM publication rejected");messages_.push_back(p);++metrics.updates;}}
        return take_messages();
    }
};
}
