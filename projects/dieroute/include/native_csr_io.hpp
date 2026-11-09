#pragma once
// Diagnostic native CSR containers use the shared 64-byte FPGAACCP header.
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

namespace dieroute::native {
namespace fs=std::filesystem;
constexpr uint32_t none=UINT32_MAX, offsets_type=0x44520001, arcs_type=0x44520002, protection_type=0x44520003;
inline void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
inline uint32_t le32(const unsigned char* p){return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);}
inline uint64_t le64(const unsigned char* p){return uint64_t(le32(p))|(uint64_t(le32(p+4))<<32);}
inline void put32(unsigned char* p,uint32_t n){for(int i=0;i<4;i++)p[i]=static_cast<unsigned char>(n>>(8*i));}
inline void put64(unsigned char* p,uint64_t n){for(int i=0;i<8;i++)p[i]=static_cast<unsigned char>(n>>(8*i));}
using Fingerprint=std::array<unsigned char,16>;
inline Fingerprint fingerprint(const std::string& text){
    check(text.size()==32,"fingerprint must contain 32 hex characters");Fingerprint r{};
    auto nibble=[](char c)->unsigned{if(c>='0' && c<='9')return c-'0';if(c>='a' && c<='f')return c-'a'+10;throw std::runtime_error("invalid fingerprint hex");};
    for(size_t i=0;i<16;i++)r[i]=static_cast<unsigned char>((nibble(text[i*2])<<4)|nibble(text[i*2+1]));
    return r;
}
inline uint64_t crc64(uint64_t crc,const unsigned char* data,size_t size){
    static const auto table=[](){std::array<uint64_t,256> t{};
        for(size_t i=0;i<256;i++){uint64_t c=uint64_t(i)<<56;for(int j=0;j<8;j++)c=(c<<1)^((c>>63)?0x42f0e1eba9ea3693ULL:0);t[i]=c;}return t;}();
    for(size_t i=0;i<size;i++)crc=table[((crc>>56)^data[i])&255]^(crc<<8);
    return crc;
}
class Mapping {
    int fd_=-1;
public:
    const unsigned char* data=nullptr;size_t bytes=0;
    explicit Mapping(const fs::path& p){
        fd_=open(p.c_str(),O_RDONLY);if(fd_<0)throw std::runtime_error("open "+p.string());struct stat st{};
        check(fstat(fd_,&st)==0 && st.st_size>=0,"file stat failed");bytes=static_cast<size_t>(st.st_size);
        if(bytes){data=static_cast<const unsigned char*>(mmap(nullptr,bytes,PROT_READ,MAP_PRIVATE,fd_,0));check(data!=MAP_FAILED,"mmap failed");}
    }
    Mapping(const Mapping&)=delete;Mapping& operator=(const Mapping&)=delete;
    ~Mapping(){if(data && data!=MAP_FAILED)munmap(const_cast<unsigned char*>(data),bytes);if(fd_>=0)close(fd_);}
};
class Raw {
    Mapping file_;size_t width_;
public:
    size_t count;
    Raw(const fs::path& path,size_t words):file_(path),width_(words),count(file_.bytes/(words*4)){check(file_.bytes%(words*4)==0,"truncated raw table");}
    uint32_t at(size_t row,size_t column)const{check(row<count && column<width_,"raw table bounds");return le32(file_.data+4*(row*width_+column));}
};
class Container {
    Mapping file_;
public:
    const unsigned char* data;uint64_t count,payload;uint32_t type;
    Container(const fs::path& p,uint32_t expected_type,size_t record_bytes,const Fingerprint& arch):file_(p){
        check(file_.bytes>=64,"truncated container header");auto h=file_.data;
        check(std::memcmp(h,"FPGAACCP",8)==0,"container magic");
        check(h[8]==0 && h[9]==0 && h[10]==1 && h[11]==0,"container schema");
        type=le32(h+12);count=le64(h+16);payload=le64(h+24);
        check(type==expected_type && le64(h+56)==1,"container type/flags");
        check(std::memcmp(h+32,arch.data(),16)==0,"architecture fingerprint");
        check(count<=UINT64_MAX/record_bytes && count*record_bytes==payload && payload==file_.bytes-64,"container payload length");
        data=h+64;check(crc64(0,data,payload)==le64(h+48),"container CRC64");
    }
    uint64_t offset(size_t i)const{check(i<count && type==offsets_type,"offset bounds/type");return le64(data+i*8);}
    uint32_t dst(size_t i)const{check(i<count && type==arcs_type,"arc bounds/type");return le32(data+i*8);}
    uint32_t edge(size_t i)const{check(i<count && type==arcs_type,"arc bounds/type");return le32(data+i*8+4);}
};
class Writer {
    std::ofstream out_;uint64_t count_,payload_=0,crc_=0;uint32_t type_;Fingerprint arch_;
public:
    Writer(const fs::path& path,uint32_t type,uint64_t count,Fingerprint arch):out_(path,std::ios::binary),count_(count),type_(type),arch_(arch){
        check(bool(out_),"container output open");std::array<char,64> zero{};out_.write(zero.data(),zero.size());
    }
    void append(const unsigned char* data,size_t bytes){
        check(bytes<=UINT64_MAX-payload_,"payload overflow");crc_=crc64(crc_,data,bytes);out_.write(reinterpret_cast<const char*>(data),bytes);
        check(bool(out_),"container output write");payload_+=bytes;
    }
    void finish_dynamic(size_t record_bytes){check(record_bytes&&payload_%record_bytes==0,"dynamic record width");count_=payload_/record_bytes;finish(record_bytes);}
    void finish(size_t record_bytes){
        check(count_<=UINT64_MAX/record_bytes && payload_==count_*record_bytes,"output record count");std::array<unsigned char,64> h{};
        std::memcpy(h.data(),"FPGAACCP",8);h[10]=1;put32(h.data()+12,type_);put64(h.data()+16,count_);put64(h.data()+24,payload_);
        std::memcpy(h.data()+32,arch_.data(),16);put64(h.data()+48,crc_);put64(h.data()+56,1);
        out_.seekp(0);out_.write(reinterpret_cast<const char*>(h.data()),64);out_.close();check(bool(out_),"container finish");
    }
};
struct Arc {uint32_t dst,edge;};
static_assert(sizeof(Arc)==8,"Arc has padding");
} // namespace dieroute::native
