#include "sparse_search.hpp"
#include <iostream>
using namespace dieroute;
static void check(bool v,const char* why){if(!v)throw std::runtime_error(why);}
template<class F>void rejects(F f){bool yes=false;try{f();}catch(const std::exception&){yes=true;}check(yes,"expected protocol rejection");}
int main(){try{
    auto part=[](uint32_t n){return n%2;};SparseLabelWorker receiver;receiver.reset(1,1,20);
    auto probe=LabelPacket::message(1,1,3,LabelOp::probe,0,1);auto empty=receiver.receive(probe,part,false);LabelPacket::match(probe,empty);
    check(empty.flags()==0&&empty.version()==0&&empty.cost()==UINT64_MAX,"absent label snapshot");
    auto bytes=empty.encode();auto decoded=LabelPacket::decode(bytes.data());check(decoded.words==empty.words,"packet roundtrip");
    check(bytes[0]==1&&bytes[8]==1&&bytes[16]==3&&bytes[20]==2&&bytes[21]==1&&bytes[22]==0&&bytes[24]==255,"little-endian byte positions");
    auto relax=LabelPacket::message(1,1,3,LabelOp::relax,0,1);relax.value(7,9,2,2,203,0,empty.version());
    auto blocked=receiver.receive(relax,part,false);LabelPacket::match(relax,blocked);check(blocked.status()==LabelStatus::budget&&receiver.size()==0,"denied credit mutated receiver");
    auto ack=receiver.receive(relax,part,true);LabelPacket::match(relax,ack);check(ack.status()==LabelStatus::accepted&&ack.flags()==LabelPacket::created&&receiver.size()==1,"first remote label admission");
    auto duplicate=receiver.receive(relax,part,true);check(duplicate.status()==LabelStatus::stale&&receiver.size()==1&&receiver.metrics().pushes==1,"duplicate applied twice");
    auto second=probe;second.words[1]=2;auto snapshot=receiver.receive(second,part,false);auto old=snapshot;
    auto update=relax;update.words[1]=2;update.value(5,7,3,4,403,0,snapshot.version());
    ack=receiver.receive(update,part,false);check(ack.status()==LabelStatus::accepted&&ack.flags()==0,"existing label unnecessarily consumes credit");
    auto delayed=relax;delayed.words[1]=3;delayed.value(4,6,3,4,403,0,old.version());
    check(receiver.receive(delayed,part,true).status()==LabelStatus::stale,"delayed optimistic request accepted");
    snapshot=receiver.receive(probe,part,false);auto dominated=relax;dominated.value(8,10,3,4,403,0,snapshot.version());
    check(receiver.receive(dominated,part,true).status()==LabelStatus::dominated,"dominated receiver update accepted");
    receiver.close(3);snapshot=receiver.receive(probe,part,false);auto closed=relax;closed.value(1,1,1,2,203,0,snapshot.version());
    check(receiver.receive(closed,part,true).status()==LabelStatus::protected_label,"closed label reopened");
    receiver.seed(5,0,0,0,true);auto root=LabelPacket::message(1,4,5,LabelOp::probe,0,1);check(receiver.receive(root,part,false).flags()&LabelPacket::root,"root flag lost");
    auto corrupt=probe;corrupt.words[2]^=uint64_t(1)<<48;rejects([&]{receiver.receive(corrupt,part,false);});
    corrupt=probe;corrupt.words[2]=(corrupt.words[2]&~uint64_t(UINT32_MAX))|4;rejects([&]{receiver.receive(corrupt,part,false);});
    corrupt=probe;corrupt.words[3]=1;rejects([&]{receiver.receive(corrupt,part,false);});
    auto bad_reply=empty;bad_reply.words[1]++;rejects([&]{LabelPacket::match(probe,bad_reply);});
    bad_reply=empty;bad_reply.words[6]|=uint64_t(128)<<32;rejects([&]{LabelPacket::match(probe,bad_reply);});
    receiver.reset(1,2,20);auto stale_epoch=receiver.receive(relax,part,true);LabelPacket::match(relax,stale_epoch);
    check(stale_epoch.status()==LabelStatus::epoch&&receiver.size()==0&&receiver.metrics().epoch_rejects==1,"old epoch/ABA mutated new workspace");
    rejects([&]{receiver.reset(1,2,20);});
    // A cross-worker label may be probed yet rejected without ever being pushed.
    SparseSearch search;auto result=search.run_guided_partitioned(6,{{0,0,0},{1,0,0}},5,20,2,part,[](uint32_t n,auto offer){
        if(n==0){offer(1,1,[]()->std::optional<uint64_t>{throw std::runtime_error("protected root evaluated cost");});offer(3,3,[](){return std::optional<uint64_t>(2);});}
        if(n==1)offer(3,103,[](){return std::optional<uint64_t>(1);});
        if(n==3)offer(5,305,[](){return std::optional<uint64_t>(1);});
    },[](uint32_t){return uint64_t(0);});
    check(result.status==SparseSearchStatus::found&&search.worker_metrics(1).probes==2&&search.worker_metrics(1).probe_protected==1&&search.worker_metrics(1).transfers==1,"rejected probe missing from traffic");
    const auto& messages=search.packets();check(messages.size()%2==0,"incomplete message pairs");
    for(size_t i=0;i<messages.size();i+=2)LabelPacket::match(messages[i],messages[i+1]);
    check(search.worker_metrics(1).traces>0,"traceback bypasses endpoint protocol");
    std::cout<<"fixed 64-byte wire format, credits, delayed/duplicate/stale/protected updates, epoch ABA and complete rejected-probe/trace traffic passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
