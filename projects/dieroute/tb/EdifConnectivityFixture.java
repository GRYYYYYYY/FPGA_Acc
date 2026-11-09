import com.xilinx.rapidwright.edif.*;
import java.nio.file.*;

/** Small explicit connectivity fixtures, independent of the flattening code. */
public final class EdifConnectivityFixture {
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("mode new.edf");
        String mode=args[0];Path output=Path.of(args[1]);if(Files.exists(output))throw new IllegalArgumentException("exists");
        EDIFNetlist n=EDIFTools.createNewNetlist("fixture");EDIFCell top=n.getTopCell();
        EDIFCell gate=new EDIFCell(n.getWorkLibrary(),"opaque");
        EDIFPort a=gate.createPort("A[2:3]",EDIFDirection.INPUT,2),y=gate.createPort("Y",EDIFDirection.OUTPUT,1);
        EDIFPort u=gate.createPort("U",EDIFDirection.INPUT,1),io=gate.createPort("IO",EDIFDirection.INOUT,1);
        if(!mode.equals("drop_spare"))gate.createPort("SPARE",EDIFDirection.INPUT,1);
        EDIFCell inner=new EDIFCell(n.getWorkLibrary(),"inner");
        EDIFPort b=inner.createPort("B[3:2]",EDIFDirection.INPUT,2),q=inner.createPort("Q",EDIFDirection.OUTPUT,1);
        EDIFPort c=inner.createPort("C",EDIFDirection.INPUT,1),bi=inner.createPort("BI",EDIFDirection.INOUT,1);
        EDIFCellInst g=new EDIFCellInst("gate",gate,inner);g.addProperty("MODE",mode.equals("property")?"B":"A");
        for(int i=0;i<2;i++){EDIFNet net=inner.createNet((mode.equals("rename")?"renamed_":"n_")+i);net.createPortInst(b,i);net.createPortInst(a,i,g);}
        EDIFNet net=inner.createNet("result");net.createPortInst(q);net.createPortInst(y,g);
        net=inner.createNet("constant");net.createPortInst(c);net.createPortInst(u,g);
        net=inner.createNet("bidirectional");net.createPortInst(bi);net.createPortInst(io,g);
        EDIFCell pass=new EDIFCell(n.getWorkLibrary(),"wire_only");
        EDIFPort pi=pass.createPort("I",EDIFDirection.INPUT,1),po=pass.createPort("O",EDIFDirection.OUTPUT,1);
        net=pass.createNet("alias");net.createPortInst(pi);net.createPortInst(po);
        EDIFCell outer=new EDIFCell(n.getWorkLibrary(),"outer");
        EDIFPort p=outer.createPort("P[5:4]",EDIFDirection.INPUT,2),r=outer.createPort("R",EDIFDirection.OUTPUT,1);
        EDIFPort oc=outer.createPort("C",EDIFDirection.INPUT,1),ob=outer.createPort("BI",EDIFDirection.INOUT,1);
        EDIFCellInst w=new EDIFCellInst("w",inner,outer),pw=new EDIFCellInst("wire",pass,outer);
        net=outer.createNet("pass_in");net.createPortInst(p,0);net.createPortInst(pi,pw);
        net=outer.createNet("pass_out");net.createPortInst(po,pw);net.createPortInst(b,0,w);
        net=outer.createNet("direct");net.createPortInst(p,1);net.createPortInst(b,1,w);
        net=outer.createNet("result");net.createPortInst(r);net.createPortInst(q,w);
        net=outer.createNet("constant");net.createPortInst(oc);net.createPortInst(c,w);
        net=outer.createNet("bidirectional");net.createPortInst(ob);net.createPortInst(bi,w);
        outer.createNet("no_terminal");
        EDIFPort ti=top.createPort("T[3:0]",EDIFDirection.INPUT,4),to=top.createPort("O[1:0]",EDIFDirection.OUTPUT,2);
        EDIFPort tb=top.createPort("BIO",EDIFDirection.INOUT,1);
        EDIFNet bus=top.createNet("bidirectional");bus.createPortInst(tb);
        EDIFNet constant=top.createNet("used_constant");
        for(int j=0;j<2;j++) {
            EDIFCellInst child=new EDIFCellInst("u"+j,outer,top);
            for(int i=0;i<2;i++) {
                net=top.createNet("input_"+j+"_"+i);net.createPortInst(ti,2*j+(mode.equals("swap")&&j==0?1-i:i));net.createPortInst(p,i,child);
            }
            net=top.createNet("output_"+j);net.createPortInst(to,j);net.createPortInst(r,child);
            bus.createPortInst(ob,child);if(j==0)constant.createPortInst(oc,child);
        }
        EDIFCell vcc=new EDIFCell(n.getHDIPrimitivesLibrary(),"VCC");EDIFPort vp=vcc.createPort("P",EDIFDirection.OUTPUT,1);
        if(!mode.equals("drop_used")){EDIFCellInst vc=new EDIFCellInst("used_const",vcc,top);constant.createPortInst(vp,vc);}
        if(!mode.equals("drop_dead")){EDIFCellInst vc=new EDIFCellInst("dead_const",vcc,top);top.createNet("unused_constant").createPortInst(vp,vc);}
        n.exportEDIF(output,true);
    }
}
