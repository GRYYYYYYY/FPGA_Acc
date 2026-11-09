#include <cstdint>
#include <iostream>
#include <vector>
#include <deque>
#include <utility>
#include <algorithm>
#include <fstream>
using namespace std;
ofstream isolation_log;uint64_t isolation_fixes=0;int n; uint64_t states=0,limit;bool limited=false;vector<int> counts,answer;vector<vector<vector<uint64_t>>> support;vector<vector<int>> neighbors;
bool search(vector<uint64_t> domains){
 if(states>=limit){limited=true;return false;}++states;
 deque<pair<int,int>> q;
 for(int i=0;i<n;i++)for(int j:neighbors[i])q.emplace_back(i,j);
 while(!q.empty()){
  auto [i,j]=q.front();q.pop_front();auto old=domains[i],next=old;
  for(int a=0;a<counts[i];a++)if((old>>a&1)&&!(support[i][j][a]&domains[j]))next&=~(uint64_t(1)<<a);
  if(next!=old){domains[i]=next;if(!next)return false;for(int k:neighbors[i])if(k!=j)q.emplace_back(k,i);}
 }
 // A variable with universal support on all current domains has no residual constraint.
 for(int i=0;i<n;i++)if(__builtin_popcountll(domains[i])>1){
  bool independent=true;
  for(int j:neighbors[i])for(int a=0;a<counts[i];a++)if((domains[i]>>a&1)&&((support[i][j][a]&domains[j])!=domains[j]))independent=false;
  if(independent){
   int chosen=__builtin_ctzll(domains[i]);
   if(isolation_fixes<256){isolation_log<<i<<" "<<chosen;for(auto d:domains)isolation_log<<" "<<d;isolation_log<<"\n";}
   ++isolation_fixes;domains[i]=uint64_t(1)<<chosen;
  }
 }
 int best=-1,size=65,degree=-1;
 for(int i=0;i<n;i++){int c=__builtin_popcountll(domains[i]),d=0;for(int j:neighbors[i])d+=__builtin_popcountll(domains[j])>1;if(c>1&&(c<size||(c==size&&d>degree))){best=i;size=c;degree=d;}}
 if(best<0){answer.clear();for(auto d:domains)answer.push_back(__builtin_ctzll(d));return true;}
 vector<pair<int,int>> ranked;
 for(int a=0;a<counts[best];a++)if(domains[best]>>a&1){int preserved=0;for(int j:neighbors[best])preserved+=__builtin_popcountll(support[best][j][a]&domains[j]);ranked.emplace_back(-preserved,a);}
 sort(ranked.begin(),ranked.end());
 for(auto entry:ranked){int a=entry.second;auto child=domains;child[best]=uint64_t(1)<<a;if(search(child))return true;if(limited)return false;}
 return false;
}
int main(int argc,char** argv){if(argc!=2)return 2;isolation_log.open(argv[1]);if(!isolation_log)return 2;if(!(cin>>n>>limit)||n<1||n>1000||limit<1)return 2;counts.resize(n);vector<uint64_t> domains;for(auto &c:counts){cin>>c;if(c<1||c>63)return 2;domains.push_back((uint64_t(1)<<c)-1);}support.resize(n,vector<vector<uint64_t>>(n));neighbors.resize(n);
 for(int i=0;i<n;i++)for(int j=0;j<n;j++)if(i!=j){bool restrict=false;for(int a=0;a<counts[i];a++){uint64_t m;cin>>m;if(!cin||m>domains[j])return 2;support[i][j].push_back(m);restrict|=m!=domains[j];}if(restrict)neighbors[i].push_back(j);}
 bool found=search(domains);cout<<(found?"FOUND":limited?"SELECTION_LIMIT":"EXHAUSTED_UNCERTIFIED")<<" "<<states<<"\n";if(found){for(auto a:answer)cout<<a<<" ";cout<<"\n";}cerr<<"isolation_fixes "<<isolation_fixes<<"\n";return 0;}
