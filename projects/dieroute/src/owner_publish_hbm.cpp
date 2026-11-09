#include "owner_publish_hbm.hpp"
namespace dieroute {
namespace {
bool power2(std::uint32_t n){
#ifdef __SYNTHESIS__
#pragma HLS INLINE off
#pragma HLS LATENCY min=2 max=2
#endif
    return n&&!(n&(n-1))&&n<=(1u<<24);
}
bool zeros(const SummaryWord& r,unsigned begin){for(unsigned i=begin;i<8;++i)if(r.w[i])return false;return true;}
bool topology_ok(std::uint64_t t,std::uint32_t die,std::uint32_t dies){
    const std::uint32_t mask=t>>32;
    return std::uint32_t(t)!=UINT32_MAX&&mask&&(mask&(mask-1))&&mask<(1u<<dies)&&(mask&(1u<<die))&&!(mask&((1u<<die)-1));
}
std::uint64_t allowed_bits(std::uint32_t mask,std::uint32_t owner,std::uint32_t lanes){
#ifdef __SYNTHESIS__
#pragma HLS INLINE off
#pragma HLS LATENCY min=2 max=2
#endif
    std::uint64_t value=0;
    for(unsigned d=0;d<8;++d)if(d!=owner&&(mask&(1u<<d)))value|=((std::uint64_t(1)<<lanes)-1)<<(d*8);
    return value;
}
bool registry_ok(const SummaryWord& r,std::uint64_t session,std::uint64_t allowed){
    return r.w[0]<=session&&(r.w[0]!=session||(!(r.w[1]&~allowed)&&!(r.w[2]&~r.w[1])&&r.w[3]==std::uint64_t(bool(r.w[2]))&&zeros(r,4)));
}
bool owner_ok(const SummaryWord& r,std::uint64_t session,std::uint64_t topo){
    return r.w[0]<=session&&(r.w[0]!=session||(r.w[4]==topo&&r.w[2]!=UINT64_MAX&&zeros(r,5)));
}
std::uint64_t operate(const SummaryWord& p,const SummaryWord& d,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* registry,std::uint32_t* queue,SummaryWord& ctl,
    std::uint32_t slots,std::uint32_t lanes,std::uint32_t die,std::uint32_t dies,
    std::uint64_t session,std::uint32_t capacity,SummaryWord& reply,std::uint64_t& wrote){
#ifdef __SYNTHESIS__
#pragma HLS INLINE off
#pragma HLS PIPELINE off
#endif
    reply=p;wrote=0;
    const std::uint32_t op=d.w[0],lane=d.w[0]>>32;
    if(d.w[1]>=slots||lane>=lanes)return summary_bad_address;
    if((op!=owner_install&&op!=owner_fetch&&op!=owner_validate&&op!=owner_subscribe)||!zeros(d,3)||(op!=owner_install&&d.w[2]))return summary_bad_packet;
    const std::uint32_t slot=d.w[1],owner=(p.w[1]>>32)&255,worker=(p.w[1]>>40)&255,kind=(p.w[1]>>48)&255;
    const auto topo=topology[slot];const std::uint32_t mask=topo>>32;
    if(std::uint32_t(p.w[1])!=std::uint32_t(topo)||!topology_ok(topo,die,dies))return summary_bad_address;
    if(owner!=die||worker>=dies||worker==owner||!(mask&(1u<<worker)))return summary_bad_role;
    if(p.w[1]>>56||!p.w[5]||!zeros(p,6)||p.w[3]==UINT64_MAX)return summary_bad_packet;
    if(p.w[0]!=session)return summary_stale;
    const bool fetch=op==owner_fetch||op==owner_subscribe;
    if(fetch?(kind!=1||p.w[2]||p.w[3]||p.w[4]):(kind!=2&&kind!=3))return summary_bad_packet;
    auto old=owners[slot],sub=registry[slot];
    if(!owner_ok(old,session,topo)||!registry_ok(sub,session,allowed_bits(mask,owner,lanes)))return summary_bad_record;
    const bool present=old.w[0]==session;
    if(sub.w[0]!=session){sub={};sub.w[0]=session;}
    if(!present&&sub.w[1])return summary_bad_record;
    if(op==owner_install){
        if(d.w[2]!=(present?old.w[3]:0))return summary_compare_failed;
        if(present){
            if(p.w[4]<old.w[3])return summary_stale;
            if(p.w[4]==old.w[3])return p.w[2]==old.w[1]&&p.w[3]==old.w[2]?summary_duplicate:summary_value_conflict;
        }
        const auto pending=sub.w[2]|sub.w[1];const bool enqueue=pending&&!sub.w[3];
        if(enqueue&&(ctl.w[2]==UINT64_MAX||ctl.w[2]-ctl.w[1]>=capacity))return publisher_queue_exhausted;
        SummaryWord next={};next.w[0]=session;next.w[1]=p.w[2];next.w[2]=p.w[3];next.w[3]=p.w[4];next.w[4]=topo;
        sub.w[2]=pending;sub.w[3]=bool(pending);
        if(enqueue){queue[ctl.w[2]&(capacity-1)]=slot;++ctl.w[2];}
        owners[slot]=next;registry[slot]=sub;wrote=1;return summary_ok;
    }
    if(!present)return summary_missing;
    if(op==owner_validate)return p.w[2]==old.w[1]&&p.w[3]==old.w[2]&&p.w[4]==old.w[3]?summary_ok:summary_stale;
    if(op==owner_subscribe){const auto bit=std::uint64_t(1)<<(worker*8+lane);wrote=!(sub.w[1]&bit);sub.w[1]|=bit;registry[slot]=sub;}
    reply.w[1]=(p.w[1]&~(std::uint64_t(255)<<48))|(std::uint64_t(2)<<48);
    reply.w[2]=old.w[1];reply.w[3]=old.w[2];reply.w[4]=old.w[3];return summary_ok;
}
unsigned first(std::uint64_t bits){
#ifdef __SYNTHESIS__
#pragma HLS INLINE off
#pragma HLS LATENCY min=2 max=2
#endif
    unsigned value=0;
    for(unsigned b=0;b<64;++b)if((bits>>b)&1){value=b;break;}
    return value;
}
}
extern "C" void dieroute_owner_publish_hbm(
    const SummaryWord* commands,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* registry,std::uint32_t* dirty_queue,
    SummaryWord* responses,SummaryWord* updates,SummaryWord* queue_control,SummaryWord* completion,
    std::uint32_t slots,std::uint32_t lanes,std::uint32_t die,std::uint32_t dies,
    std::uint64_t session,std::uint32_t command_capacity,std::uint32_t response_capacity,
    std::uint32_t update_capacity,std::uint32_t dirty_capacity,
    std::uint64_t command_read,std::uint64_t command_write,
    std::uint64_t response_read,std::uint64_t response_write,
    std::uint64_t update_read,std::uint64_t update_write,
    std::uint32_t max_commands,std::uint32_t max_updates,std::uint32_t max_visits,
    std::uint64_t subscriber_filter){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=commands offset=slave bundle=traffic depth=32 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=topology offset=slave bundle=index depth=16 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=owners offset=slave bundle=owner_state depth=16 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=registry offset=slave bundle=subscriptions depth=16 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=dirty_queue offset=slave bundle=index depth=16 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=responses offset=slave bundle=traffic depth=32 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=updates offset=slave bundle=publications depth=32 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=queue_control offset=slave bundle=index depth=1 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=completion offset=slave bundle=traffic depth=1 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS AGGREGATE variable=commands compact=none
#pragma HLS AGGREGATE variable=owners compact=none
#pragma HLS AGGREGATE variable=registry compact=none
#pragma HLS AGGREGATE variable=responses compact=none
#pragma HLS AGGREGATE variable=updates compact=none
#pragma HLS AGGREGATE variable=queue_control compact=none
#pragma HLS AGGREGATE variable=completion compact=none
#pragma HLS INTERFACE s_axilite port=commands bundle=control
#pragma HLS INTERFACE s_axilite port=topology bundle=control
#pragma HLS INTERFACE s_axilite port=owners bundle=control
#pragma HLS INTERFACE s_axilite port=registry bundle=control
#pragma HLS INTERFACE s_axilite port=dirty_queue bundle=control
#pragma HLS INTERFACE s_axilite port=responses bundle=control
#pragma HLS INTERFACE s_axilite port=updates bundle=control
#pragma HLS INTERFACE s_axilite port=queue_control bundle=control
#pragma HLS INTERFACE s_axilite port=completion bundle=control
#pragma HLS INTERFACE s_axilite port=slots bundle=control
#pragma HLS INTERFACE s_axilite port=lanes bundle=control
#pragma HLS INTERFACE s_axilite port=die bundle=control
#pragma HLS INTERFACE s_axilite port=dies bundle=control
#pragma HLS INTERFACE s_axilite port=session bundle=control
#pragma HLS INTERFACE s_axilite port=command_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=response_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=update_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=dirty_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=command_read bundle=control
#pragma HLS INTERFACE s_axilite port=command_write bundle=control
#pragma HLS INTERFACE s_axilite port=response_read bundle=control
#pragma HLS INTERFACE s_axilite port=response_write bundle=control
#pragma HLS INTERFACE s_axilite port=update_read bundle=control
#pragma HLS INTERFACE s_axilite port=update_write bundle=control
#pragma HLS INTERFACE s_axilite port=max_commands bundle=control
#pragma HLS INTERFACE s_axilite port=max_updates bundle=control
#pragma HLS INTERFACE s_axilite port=max_visits bundle=control
#pragma HLS INTERFACE s_axilite port=subscriber_filter bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
    SummaryWord done={};done.w[0]=command_read;done.w[1]=response_write;done.w[2]=update_write;done.w[7]=session;
    const bool valid=slots&&slots<=(1u<<24)&&lanes&&lanes<=8&&dies&&dies<=8&&die<dies&&session&&power2(command_capacity)&&power2(response_capacity)&&power2(update_capacity)&&power2(dirty_capacity)&&dirty_capacity>=slots&&command_read<=command_write&&response_read<=response_write&&update_read<=update_write&&command_write-command_read<=command_capacity&&response_write-response_read<=response_capacity&&update_write-update_read<=update_capacity;
    auto ctl=*queue_control;
    if(!valid||ctl.w[0]>session||!zeros(ctl,3)||(ctl.w[0]==session&&(ctl.w[1]>ctl.w[2]||ctl.w[2]-ctl.w[1]>slots))){done.w[6]=1;*completion=done;return;}
    if(ctl.w[0]!=session){ctl={};ctl.w[0]=session;}
    std::uint64_t count=command_write-command_read,credit=response_capacity-(response_write-response_read);
    if(count>credit)count=credit;
    if(count>max_commands)count=max_commands;
    if(count>UINT64_MAX-response_write)count=UINT64_MAX-response_write;
    for(std::uint64_t i=0;i<count;++i){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE off
#endif
        auto packet=commands[((command_read+i)&(command_capacity-1))*2],descriptor=commands[((command_read+i)&(command_capacity-1))*2+1];
        SummaryWord reply={},receipt={};std::uint64_t wrote=0;
        auto status=operate(packet,descriptor,topology,owners,registry,dirty_queue,ctl,slots,lanes,die,dies,session,dirty_capacity,reply,wrote);
        receipt.w[0]=status;receipt.w[1]=command_read+i;receipt.w[2]=descriptor.w[0];receipt.w[3]=descriptor.w[1];receipt.w[4]=wrote;
        auto index=((response_write+i)&(response_capacity-1))*2;responses[index]=reply;responses[index+1]=receipt;
    }
    done.w[0]+=count;done.w[1]+=count;done.w[3]=count;
    const auto initial=ctl.w[2]-ctl.w[1];std::uint64_t retired=0;
    while(retired<initial&&done.w[5]<max_visits&&done.w[4]<max_updates){
        const auto slot=dirty_queue[ctl.w[1]&(dirty_capacity-1)];
        if(slot>=slots){done.w[6]=2;break;}
        const auto topo=topology[slot];auto sub=registry[slot],owner=owners[slot];
        if(!topology_ok(topo,die,dies)||sub.w[0]!=session||!registry_ok(sub,session,allowed_bits(topo>>32,die,lanes))||!sub.w[2]||owner.w[0]!=session||!owner_ok(owner,session,topo)){done.w[6]=2;break;}
        const auto eligible=sub.w[2]&subscriber_filter;
        if(!eligible){
            if(ctl.w[2]==UINT64_MAX){done.w[6]=3;break;}
            dirty_queue[ctl.w[2]&(dirty_capacity-1)]=slot;++ctl.w[1];++ctl.w[2];++retired;++done.w[5];continue;
        }
        if(done.w[2]-update_read>=update_capacity||done.w[2]==UINT64_MAX)break;
        const auto bit=first(eligible);const auto worker=bit/8,lane=bit%8;
        SummaryWord packet={},metadata={};packet.w[0]=session;packet.w[1]=std::uint32_t(topo)|(std::uint64_t(die)<<32)|(std::uint64_t(worker)<<40)|(std::uint64_t(3)<<48);packet.w[2]=owner.w[1];packet.w[3]=owner.w[2];packet.w[4]=owner.w[3];packet.w[5]=done.w[2]+1;
        metadata.w[0]=lane;metadata.w[1]=slot;metadata.w[2]=owner.w[3];const auto index=(done.w[2]&(update_capacity-1))*2;updates[index]=packet;updates[index+1]=metadata;
        sub.w[2]&=~(std::uint64_t(1)<<bit);sub.w[3]=bool(sub.w[2]);registry[slot]=sub;
        if(!sub.w[2]){++ctl.w[1];++retired;}
        ++done.w[2];++done.w[4];++done.w[5];
    }
    *queue_control=ctl;*completion=done;
}
}
