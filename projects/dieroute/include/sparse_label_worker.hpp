#pragma once
#include "sparse_table.hpp"
#include "label_packet.hpp"
#include <algorithm>
#include <tuple>
namespace dieroute {
struct SparseLabel {
    std::uint64_t cost=UINT64_MAX;
    std::uint32_t hops=UINT32_MAX,parent=UINT32_MAX,edge=UINT32_MAX;
    bool closed=false,root=false;
    std::uint64_t version=0;
};
using SparseQueueEntry=std::tuple<std::uint64_t,std::uint64_t,std::uint32_t,std::uint32_t,std::uint32_t>;
struct SparseWorkerMetrics {
    std::uint64_t expanded=0,edge_visits=0,pushes=0,transfers=0;
    std::size_t labels=0;
    std::uint64_t probes=0,probe_protected=0,relaxes=0,accepted=0,rejected=0,traces=0,epoch_rejects=0;
};
// Receiver owns both its sparse labels and queue. Remote callers get value
// responses, never a reference to its table. The serialized coordinator grants
// new-label credit; simultaneous admission would need a global credit arbiter.
class SparseLabelWorker {
    SparseNodeTable<SparseLabel> labels_;
    std::vector<SparseQueueEntry> queue_;
    SparseWorkerMetrics metrics_;
    std::uint32_t die_=0;
    std::uint64_t epoch_=0,nodes_=0;
    static void require(bool ok,const char* what){if(!ok)throw std::logic_error(what);}
    static void room(const SparseLabel& l){if(l.version==UINT64_MAX)throw std::overflow_error("search label version exhausted");}
    void push(SparseQueueEntry e,std::uint32_t sender){queue_.push_back(e);std::push_heap(queue_.begin(),queue_.end(),std::greater<SparseQueueEntry>());++metrics_.pushes;metrics_.transfers+=sender!=LabelPacket::controller&&sender!=die_;}
public:
    void reset(std::uint32_t die,std::uint64_t epoch,std::uint64_t nodes){
        require(die<8&&epoch>epoch_&&nodes<=UINT32_MAX,"invalid label receiver reset");die_=die;epoch_=epoch;nodes_=nodes;labels_.reset();queue_.clear();metrics_={};
    }
    std::size_t size()const{return labels_.size();}
    std::size_t retained_bytes()const{return labels_.retained_bytes()+queue_.capacity()*sizeof(SparseQueueEntry);}
    SparseWorkerMetrics metrics()const{auto m=metrics_;m.labels=size();return m;}
    bool empty()const{return queue_.empty();}
    const SparseQueueEntry& head()const{return queue_.front();}
    SparseQueueEntry pop(){std::pop_heap(queue_.begin(),queue_.end(),std::greater<SparseQueueEntry>());auto e=queue_.back();queue_.pop_back();return e;}
    SparseLabel local(std::uint32_t n)const{return labels_.get(n);}
    void visit(){++metrics_.edge_visits;}
    void close(std::uint32_t n){auto& l=labels_.touch(n);room(l);l.closed=true;++l.version;++metrics_.expanded;}
    bool seed(std::uint32_t n,std::uint64_t cost,std::uint64_t priority,std::uint32_t hops,bool credit){
        auto old=labels_.get(n);if(std::tie(cost,hops)>=std::tie(old.cost,old.hops))return true;
        if(!labels_.contains(n)&&!credit)return false;
        room(old);
        auto& l=labels_.touch(n);l.cost=cost;l.hops=hops;l.root=true;++l.version;push({priority,cost,hops,n,UINT32_MAX},LabelPacket::controller);return true;
    }
    template<class Partition> LabelPacket receive(const LabelPacket& req,Partition partition,bool credit){
        require(req.to()==die_&&req.from()<=LabelPacket::controller&&req.node()<nodes_&&partition(req.node())==die_&&req.id()!=0&&req.status()==LabelStatus::ok,"misrouted/malformed label request");
        const auto op=req.op();require(op==LabelOp::probe||op==LabelOp::relax||op==LabelOp::trace,"invalid label request opcode");
        const auto reply_op=op==LabelOp::probe?LabelOp::probe_reply:op==LabelOp::trace?LabelOp::trace_reply:LabelOp::relax_reply;
        auto response=[&](LabelStatus status){return LabelPacket::message(req.epoch(),req.id(),req.node(),reply_op,die_,req.from(),status);};
        const bool remote=req.from()!=die_;
        if(op!=LabelOp::relax){for(unsigned i=3;i<8;++i)require(req.words[i]==0,"nonzero probe payload");}
        else require(req.from()<8&&req.cost()<UINT64_MAX&&req.priority()<UINT64_MAX&&req.priority()>=req.cost()&&req.parent()<nodes_&&req.hops()>0&&req.flags()==0,"invalid label relaxation payload");
        if(remote){if(op==LabelOp::trace)++metrics_.traces;else if(op==LabelOp::probe)++metrics_.probes;else ++metrics_.relaxes;}
        if(req.epoch()!=epoch_){if(remote){++metrics_.epoch_rejects;metrics_.rejected+=op==LabelOp::relax;}return response(LabelStatus::epoch);}
        const auto old=labels_.get(req.node());
        if(op!=LabelOp::relax){
            if(remote&&op==LabelOp::probe)metrics_.probe_protected+=old.closed||old.root;
            auto reply=response(LabelStatus::ok);reply.value(old.cost,0,old.hops,old.parent,old.edge,(labels_.contains(req.node())?LabelPacket::present:0)|(old.closed?LabelPacket::closed:0)|(old.root?LabelPacket::root:0),old.version);return reply;
        }
        auto reject=[&](LabelStatus status){if(remote)++metrics_.rejected;auto r=response(status);r.words[7]=old.version;return r;};
        if(req.version()!=old.version)return reject(LabelStatus::stale);
        if(old.closed||old.root)return reject(LabelStatus::protected_label);
        auto cost=req.cost();auto hops=req.hops();auto parent=req.parent();auto edge=req.edge();
        if(std::tie(cost,hops,parent,edge)>=std::tie(old.cost,old.hops,old.parent,old.edge))return reject(LabelStatus::dominated);
        const bool created=!labels_.contains(req.node());if(created&&!credit)return reject(LabelStatus::budget);
        if(old.version==UINT64_MAX)return reject(LabelStatus::overflow);
        auto& l=labels_.touch(req.node());l.cost=cost;l.hops=hops;l.parent=parent;l.edge=edge;++l.version;
        push({req.priority(),cost,hops,req.node(),parent},req.from());if(remote)++metrics_.accepted;
        auto reply=response(LabelStatus::accepted);reply.words[6]=std::uint64_t(created?LabelPacket::created:0)<<32;reply.words[7]=l.version;return reply;
    }
};
}
