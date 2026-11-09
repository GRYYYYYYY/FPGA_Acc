#include "owner_publish_hbm.hpp"
#include "native_csr_io.hpp"
#include <algorithm>
#include <iostream>
#include <memory>
#include <vector>
using namespace dieroute;
using namespace dieroute::native;
static SummaryWord decode(const unsigned char* p){SummaryWord w={};for(unsigned i=0;i<8;++i)w.w[i]=le64(p+i*8);return w;}
static bool equal(const SummaryWord& a,const SummaryWord& b){return !std::memcmp(&a,&b,64);}
struct Context {
    std::vector<SummaryWord> owner,registry,cache;
    std::vector<std::uint32_t> dirty;
    SummaryWord commands[16]={},responses[16]={},updates[16]={},ctl={},done={};
    SummaryWord receiver_commands[16]={},receiver_responses[16]={};
    std::uint64_t ticket=0,ur=0,uw=0,receiver_ticket=0,session=0,launches=0,visits=0,emitted=0,receiver_calls=0;
    unsigned die,lanes,capacity=1;const std::vector<std::uint64_t>& topo;
    Context(const std::vector<std::uint64_t>& t,unsigned d,unsigned l):owner(t.size()),registry(t.size()),cache(t.size()*l),die(d),lanes(l),topo(t){while(capacity<t.size())capacity*=2;dirty.resize(capacity);}
    void reset(std::uint64_t s){session=s;ticket=ur=uw=receiver_ticket=0;}
    void invoke(unsigned count,unsigned max_updates,std::uint64_t filter){
        dieroute_owner_publish_hbm(commands,topo.data(),owner.data(),registry.data(),dirty.data(),responses,updates,&ctl,&done,topo.size(),lanes,die,3,session,8,8,8,capacity,ticket,ticket+count,ticket,ticket,ur,uw,count,max_updates,capacity*65,filter);
        ++launches;check(done.w[6]==0&&done.w[7]==session&&done.w[3]==count,"publisher replay completion");ticket=done.w[0];check(done.w[1]==ticket,"publisher reply count");uw=done.w[2];visits+=done.w[5];emitted+=done.w[4];
    }
    void receiver(SummaryWord p,SummaryWord descriptor,const SummaryWord& expected,std::uint64_t status){
        auto index=(receiver_ticket&7)*2;receiver_commands[index]=p;receiver_commands[index+1]=descriptor;SummaryWord result={};
        dieroute_summary_hbm(receiver_commands,topo.data(),owner.data(),cache.data(),receiver_responses,&result,topo.size(),lanes,die,3,session,8,8,receiver_ticket,receiver_ticket+1,receiver_ticket,receiver_ticket,1);
        check(result.w[2]==1&&!result.w[3]&&receiver_responses[index+1].w[0]==status&&equal(receiver_responses[index],expected),"receiver/query differs from audited source trace");++receiver_ticket;++receiver_calls;
    }
};
int main(int argc,char** argv){try{
    check(argc==6,"usage: replay_owner_publish_hbm FRAMES TOPOLOGY ARCH LANES NEW_OUTPUT");const auto arch=fingerprint(argv[3]);const auto lanes=std::stoul(argv[4]);check(lanes&&lanes<=8,"lane range");fs::path out=argv[5];check(fs::create_directory(out),"output already exists");
    Container source(argv[1],0x44520024,384,arch),directory(argv[2],0x44520023,8,arch);std::vector<std::uint64_t> topo;for(std::uint64_t s=0;s<directory.count;++s)topo.push_back(le64(directory.data+s*8));check(!topo.empty(),"empty topology");
    std::vector<std::unique_ptr<Context>> contexts;for(unsigned d=0;d<3;++d)contexts.emplace_back(new Context(topo,d,lanes));
    Writer events(out/"events.bin",0x44520025,0,arch);std::ofstream owners(out/"owners.csv"),caches(out/"caches.csv"),subscriptions(out/"subscriptions.csv");
    owners<<"repeat,owner,node,occupancy,history,version\n";caches<<"repeat,lane,worker,node,occupancy,history,version\n";subscriptions<<"repeat,owner,node,subscribers,pending,queued\n";
    std::uint64_t session=0,call=0,source_index=0,actor=0,reason=0,repeats=0,commands=0,refreshes=0,removed_scans=0,pushed=0;
    auto emit=[&](unsigned die,unsigned type,unsigned ordinal,const std::array<SummaryWord,5>& payload){std::array<unsigned char,384> bytes{};const std::uint64_t meta[]={session-1,source_index,actor,reason,die,type,call,ordinal};for(unsigned j=0;j<8;++j)put64(bytes.data()+j*8,meta[j]);for(unsigned i=0;i<5;++i)for(unsigned j=0;j<8;++j)put64(bytes.data()+64+i*64+j*8,payload[i].w[j]);events.append(bytes.data(),bytes.size());};
    auto finish=[&]{if(!session)return;for(const auto& ptr:contexts)check(ptr->ctl.w[1]==ptr->ctl.w[2],"final dirty queue not drained");
        for(std::size_t s=0;s<topo.size();++s){auto mask=topo[s]>>32;unsigned owner=0;while(!(mask&(1u<<owner)))++owner;const auto node=std::uint32_t(topo[s]);const auto& c=*contexts[owner];const auto& value=c.owner[s];const auto& sub=c.registry[s];check(value.w[0]==session&&sub.w[0]==session&&!sub.w[2]&&!sub.w[3],"final owner/session/pending invariant");
            owners<<session-1<<','<<owner<<','<<node<<','<<value.w[1]<<','<<value.w[2]<<','<<value.w[3]<<'\n';subscriptions<<session-1<<','<<owner<<','<<node<<','<<sub.w[1]<<','<<sub.w[2]<<','<<sub.w[3]<<'\n';
            for(unsigned d=0;d<3;++d)for(unsigned l=0;l<lanes;++l){const auto& record=contexts[d]->cache[l*topo.size()+s];if(record.w[0]==session){check(record.w[1]==value.w[1]&&record.w[2]==value.w[2]&&record.w[3]==value.w[3],"final cache differs from owner");check(sub.w[1]&(1ull<<(d*8+l)),"receiver lacks owner subscription");caches<<session-1<<','<<l<<','<<d<<','<<node<<','<<record.w[1]<<','<<record.w[2]<<','<<record.w[3]<<'\n';}}
        }++repeats;
    };
    for(std::uint64_t i=0;i<source.count;){const auto* f=source.data+i*384;source_index=i;actor=le64(f+24);reason=le64(f+40);const auto s=le64(f)+1;
        if(s!=session){finish();check(s==session+1,"session order");session=s;call=0;for(auto& c:contexts)c->reset(session);}
        if(reason==2){
            check(actor<lanes,"refresh actor");++refreshes;std::vector<std::array<SummaryWord,3>> expected;
            auto end=i;
            while(end<source.count){const auto* g=source.data+end*384;bool same=true;for(unsigned j=0;j<6;++j)same&=le64(g+j*8)==le64(f+j*8);if(!same)break;
                auto p=decode(g+64),d=decode(g+128),r=decode(g+192);auto op=std::uint32_t(d.w[0]);if(op==shadow_receive)expected.push_back({p,d,r});else{check(op==owner_fetch||op==shadow_inspect,"unexpected refresh op");++removed_scans;}++end;
            }
            std::vector<std::pair<SummaryWord,SummaryWord>> pending;
            std::uint64_t filter=0;for(unsigned d=0;d<3;++d)filter|=1ull<<(d*8+actor);
            for(auto& ptr:contexts){auto& c=*ptr;for(;;){auto before=c.ctl;SummaryWord config={};config.w[0]=filter;config.w[1]=8;config.w[2]=c.capacity*65;config.w[3]=c.ur;config.w[4]=c.uw;config.w[5]=c.ticket;
                    c.invoke(0,8,filter);emit(c.die,1,0,{config,before,c.ctl,c.done,{}});
                    unsigned ordinal=0;while(c.ur<c.uw){auto index=(c.ur&7)*2;auto p=c.updates[index],m=c.updates[index+1];check(m.w[0]==actor&&p.w[5]==c.ur+1,"publisher target/serial");emit(c.die,2,ordinal++,{p,m,{},{},{}});pending.emplace_back(p,m);++c.ur;}
                    ++call;if(c.done.w[4]==0)break;
                }}
            auto key=[](const SummaryWord& p){return std::make_pair(unsigned((p.w[1]>>40)&255),std::uint32_t(p.w[1]));};
            std::sort(pending.begin(),pending.end(),[&](const auto& a,const auto& b){return key(a.first)<key(b.first);});check(pending.size()==expected.size(),"changed-only publications differ from audited scan backend");
            for(std::size_t j=0;j<pending.size();++j){auto packet=pending[j].first;packet.w[5]=expected[j][0].w[5];check(equal(packet,expected[j][0]),"publisher values/order differ from source delivery");const auto worker=(packet.w[1]>>40)&255;check(pending[j].second.w[1]==expected[j][1].w[1],"publisher slot envelope");contexts[worker]->receiver(packet,expected[j][1],expected[j][2],summary_ok);++pushed;}
            i=end;continue;
        }
        auto p=decode(f+64),d=decode(f+128),r=decode(f+192),ack=decode(f+256);auto die=le64(f+56);check(die<3,"die range");auto& c=*contexts[die];auto op=std::uint32_t(d.w[0]);
        if(op==owner_install||op==owner_fetch||op==owner_validate){
            if(op==owner_fetch){check(actor<lanes&&reason==0,"unexpected source fetch");d.w[0]=owner_subscribe|(actor<<32);}
            auto index=(c.ticket&7)*2;c.commands[index]=p;c.commands[index+1]=d;c.invoke(1,0,0);check(c.responses[index+1].w[0]==ack.w[0]&&equal(c.responses[index],r),"owner reply/validation differs from source trace");emit(die,0,0,{p,d,c.responses[index],c.responses[index+1],c.done});++call;++commands;
        }else{check(reason==0&&(op==shadow_receive||op==shadow_inspect),"unexpected receiver op");c.receiver(p,d,r,ack.w[0]);}
        ++i;
    }
    finish();events.finish_dynamic(384);for(auto stream:{&owners,&caches,&subscriptions}){stream->close();check(bool(*stream),"inventory write failure");}
    std::uint64_t visits=0,launches=0,emitted=0,receiver=0;for(const auto& c:contexts){visits+=c->visits;launches+=c->launches;emitted+=c->emitted;receiver+=c->receiver_calls;}
    check(emitted==pushed,"publication accounting");std::cout<<"{\"passed\":true,\"repeats\":"<<repeats<<",\"owner_commands\":"<<commands<<",\"publisher_launches\":"<<launches<<",\"receiver_launches\":"<<receiver<<",\"refresh_groups\":"<<refreshes<<",\"removed_lookup_commands\":"<<removed_scans<<",\"dirty_queue_visits\":"<<visits<<",\"published_updates\":"<<pushed<<",\"boundary_slots\":"<<topo.size()<<",\"scope\":\"C-model replacement replay of audited native commands; source search not rerun; CPU dispatches output records; no board performance claim\"}\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
