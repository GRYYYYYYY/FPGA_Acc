#include "summary_hbm.hpp"
namespace dieroute {
static bool power2(std::uint32_t n){
#ifdef __SYNTHESIS__
#pragma HLS INLINE off
#pragma HLS LATENCY min=2 max=2
#endif
    return n&&!(n&(n-1))&&n<=(1u<<20);
}
static bool tuple_equal(const SummaryWord& record,const SummaryWord& packet){
    return record.w[1]==packet.w[2]&&record.w[2]==packet.w[3]&&record.w[3]==packet.w[4];
}
static SummaryWord store_word(const SummaryWord& p,std::uint64_t topo){
    SummaryWord r={};r.w[0]=p.w[0];r.w[1]=p.w[2];r.w[2]=p.w[3];r.w[3]=p.w[4];r.w[4]=topo;return r;
}
static bool record_ok(const SummaryWord& r,std::uint64_t topo,std::uint64_t session){
    return r.w[0]<=session&&(r.w[0]!=session||(r.w[4]==topo&&r.w[2]!=UINT64_MAX&&r.w[5]==0&&r.w[6]==0&&r.w[7]==0));
}
static std::uint64_t operate(const SummaryWord& p,const SummaryWord& d,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* shadows,std::uint32_t slots,std::uint32_t lanes,
    std::uint32_t die,std::uint32_t dies,std::uint64_t session,SummaryWord& reply,std::uint64_t& wrote){
    const std::uint32_t op=d.w[0],lane=d.w[0]>>32;
    reply=p;wrote=0;
    if(d.w[1]>=slots||lane>=lanes)return summary_bad_address;
    if(op<owner_install||op>owner_validate||d.w[3]||d.w[4]||d.w[5]||d.w[6]||d.w[7]||(op!=owner_install&&d.w[2]))return summary_bad_packet;
    const std::uint32_t slot=d.w[1],node=p.w[1],owner=(p.w[1]>>32)&255,worker=(p.w[1]>>40)&255,kind=(p.w[1]>>48)&255;
    const std::uint64_t topo=topology[slot];const std::uint32_t mask=topo>>32;
    if(std::uint32_t(topo)!=node||node==UINT32_MAX||!mask||mask>=(1u<<dies)||!(mask&(mask-1)))return summary_bad_address;
    std::uint32_t actual_owner=0;
    for(std::uint32_t i=0;i<8;++i){
#ifdef __SYNTHESIS__
#pragma HLS UNROLL
#endif
        if((mask&(1u<<i))&&!(mask&((1u<<i)-1)))actual_owner=i;
    }
    if(owner!=actual_owner||worker>=dies||worker==owner||!(mask&(1u<<worker)))return summary_bad_role;
    if(p.w[1]>>56||!p.w[5]||p.w[6]||p.w[7]||p.w[3]==UINT64_MAX)return summary_bad_packet;
    if(p.w[0]!=session)return summary_stale;
    const bool request=op==owner_fetch||op==shadow_inspect;
    if(request?(kind!=1||p.w[2]||p.w[3]||p.w[4]):(kind!=2&&kind!=3))return summary_bad_packet;
    const bool local=op==owner_install||op==owner_fetch||op==owner_validate;
    if((local?owner:worker)!=die)return summary_bad_role;
    const std::uint64_t address=std::uint64_t(lane)*slots+slot;
    SummaryWord old=local?owners[slot]:shadows[address];
    if(!record_ok(old,topo,session))return summary_bad_record;
    const bool present=old.w[0]==session;
    if(op==owner_install){
        if(d.w[2]!=(present?old.w[3]:0))return summary_compare_failed;
    }
    if(op==owner_install||op==shadow_receive){
        if(present){
            if(p.w[4]<old.w[3])return summary_stale;
            if(p.w[4]==old.w[3])return tuple_equal(old,p)?summary_duplicate:summary_value_conflict;
        }
        SummaryWord next=store_word(p,topo);
        if(local)owners[slot]=next;else shadows[address]=next;
        wrote=1;return summary_ok;
    }
    if(!present)return summary_missing;
    if(op==owner_validate)return tuple_equal(old,p)?summary_ok:summary_stale;
    reply.w[1]=(p.w[1]&~(std::uint64_t(255)<<48))|(std::uint64_t(2)<<48);
    reply.w[2]=old.w[1];reply.w[3]=old.w[2];reply.w[4]=old.w[3];return summary_ok;
}
extern "C" void dieroute_summary_hbm(
    const SummaryWord* commands,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* shadows,SummaryWord* responses,SummaryWord* completion,
    std::uint32_t slots,std::uint32_t lanes,std::uint32_t die,std::uint32_t dies,
    std::uint64_t session,std::uint32_t command_capacity,std::uint32_t response_capacity,
    std::uint64_t command_read,std::uint64_t command_write,
    std::uint64_t response_read,std::uint64_t response_write,std::uint32_t max_steps){
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=commands offset=slave bundle=ingress depth=32 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=topology offset=slave bundle=directory depth=16 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=owners offset=slave bundle=owner_state depth=16 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=shadows offset=slave bundle=shadow_state depth=64 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#if defined(DIEROUTE_SUMMARY_SHARED_TRAFFIC) && DIEROUTE_SUMMARY_SHARED_TRAFFIC
// The joint seven-CU platform shares the receiver's request/reply master.
// This changes only the synthesized interface, not the command semantics.
#pragma HLS INTERFACE m_axi port=responses offset=slave bundle=ingress depth=32 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=completion offset=slave bundle=ingress depth=1 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#else
#pragma HLS INTERFACE m_axi port=responses offset=slave bundle=egress depth=32 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#pragma HLS INTERFACE m_axi port=completion offset=slave bundle=egress depth=1 max_widen_bitwidth=512 num_read_outstanding=2 num_write_outstanding=2 max_read_burst_length=2 max_write_burst_length=2
#endif
#pragma HLS AGGREGATE variable=commands compact=none
#pragma HLS AGGREGATE variable=owners compact=none
#pragma HLS AGGREGATE variable=shadows compact=none
#pragma HLS AGGREGATE variable=responses compact=none
#pragma HLS AGGREGATE variable=completion compact=none
#pragma HLS INTERFACE s_axilite port=commands bundle=control
#pragma HLS INTERFACE s_axilite port=topology bundle=control
#pragma HLS INTERFACE s_axilite port=owners bundle=control
#pragma HLS INTERFACE s_axilite port=shadows bundle=control
#pragma HLS INTERFACE s_axilite port=responses bundle=control
#pragma HLS INTERFACE s_axilite port=completion bundle=control
#pragma HLS INTERFACE s_axilite port=slots bundle=control
#pragma HLS INTERFACE s_axilite port=lanes bundle=control
#pragma HLS INTERFACE s_axilite port=die bundle=control
#pragma HLS INTERFACE s_axilite port=dies bundle=control
#pragma HLS INTERFACE s_axilite port=session bundle=control
#pragma HLS INTERFACE s_axilite port=command_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=response_capacity bundle=control
#pragma HLS INTERFACE s_axilite port=command_read bundle=control
#pragma HLS INTERFACE s_axilite port=command_write bundle=control
#pragma HLS INTERFACE s_axilite port=response_read bundle=control
#pragma HLS INTERFACE s_axilite port=response_write bundle=control
#pragma HLS INTERFACE s_axilite port=max_steps bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
    SummaryWord done={};done.w[0]=command_read;done.w[1]=response_write;done.w[6]=session;
    // Bound address arithmetic independently of the cosimulation depth hints.
    const bool valid=slots&&slots<=(1u<<24)&&lanes&&lanes<=8&&dies&&dies<=8&&die<dies&&session&&
        power2(command_capacity)&&power2(response_capacity)&&command_read<=command_write&&response_read<=response_write&&
        command_write-command_read<=command_capacity&&response_write-response_read<=response_capacity;
    if(!valid){done.w[3]=1;*completion=done;return;}
    const std::uint64_t available=command_write-command_read,credit=response_capacity-(response_write-response_read);
    std::uint64_t count=available<credit?available:credit;
    if(count>max_steps)count=max_steps;
    if(count>UINT64_MAX-response_write)count=UINT64_MAX-response_write;
    for(std::uint64_t i=0;i<count;++i){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE off
#endif
        const std::uint64_t input=((command_read+i)&(command_capacity-1))*2,output=((response_write+i)&(response_capacity-1))*2;
        const SummaryWord packet=commands[input],descriptor=commands[input+1];SummaryWord reply={},receipt={};std::uint64_t wrote=0;
        const auto status=operate(packet,descriptor,topology,owners,shadows,slots,lanes,die,dies,session,reply,wrote);
        receipt.w[0]=status;receipt.w[1]=command_read+i;receipt.w[2]=descriptor.w[0];receipt.w[3]=descriptor.w[1];receipt.w[4]=wrote;
        responses[output]=reply;responses[output+1]=receipt;done.w[4]+=wrote;done.w[5]+=status!=summary_ok&&status!=summary_duplicate;
    }
    done.w[0]+=count;done.w[1]+=count;done.w[2]=count;*completion=done;
}
}
