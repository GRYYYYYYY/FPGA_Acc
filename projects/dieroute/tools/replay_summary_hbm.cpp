#include "summary_hbm.hpp"
#include "native_worker_shadows.hpp"
#include "native_csr_io.hpp"
#include <iostream>
#include <algorithm>
using namespace dieroute;
using namespace dieroute::native;
struct Endpoint {
    std::vector<SummaryWord> owner,shadow;
    SummaryWord commands[32]={},responses[32]={},done={};
    std::vector<SummaryWord> expected;
    const std::vector<std::uint64_t>& topology;
    std::uint64_t cr=0,cw=0,rr=0,rw=0,session=0,launches=0;unsigned die,lanes;
    Endpoint(const std::vector<std::uint64_t>& t,unsigned d,unsigned l):owner(t.size()),shadow(t.size()*l),topology(t),die(d),lanes(l){}
    void flush(){
        while(cr<cw){
            const auto before=cr;
            dieroute_summary_hbm(commands,topology.data(),owner.data(),shadow.data(),responses,&done,topology.size(),lanes,die,3,session,8,8,cr,cw,rr,rw,(launches++%3==0)?1:3);
            check(done.w[3]==0&&done.w[2]>0,"replay ring stalled/error");cr=done.w[0];rw=done.w[1];
            while(rr<rw){auto output=(rr&7)*2;auto receipt=responses[output+1];
                check(receipt.w[0]==summary_ok&&receipt.w[1]==rr,"replay receipt status/ticket");
                const auto& want=expected[rr%8];for(unsigned j=0;j<8;++j)check(responses[output].w[j]==want.w[j],"hardware C-model differs from NativeWorkerShadows");
                ++rr;
            }
            check(cr>before&&rr==rw,"replay progress");
        }
    }
    void enqueue(SummaryWord p,unsigned op,unsigned slot,unsigned lane,SummaryWord want){
        if(cw-cr==8)flush();
        auto input=(cw&7)*2;commands[input]=p;commands[input+1]={};commands[input+1].w[0]=op|(std::uint64_t(lane)<<32);commands[input+1].w[1]=slot;
        if(expected.empty())expected.resize(8);
        expected[cw%8]=want;++cw;
    }
};
int main(int argc,char** argv){try{
    check(argc==6,"usage: replay_summary_hbm MESSAGES NODES ARCH LANES OUTPUT_CSV");
    Container messages(argv[1],0x44520022,128,fingerprint(argv[3]));Raw nodes(argv[2],16);check(nodes.count<UINT32_MAX,"node index range");unsigned lanes=std::stoul(argv[4]);check(lanes&&lanes<=8,"lanes");
    std::vector<std::uint64_t> topology;std::vector<std::uint32_t> ids;
    for(std::uint32_t n=0;n<nodes.count;++n){auto mask=nodes.at(n,5);if(mask&&(mask&(mask-1))){check(mask<8&&nodes.at(n,0)==n,"topology membership");ids.push_back(n);topology.push_back(n|(std::uint64_t(mask)<<32));}}
    check(!topology.empty(),"no boundary topology");
    NativeOwnerLayout layout=NativeOwnerLayout::from_membership(3,[&](std::uint32_t n){return nodes.at(n,5);});NativeRouteState authority(layout);
    std::vector<NativeWorkerShadows> reference(lanes);std::vector<Endpoint> endpoints;for(unsigned d=0;d<3;++d)endpoints.emplace_back(topology,d,lanes);
    std::set<std::tuple<unsigned,unsigned,std::uint32_t>> subscribed;std::uint64_t session=0,delivered=0,requests=0,repetitions=0;std::ofstream out(argv[5]);check(bool(out),"output open");
    out<<"repeat,lane,worker,node,occupancy,history,version\n";
    auto finish=[&]{if(!session)return;for(auto& e:endpoints)e.flush();for(auto entry:subscribed){auto [lane,worker,node]=entry;auto slot=std::lower_bound(ids.begin(),ids.end(),node)-ids.begin();const auto& s=endpoints[worker].shadow[lane*ids.size()+slot];
            auto value=reference[lane].query(authority,worker,node);check(value.second&&s.w[0]==session&&s.w[1]==value.first.occupancy&&s.w[2]==value.first.history&&s.w[3]==value.first.version,"final receiver mismatch");
            out<<session-1<<','<<lane<<','<<worker<<','<<node<<','<<s.w[1]<<','<<s.w[2]<<','<<s.w[3]<<'\n';}
        ++repetitions;subscribed.clear();};
    for(std::uint64_t i=0;i<messages.count;++i){const auto* frame=messages.data+i*128;auto rep=le64(frame),lane=le64(frame+24);auto p=NativeSummaryPacket::decode(frame+64);check(lane<lanes&&p.session()==rep+1,"capture session/lane");
        if(p.session()!=session){finish();check(p.session()==session+1,"nonconsecutive sessions");session=p.session();for(auto& r:reference)r.reset(layout,session);for(auto& e:endpoints)e.session=session;}
        if(p.kind()==1){++requests;continue;}check(p.kind()==2||p.kind()==3,"capture operation");
        const auto node=p.node();auto found=std::lower_bound(ids.begin(),ids.end(),node);check(found!=ids.end()&&*found==node,"missing boundary slot");unsigned slot=found-ids.begin();
        check(reference[lane].receive(p),"real capture unexpectedly stale/duplicate");auto value=reference[lane].query(authority,p.worker(),node);check(value.second,"reference hidden cold fetch");
        SummaryWord encoded={};for(unsigned j=0;j<8;++j)encoded.w[j]=p.words[j];auto& endpoint=endpoints[p.worker()];endpoint.enqueue(encoded,shadow_receive,slot,lane,encoded);
        auto request=NativeSummaryPacket::make(session,p.serial(),node,p.owner(),p.worker(),1);SummaryWord query={},wanted={};for(unsigned j=0;j<8;++j)query.w[j]=request.words[j];
        auto reply=NativeSummaryPacket::make(session,p.serial(),node,p.owner(),p.worker(),2,value.first);for(unsigned j=0;j<8;++j)wanted.w[j]=reply.words[j];
        endpoint.enqueue(query,shadow_inspect,slot,lane,wanted);subscribed.emplace(lane,p.worker(),node);++delivered;
    }
    finish();out.close();check(bool(out),"output close");std::uint64_t launches=0;for(const auto& e:endpoints)launches+=e.launches;
    std::cout<<"{\"passed\":true,\"repeats\":"<<repetitions<<",\"boundary_slots\":"<<ids.size()<<",\"receiver_deliveries\":"<<delivered<<",\"cache_inspections\":"<<delivered<<",\"source_fetch_requests\":"<<requests<<",\"kernel_launches\":"<<launches<<",\"cache_bytes_per_die\":"<<ids.size()*lanes*64<<",\"scope\":\"C-model receiver/lookup replay of independently audited capture; owner fetch/validation tested separately; no hardware throughput claim\"}\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
