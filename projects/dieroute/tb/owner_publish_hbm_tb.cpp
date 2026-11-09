#include "owner_publish_hbm.hpp"
#include <iostream>
#include <stdexcept>
#include <cstring>
using namespace dieroute;
static void check(bool x,const char* why){if(!x)throw std::runtime_error(why);}
static SummaryWord packet(std::uint64_t session,unsigned node,unsigned owner,unsigned worker,unsigned kind,std::uint64_t value=0,std::uint64_t version=0){SummaryWord p={};p.w[0]=session;p.w[1]=node|(std::uint64_t(owner)<<32)|(std::uint64_t(worker)<<40)|(std::uint64_t(kind)<<48);p.w[2]=value;p.w[4]=version;p.w[5]=1;return p;}
struct Fixture {
    SummaryWord cmd[32]={},owners[16]={},subs[16]={},reply[32]={},updates[32]={},control={},done={};std::uint64_t topo[16]={};std::uint32_t dirty[16]={};
    std::uint64_t cr=14,cw=14,rr=11,rw=11,ur=7,uw=7,session=1;unsigned die=0;static unsigned launches;
    Fixture(){topo[0]=10|(std::uint64_t(7)<<32);topo[1]=20|(std::uint64_t(3)<<32);topo[2]=30|(std::uint64_t(6)<<32);topo[3]=40|(std::uint64_t(7)<<32);}
    void push(SummaryWord p,unsigned op,unsigned slot=0,unsigned lane=0,std::uint64_t expected=0){check(cw-cr<8,"test input full");auto i=(cw++&7)*2;cmd[i]=p;cmd[i+1]={};cmd[i+1].w[0]=op|(std::uint64_t(lane)<<32);cmd[i+1].w[1]=slot;cmd[i+1].w[2]=expected;}
    void run(unsigned commands=8,unsigned publications=0,std::uint64_t filter=~std::uint64_t(0),unsigned visits=64,unsigned expected_error=0){
        dieroute_owner_publish_hbm(cmd,topo,owners,subs,dirty,reply,updates,&control,&done,4,2,die,3,session,8,8,8,8,cr,cw,rr,rw,ur,uw,commands,publications,visits,filter);++launches;
        check(done.w[6]==expected_error&&done.w[7]==session,"launch/queue status");cr=done.w[0];rw=done.w[1];uw=done.w[2];
    }
    SummaryWord pop(unsigned status){check(rr<rw,"missing owner reply");auto i=(rr++&7)*2;check(reply[i+1].w[0]==status,"owner operation status");return reply[i];}
    SummaryWord update(unsigned lane,unsigned slot,std::uint64_t version){check(ur<uw,"missing publication");auto i=(ur&7)*2;check(updates[i+1].w[0]==lane&&updates[i+1].w[1]==slot&&updates[i+1].w[2]==version&&updates[i].w[4]==version&&updates[i].w[5]==ur+1,"publication address/version/sequence");++ur;return updates[i];}
};
unsigned Fixture::launches=0;
int main(){try{
    Fixture f;auto a=packet(1,10,0,1,3,1,1);f.push(packet(1,10,0,1,1),owner_subscribe);f.run();f.pop(summary_missing);check(!f.subs[0].w[1],"missing owner created subscription");
    f.push(a,owner_install);f.push(packet(1,10,0,1,1),owner_subscribe,0,0);f.push(packet(1,10,0,2,1),owner_subscribe,0,1);f.run();f.pop(summary_ok);check(f.pop(summary_ok).w[2]==1&&f.pop(summary_ok).w[2]==1,"atomic subscription snapshot");check(f.subs[0].w[1]==((1ull<<8)|(1ull<<17))&&!f.subs[0].w[2]&&f.control.w[1]==f.control.w[2],"initial subscription queued redundant update");
    auto b=a;b.w[2]=2;b.w[4]=2;auto c=b;c.w[2]=3;c.w[4]=3;
    f.push(b,owner_install,0,0,1);f.push(c,owner_install,0,0,2);f.run();f.pop(summary_ok);f.pop(summary_ok);check(f.control.w[2]-f.control.w[1]==1&&f.subs[0].w[2]==f.subs[0].w[1],"coalescing duplicated dirty slot");
    auto before=f.subs[0];f.run(0,8,1ull<<9);check(!f.done.w[4]&&f.done.w[5]==1&&!std::memcmp(&before,&f.subs[0],64),"filtered subscriber lost dirty bit or unbounded scan");
    f.run(0,8,1ull<<8);auto p=f.update(0,0,3);check(p.w[2]==3&&((p.w[1]>>40)&255)==1&&f.subs[0].w[2]==(1ull<<17),"selected subscriber publication");
    auto d=c;d.w[2]=0;d.w[4]=4;f.push(d,owner_install,0,0,3);f.run();f.pop(summary_ok);check(f.control.w[2]-f.control.w[1]==1,"dirty slot enqueued twice during delayed subscriber");
    f.run(0,8);check(f.update(0,0,4).w[2]==0&&f.update(1,0,4).w[2]==0&&f.control.w[1]==f.control.w[2]&&!f.subs[0].w[2],"latest tombstone multicast");
    f.push(d,owner_install,0,0,4);f.push(packet(1,10,0,1,1),owner_subscribe);f.run();f.pop(summary_duplicate);f.pop(summary_ok);check(!f.subs[0].w[2],"idempotent commands marked dirty");
    // Fill all output credits with repeated versions, leaving a newer pending
    // value. Owner installation and response delivery must remain independent.
    for(unsigned v=5;v<=8;++v){auto next=d;next.w[2]=v;next.w[4]=v;f.push(next,owner_install,0,0,v-1);f.run(8,8);f.pop(summary_ok);}
    check(f.uw-f.ur==8,"test did not fill publication queue");auto next=d;next.w[2]=9;next.w[4]=9;f.push(next,owner_install,0,0,8);f.run(8,8);f.pop(summary_ok);check(f.done.w[4]==0&&f.subs[0].w[2]==f.subs[0].w[1],"full egress lost pending update");
    for(unsigned v=5;v<=8;++v){f.update(0,0,v);f.update(1,0,v);}f.run(0,1);check(f.done.w[4]==1&&f.subs[0].w[2],"publication budget ignored");f.update(0,0,9);f.run(0,8);f.update(1,0,9);
    // Backpressure on replies must not consume even a subscribe request.
    for(unsigned i=0;i<8;++i)f.push(packet(1,10,0,1,1),owner_fetch);f.run();
    f.push(packet(1,10,0,1,1),owner_subscribe,0,1);auto cr=f.cr;f.run();check(f.cr==cr&&!(f.subs[0].w[1]&(1ull<<9)),"reply backpressure mutated subscription");
    for(unsigned i=0;i<8;++i)f.pop(summary_ok);f.run();f.pop(summary_ok);check(f.subs[0].w[1]&(1ull<<9),"subscribe did not resume");
    // Independent slots and filters survive circular queue wrap and bounded
    // one-step visits. A late subscriber receives the current owner immediately.
    auto e=packet(1,20,0,1,3,1,1);f.push(e,owner_install,1);f.push(packet(1,20,0,1,1),owner_subscribe,1,1);f.run();f.pop(summary_ok);f.pop(summary_ok);
    e.w[2]=2;e.w[4]=2;f.push(e,owner_install,1,0,1);next.w[4]=10;f.push(next,owner_install,0,0,9);f.run();f.pop(summary_ok);f.pop(summary_ok);
    f.run(0,8,1ull<<9,1);check(f.done.w[5]==1&&f.done.w[4]==1,"visit budget");f.update(1,1,2);f.run(0,8,1ull<<9);f.update(1,0,10);check(f.control.w[2]-f.control.w[1]==1,"filtered pending slot lost");
    f.push(packet(1,10,0,2,1),owner_subscribe,0,0);f.run();check(f.pop(summary_ok).w[4]==10&&!(f.subs[0].w[2]&(1ull<<16)),"late subscriber snapshot duplicated as pending");f.run(0,8);f.update(0,0,10);f.update(1,0,10);
    // CAS/version checks fail before owner/registry mutation.
    before=f.owners[0];auto beforeSub=f.subs[0];next.w[4]=11;f.push(next,owner_install,0,0,8);f.push(next,owner_validate);f.push(packet(1,10,0,1,1),owner_subscribe,1);f.run();f.pop(summary_compare_failed);f.pop(summary_stale);f.pop(summary_bad_address);check(!std::memcmp(&before,&f.owners[0],64)&&!std::memcmp(&beforeSub,&f.subs[0],64),"rejected command changed state");
    // Exhausted dirty tickets reject an installation atomically.
    auto saved=f.control;f.control.w[1]=f.control.w[2]=UINT64_MAX;f.push(next,owner_install,0,0,10);f.run();f.pop(publisher_queue_exhausted);check(!std::memcmp(&before,&f.owners[0],64)&&!std::memcmp(&beforeSub,&f.subs[0],64),"dirty ticket exhaustion partially installed owner");f.control=saved;
    // Session rollover cancels old subscriptions/dirty work; delayed packets
    // and backwards session requests cannot mutate the new generation.
    f.push(next,owner_install,0,0,10);f.run();f.pop(summary_ok);check(f.subs[0].w[2],"session test requires pending state");f.session=2;f.run(0,8);check(f.control.w[1]==f.control.w[2]&&!f.done.w[4],"old pending state escaped generation");f.push(next,owner_install,0,0,0);f.run();f.pop(summary_stale);
    f.push(packet(2,10,0,1,3),owner_install);f.push(packet(2,10,0,1,1),owner_subscribe);f.run();f.pop(summary_ok);f.pop(summary_ok);check(f.subs[0].w[1]==(1ull<<8)&&f.owners[0].w[3]==0,"session bootstrap retained stale subscribers");f.session=1;f.run(0,0,~0ull,64,1);f.session=2;
    // Future/corrupt registry values and dirty queue entries fail closed.
    beforeSub=f.subs[0];f.subs[0].w[1]|=1;f.push(packet(2,10,0,1,1),owner_subscribe);f.run();f.pop(summary_bad_record);f.subs[0]=beforeSub;
    f.push(packet(2,10,0,1,3,1,1),owner_install,0,0,0);f.run();f.pop(summary_ok);f.dirty[f.control.w[1]&7]=99;f.run(0,8,~0ull,64,2);check(!f.done.w[4]&&f.subs[0].w[2],"corrupt dirty address mutated pending state");
    Fixture g;g.die=1;g.push(packet(1,30,1,2,3),owner_install,2);g.push(packet(1,30,1,2,1),owner_subscribe,2,1);g.run();g.pop(summary_ok);g.pop(summary_ok);g.push(packet(1,30,1,2,3,2,1),owner_install,2);g.run(8,8);g.pop(summary_ok);check(g.update(1,2,1).w[2]==2,"nonzero owner routing");
    g.push(packet(1,30,1,2,3,3,2),owner_install,2,0,1);g.run();g.pop(summary_ok);
    beforeSub=g.subs[2];g.run(0,8,~0ull,0);check(!g.done.w[5]&&!std::memcmp(&beforeSub,&g.subs[2],64),"zero visits changed pending state");
    g.ur=g.uw=UINT64_MAX;g.run(0,8);check(g.uw==UINT64_MAX&&!g.done.w[4]&&!std::memcmp(&beforeSub,&g.subs[2],64),"publication ticket overflow");
    g.rr=g.rw=UINT64_MAX;g.push(packet(1,30,1,2,1),owner_subscribe,2,0);cr=g.cr;g.run();check(g.cr==cr&&!(g.subs[2].w[1]&(1ull<<16)),"reply ticket overflow mutated subscription");
    std::cout<<"owner publisher: atomic subscribe, coalescing, multicast, filtered deferred lanes, queue wrap/credit/budgets, sessions, rejection and final drain passed; launches="<<Fixture::launches<<'\n';
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
