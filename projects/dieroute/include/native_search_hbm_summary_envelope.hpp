#pragma once
#include "native_search_hbm_summary_binding.hpp"
namespace dieroute {
// Success receipts and publication metadata are part of source binding; packet
// fields alone cannot establish that the expected operation actually succeeded.
inline NativeSummaryBindingStatus native_search_bind_owner_reply(
 const std::uint64_t* packet,const std::uint64_t* receipt,std::uint32_t node,
 std::uint32_t owner,std::uint32_t worker,std::uint32_t membership,std::uint64_t serial,
 std::uint64_t session,std::uint64_t epoch,std::uint32_t operation,
 std::uint64_t ticket,std::uint32_t lane,std::uint32_t slot,NativeSearchResourceObservation& output){
 if((operation!=2&&operation!=6)||ticket==UINT64_MAX||lane>=8||slot>=(1u<<24)||
    receipt[0]!=0||receipt[1]!=ticket||receipt[2]!=(std::uint64_t(operation)|(std::uint64_t(lane)<<32))||
    receipt[3]!=slot||receipt[4]>1||(operation==2&&receipt[4])||receipt[5]||receipt[6]||receipt[7]||
    ((packet[1]>>48)&255)!=2)return NativeSummaryBindingStatus::invalid;
 return native_search_bind_summary(packet,node,owner,worker,membership,serial,session,epoch,output);
}
inline NativeSummaryBindingStatus native_search_bind_owner_update(
 const std::uint64_t* packet,const std::uint64_t* metadata,std::uint32_t node,
 std::uint32_t owner,std::uint32_t worker,std::uint32_t membership,std::uint64_t ticket,
 std::uint64_t session,std::uint64_t epoch,std::uint32_t lane,std::uint32_t slot,
 NativeSearchResourceObservation& output){
 if(ticket==UINT64_MAX||lane>=8||slot>=(1u<<24)||metadata[0]!=lane||metadata[1]!=slot||
    metadata[2]!=packet[4]||metadata[3]||metadata[4]||metadata[5]||metadata[6]||metadata[7]||
    ((packet[1]>>48)&255)!=3)return NativeSummaryBindingStatus::invalid;
 return native_search_bind_summary(packet,node,owner,worker,membership,ticket+1,session,epoch,output);
}
}
