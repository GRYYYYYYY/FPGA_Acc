#pragma once
#include "../wire_control_commit/full_color_words.hpp"
#include <vector>
namespace tileplace_wire_control_commit {
class HostColorScratch {
 std::vector<std::uint64_t> words_[18];std::vector<std::uint32_t> ids_[9];std::vector<std::uint8_t> kinds_;
 ColorScratch view_{};
 static unsigned product(std::uint64_t a,std::uint64_t b){if(a&&b>UINT32_MAX/a)throw std::length_error("color scratch capacity exceeds ABI");return unsigned(a*b);}
public:
 explicit HostColorScratch(const ColorInput& in){
 unsigned r=unsigned(std::min<std::uint64_t>(in.limit,in.site_count)),c=unsigned(std::min<std::uint64_t>(in.chain_limit,in.site_count)),g=in.unit_count;
 std::uint64_t largest=0;for(unsigned i=0;i<g;++i)largest=std::max(largest,in.units[4ULL*i+1]);
 unsigned m=std::max(3U,product(largest,2)),d=product(product(g,r),std::uint64_t(c)+1),o=product(d,3),t=product(d,m),w=product(t,2),n=product(d,in.net_count),k=product(d,10);
 words_[0].resize(std::max<std::uint64_t>(1,2ULL*in.limit));view_.roots=words_[0].data();
 words_[1].resize(std::max<std::uint64_t>(1,2ULL*in.chain_limit));view_.chain_roots=words_[1].data();
 words_[2].resize(std::max<std::uint64_t>(1,3ULL*m));view_.first=words_[2].data();
 words_[3].resize(std::max<std::uint64_t>(1,3ULL*m));view_.second=words_[3].data();
 words_[4].resize(std::max<std::uint64_t>(1,3ULL*m));view_.merged=words_[4].data();
 words_[5].resize(std::max<std::uint64_t>(1,6ULL*d));view_.descriptors=words_[5].data();
 words_[6].resize(std::max<std::uint64_t>(1,3ULL*t));view_.source_trials=words_[6].data();
 words_[7].resize(std::max<std::uint64_t>(1,2ULL*g));view_.groups=words_[7].data();
 words_[8].resize(std::max<std::uint64_t>(1,6ULL*d));view_.scored=words_[8].data();
 words_[9].resize(std::max<std::uint64_t>(1,6ULL*d));view_.conflicts=words_[9].data();
 words_[10].resize(std::max<std::uint64_t>(1,2ULL*w));view_.writes=words_[10].data();
 words_[11].resize(std::max<std::uint64_t>(1,7ULL*d));view_.candidates=words_[11].data();
 words_[12].resize(std::max<std::uint64_t>(1,13ULL*d));view_.records=words_[12].data();
 words_[13].resize(std::max<std::uint64_t>(1,2ULL*o));view_.identity_units=words_[13].data();
 words_[14].resize(std::max<std::uint64_t>(1,3ULL*t));view_.identity_trials=words_[14].data();
 words_[15].resize(std::max<std::uint64_t>(1,6ULL*d));view_.forbidden=words_[15].data();
 words_[16].resize(std::max<std::uint64_t>(1,7ULL*g));view_.best7=words_[16].data();
 words_[17].resize(std::max<std::uint64_t>(1,13ULL*g));view_.compact13=words_[17].data();
 ids_[0].resize(std::max<std::uint64_t>(1,g));view_.eligible=ids_[0].data();
 ids_[1].resize(std::max<std::uint64_t>(1,o));view_.owners=ids_[1].data();
 ids_[2].resize(std::max<std::uint64_t>(1,n));view_.touched=ids_[2].data();
 ids_[3].resize(std::max<std::uint64_t>(1,4ULL*d));view_.diagnostics=ids_[3].data();
 ids_[4].resize(std::max<std::uint64_t>(1,g));view_.order=ids_[4].data();
 ids_[5].resize(std::max<std::uint64_t>(1,g));view_.selected=ids_[5].data();
 ids_[6].resize(std::max<std::uint64_t>(1,g));view_.group_indices=ids_[6].data();
 ids_[7].resize(std::max<std::uint64_t>(1,g));view_.gathered=ids_[7].data();
 ids_[8].resize(std::max<std::uint64_t>(1,g));view_.unique_indices=ids_[8].data();
 kinds_.resize(std::max(1U,k));view_.kinds=kinds_.data();view_.root_capacity=in.limit;view_.chain_capacity=in.chain_limit;view_.move_capacity=m;view_.record_capacity=d;view_.owner_capacity=o;view_.trial_capacity=t;view_.group_capacity=g;view_.write_capacity=w;view_.touched_capacity=n;view_.kind_capacity=k;view_.identity_unit_capacity=o;
 }
 const ColorScratch& view()const{return view_;}
 HostColorScratch(const HostColorScratch&)=delete;HostColorScratch& operator=(const HostColorScratch&)=delete;
};
}
