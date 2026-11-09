// CRC64-ECMA checker for large immutable research containers. The Python
// semantic auditors retain a pure-Python fallback and bind this executable's
// hash whenever the optional fast checker is selected.
#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
int main(int argc,char** argv){try{
 if(argc!=3)throw std::runtime_error("usage: native_crc64 FILE OFFSET");
 std::size_t used=0;auto offset=std::stoull(argv[2],&used);if(used!=std::string(argv[2]).size())throw std::runtime_error("invalid offset");
 std::ifstream input(argv[1],std::ios::binary);if(!input)throw std::runtime_error("open failed");input.seekg(0,std::ios::end);auto size=input.tellg();if(size<0||offset>std::uint64_t(size))throw std::runtime_error("offset beyond file");input.seekg(offset);
 std::array<std::uint64_t,256> table{};for(unsigned byte=0;byte<256;++byte){auto value=std::uint64_t(byte)<<56;for(unsigned bit=0;bit<8;++bit)value=(value<<1)^((value>>63)?UINT64_C(0x42f0e1eba9ea3693):0);table[byte]=value;}
 std::array<char,1024*1024> buffer{};std::uint64_t crc=0;
 do{input.read(buffer.data(),buffer.size());for(std::streamsize i=0;i<input.gcount();++i)crc=table[(crc>>56)^static_cast<unsigned char>(buffer[i])]^(crc<<8);}while(input);
 if(!input.eof())throw std::runtime_error("read failed");
 std::cout<<std::hex<<std::setfill('0')<<std::setw(16)<<crc<<'\n';
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
