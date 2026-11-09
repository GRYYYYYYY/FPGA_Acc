#pragma once
#include <cstdint>
#include <cstring>
#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <limits>
struct RCExcessEntry {uint32_t node;float excess;};
inline uint64_t rc_excess_unsigned(const std::string& s) {
 if(s.empty())throw std::runtime_error("empty excess integer");
 for(char c:s)if(c<'0'||c>'9')throw std::runtime_error("nondecimal excess integer");
 size_t used=0;auto value=std::stoull(s,&used);if(used!=s.size())throw std::runtime_error("excess integer suffix");return value;
}
inline std::vector<RCExcessEntry> rc_read_excess(const std::string& path,const std::string& expected_graph,uint64_t nodes) {
 if(expected_graph.size()!=64)throw std::runtime_error("expected graph SHA missing");
 for(char c:expected_graph)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))throw std::runtime_error("expected graph SHA syntax");
 std::ifstream input(path);if(!input)throw std::runtime_error("excess file open");std::string line,magic,digest,n,c,extra;
 if(!std::getline(input,line))throw std::runtime_error("excess header missing");std::istringstream header(line);
 if(!(header>>magic>>digest>>n>>c)||(header>>extra)||magic!="RCRISK1"||digest!=expected_graph||rc_excess_unsigned(n)!=nodes)throw std::runtime_error("excess header mismatch");
 auto count=rc_excess_unsigned(c);if(count>nodes)throw std::runtime_error("excess entry count");std::vector<RCExcessEntry> result;result.reserve(count);uint64_t previous=0;
 for(uint64_t i=0;i<count;++i) {
  if(!std::getline(input,line))throw std::runtime_error("excess truncated");std::istringstream row(line);std::string id,b;
  if(!(row>>id>>b)||(row>>extra))throw std::runtime_error("excess row syntax");auto node=rc_excess_unsigned(id),bits=rc_excess_unsigned(b);
  if(node>=nodes||node>std::numeric_limits<uint32_t>::max()||(i&&node<=previous)||bits>std::numeric_limits<uint32_t>::max())throw std::runtime_error("excess row identity");
  uint32_t word=uint32_t(bits);float value;static_assert(sizeof(float)==sizeof(word),"binary32 required");static_assert(std::numeric_limits<float>::is_iec559,"IEEE754 required");std::memcpy(&value,&word,sizeof(value));
  if(!std::isfinite(value)||value<=0)throw std::runtime_error("excess value must be finite positive");result.push_back({uint32_t(node),value});previous=node;
 }
 if(std::getline(input,line))throw std::runtime_error("excess trailing records");if(!input.eof())throw std::runtime_error("excess read failed");return result;
}
