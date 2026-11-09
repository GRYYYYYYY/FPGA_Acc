#include "summary_hbm.hpp"
#include <iostream>
#include <stdexcept>
#include <cstring>
using namespace dieroute;
static void require(bool ok,const char* what){if(!ok)throw std::runtime_error(what);}
static SummaryWord packet(std::uint64_t session,std::uint32_t node,unsigned owner,unsigned worker,unsigned kind,std::uint64_t occ=0,std::uint64_t history=0,std::uint64_t version=0){
    SummaryWord p={};p.w[0]=session;p.w[1]=node|(std::uint64_t(owner)<<32)|(std::uint64_t(worker)<<40)|(std::uint64_t(kind)<<48);p.w[2]=occ;p.w[3]=history;p.w[4]=version;p.w[5]=17;return p;
}
struct Fixture {
    SummaryWord commands[32]={},owners[16]={},shadows[64]={},responses[32]={},done={};
    std::uint64_t topology[16]={},cr=14,cw=14,rr=11,rw=11,session=1;unsigned die=0;
    Fixture(){topology[0]=2|(std::uint64_t(3)<<32);topology[1]=3|(std::uint64_t(3)<<32);topology[2]=5|(std::uint64_t(6)<<32);}
    void push(SummaryWord p,unsigned op,unsigned slot=0,unsigned lane=0,std::uint64_t expected=0){
        require(cw-cr<8,"input overflow in test");auto i=(cw&7)*2;commands[i]=p;commands[i+1]={};commands[i+1].w[0]=op|(std::uint64_t(lane)<<32);commands[i+1].w[1]=slot;commands[i+1].w[2]=expected;++cw;
    }
    void run(unsigned steps=8){dieroute_summary_hbm(commands,topology,owners,shadows,responses,&done,3,2,die,3,session,8,8,cr,cw,rr,rw,steps);require(!done.w[3],"valid queue rejected");cr=done.w[0];rw=done.w[1];}
    SummaryWord pop(unsigned status){require(rr<rw,"missing response");auto i=(rr&7)*2;++rr;require(responses[i+1].w[0]==status,"wrong response status");return responses[i];}
};
int main(){try{
    Fixture f;auto a=packet(1,2,0,1,3,1,2,7),b=a;b.w[2]=2;b.w[4]=8;
    f.push(a,owner_install);f.push(packet(1,2,0,1,1),owner_fetch);f.push(a,owner_validate);f.push(b,owner_validate);f.run();
    f.pop(summary_ok);auto response=f.pop(summary_ok);require(response.w[2]==1&&response.w[3]==2&&response.w[4]==7&&((response.w[1]>>48)&255)==2,"owner fetch tuple");f.pop(summary_ok);f.pop(summary_stale);
    f.push(b,owner_install,0,0,6);f.push(b,owner_install,0,0,7);f.push(b,owner_install,0,0,8);f.run();f.pop(summary_compare_failed);f.pop(summary_ok);f.pop(summary_duplicate);require(f.owners[0].w[1]==2,"owner compare install");
    f.die=1;f.push(response,shadow_receive);f.push(response,shadow_receive);f.push(b,shadow_receive);f.push(a,shadow_receive);auto forged=b;forged.w[2]=9;f.push(forged,shadow_receive);f.push(packet(1,2,0,1,1),shadow_inspect);f.run();
    f.pop(summary_ok);f.pop(summary_duplicate);f.pop(summary_ok);f.pop(summary_stale);f.pop(summary_value_conflict);require(f.pop(summary_ok).w[2]==2,"persistent shadow inspect");
    // Eight full response slots block the next valid state mutation completely.
    for(unsigned i=0;i<8;++i)f.push(packet(1,2,0,1,1),shadow_inspect);f.run();
    auto next=b;next.w[2]=0;next.w[4]=9;f.push(next,shadow_receive);auto before=f.cr;f.run();require(f.cr==before&&f.done.w[2]==0&&f.shadows[0].w[1]==2,"backpressure lost command or mutated state");
    for(unsigned i=0;i<8;++i)f.pop(summary_ok);f.run();f.pop(summary_ok);require(f.shadows[0].w[1]==0&&f.shadows[0].w[3]==9,"tombstone lost after wrap/backpressure");
    // Slot/lane and immutable full membership prevent aliasing.
    f.push(next,shadow_receive,1);f.push(next,shadow_receive,0,2);forged=next;forged.w[1]|=std::uint64_t(1)<<56;f.push(forged,shadow_receive);forged=next;forged.w[6]=1;f.push(forged,shadow_receive);forged=next;forged.w[1]^=std::uint64_t(1)<<32;f.push(forged,shadow_receive);f.run();
    f.pop(summary_bad_address);f.pop(summary_bad_address);f.pop(summary_bad_packet);f.pop(summary_bad_packet);f.pop(summary_bad_role);
    // A fresh session logically invalidates old cache entries, including ABA.
    f.session=2;f.push(packet(2,2,0,1,1),shadow_inspect);f.push(next,shadow_receive);auto fresh=packet(2,2,0,1,2,0,0,0);f.push(fresh,shadow_receive);f.push(packet(2,2,0,1,1),shadow_inspect);f.run();f.pop(summary_missing);f.pop(summary_stale);f.pop(summary_ok);require(f.pop(summary_ok).w[4]==0,"new session bootstrap");
    f.session=1;f.push(next,shadow_receive);f.run();f.pop(summary_bad_record);f.session=2;
    f.push(fresh,shadow_receive,0,1);f.run(0);require(f.done.w[2]==0,"max_steps ignored");f.run(1);f.pop(summary_ok);require(f.shadows[3].w[0]==2,"lane address mapping");
    f.die=2;f.push(packet(2,5,1,2,3,4,3,2),shadow_receive,2,1);f.run();f.pop(summary_ok);require(f.shadows[5].w[1]==4,"three-die membership");
    f.topology[2]|=std::uint64_t(1)<<63;f.push(packet(2,5,1,2,3,4,3,3),shadow_receive,2,1);f.run();f.pop(summary_bad_address);
    SummaryWord snapshot=f.shadows[0];dieroute_summary_hbm(f.commands,f.topology,f.owners,f.shadows,f.responses,&f.done,3,2,1,3,2,3,8,f.cr,f.cw,f.rr,f.rw,8);require(f.done.w[3]==1&&!std::memcmp(&snapshot,&f.shadows[0],64),"invalid queue mutated state");
    // Exhausted output tickets stop without wrapping to a reusable old ticket.
    dieroute_summary_hbm(f.commands,f.topology,f.owners,f.shadows,f.responses,&f.done,3,2,1,3,2,8,8,0,1,UINT64_MAX,UINT64_MAX,8);require(f.done.w[2]==0&&f.done.w[1]==UINT64_MAX,"output ticket wrapped");
    std::cout<<"summary HBM owner/fetch/validate, receiver versions/sessions, full membership, lane indexing, queue wrap/credit/resume and rejection passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
