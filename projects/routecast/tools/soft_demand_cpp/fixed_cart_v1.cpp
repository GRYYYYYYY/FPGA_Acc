#include <cstdint>
#include <vector>
#include <cmath>
#include <algorithm>
#include <stdexcept>
using U=uint64_t;using W=unsigned __int128;
struct Node{int64_t feature=-1,left=-1,right=-1;U rows=0,positive=0;double threshold=0;};
struct Builder{
 U n,d,depth_limit,minleaf,capacity;const double*x,*y;std::vector<Node>nodes;
 U build(const std::vector<U>&rows,U depth){
  if(nodes.size()>=capacity)throw std::length_error("capacity");U index=nodes.size(),N=rows.size(),P=0;for(U r:rows)P+=y[r]==1;Node node;node.rows=N;node.positive=P;nodes.push_back(node);
  if(depth>=depth_limit||N<2*minleaf||!P||P==N)return index;
  W bestnum=W(P)*P,bestden=N;int64_t feature=-1;double threshold=0;
  for(U f=0;f<d;f++){
   auto order=rows;std::sort(order.begin(),order.end(),[&](U a,U b){double u=x[a*d+f],v=x[b*d+f];return u<v||(u==v&&a<b);});U lp=0;
   for(U i=0;i+1<N;i++){lp+=y[order[i]]==1;U a=i+1,b=N-a;if(a<minleaf||b<minleaf||x[order[i]*d+f]==x[order[i+1]*d+f])continue;U rp=P-lp;W numerator=W(lp)*lp*b+W(rp)*rp*a,denominator=W(a)*b;
    if(numerator*bestden>bestnum*denominator){bestnum=numerator;bestden=denominator;feature=f;threshold=x[order[i]*d+f];}
   }
  }
  if(feature<0)return index;std::vector<U>left,right;for(U r:rows)(x[r*d+feature]<=threshold?left:right).push_back(r);if(left.size()<minleaf||right.size()<minleaf)throw std::runtime_error("split domain");U a=build(left,depth+1),b=build(right,depth+1);nodes[index].feature=feature;nodes[index].threshold=threshold;nodes[index].left=a;nodes[index].right=b;return index;
 }
};
extern "C" int rc_fixed_cart(U n,U d,const double*x,const double*y,U depth,U minleaf,U capacity,int64_t*metadata,double*thresholds,U*node_count){
 try{
  if(!n||n>1000000||!d||d>256||depth>16||!minleaf||minleaf>1000000||!capacity||capacity>131071||!x||!y||!metadata||!thresholds||!node_count)return -1;
  for(U i=0;i<n*d;i++)if(!std::isfinite(x[i]))return -2;for(U i=0;i<n;i++)if(y[i]!=0&&y[i]!=1)return -2;
  Builder b{n,d,depth,minleaf,capacity,x,y,{}};std::vector<U>rows(n);for(U i=0;i<n;i++)rows[i]=i;b.build(rows,0);
  for(U i=0;i<b.nodes.size();i++){const auto&r=b.nodes[i];metadata[i*5]=r.feature;metadata[i*5+1]=r.left;metadata[i*5+2]=r.right;metadata[i*5+3]=r.rows;metadata[i*5+4]=r.positive;thresholds[i]=r.threshold;}*node_count=b.nodes.size();return 0;
 }catch(const std::length_error&){return -4;}catch(...){return -9;}
}
