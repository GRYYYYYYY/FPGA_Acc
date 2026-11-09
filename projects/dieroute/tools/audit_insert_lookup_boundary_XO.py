"""Audit actual hardware XO provenance, ABI and generated caller register boundary."""
from pathlib import Path
import hashlib,json,re,zipfile
import xml.etree.ElementTree as ET
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        xml_name, = [n for n in archive.namelist() if n.endswith('/kernel.xml')]
        kernel = ET.fromstring(archive.read(xml_name)).find('kernel')
        assert kernel is not None
        assert kernel.attrib['name'] == 'dieroute_net_commit_sharded_hbm'
        ports = [dict(p.attrib) for p in kernel.findall('ports/port')]
        args = [dict(a.attrib) for a in kernel.findall('args/arg')]
        assert len(args) == 29
        assert sum(a['addressQualifier'] == '1' for a in args) == 17
        assert sum(p['mode'] == 'master' for p in ports) == 7
        member, = [n for n in archive.namelist() if n.endswith('/dieroute_net_commit_sharded_hbm_csynth.rpt')]
        raw = archive.read(member)
    report = raw.decode()
    clock = re.search(r'\|ap_clk\s*\|\s*([\d.]+) ns\|\s*([\d.]+) ns\|\s*([\d.]+) ns\|', report)
    assert clock
    total = re.search(r'^\|Total\s*\|([^\n]+)', report.split('== Utilization Estimates', 1)[1], re.M)
    values = [int(v.strip()) for v in total[1].split('|') if v.strip()]
    assert len(values) == 5
    return dict(xo_sha256=sha(path), ports=ports, args=args,
                control_protocol=kernel.attrib['hwControlProtocol'],
                version=re.search(r'\* Version:\s+(.+)', report)[1],
                device=re.search(r'\* Target device:\s+(\S+)', report)[1],
                target_ns=float(clock[1]), estimated_ns=float(clock[2]),
                uncertainty_ns=float(clock[3]),
                resources=dict(zip(['BRAM_18K', 'DSP', 'FF', 'LUT', 'URAM'], values)),
                report_sha256=hashlib.sha256(raw).hexdigest())


R=Path(__file__).resolve().parents[1]
D=R/'work/insert_lookup_boundary_hw_20261020'
B=R/'work/negotiate_scan_helper_hw_20261020'
def main():
 refs={}
 def sha(p):
  p=Path(p);v=hashlib.sha256(p.read_bytes()).hexdigest();refs[str(p)]=v;return v
 protocol=json.loads((D/'protocol.json').read_text())
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 m=json.loads((D/'manifest.json').read_text());assert m['returncode']==0
 a=inspect(B/'commit.xo');b=inspect(D/'commit.xo')
 assert len(b['ports'])==8 and len(b['args'])==29
 assert b['device']=='xcu280-fsvh2892-2L-e'
 for k in ['ports','args','control_protocol','version','device','target_ns','uncertainty_ns']:assert a[k]==b[k],k
 source=D/'source/net_commit_sharded_hbm.cpp'
 with zipfile.ZipFile(D/'commit.xo') as z:
  matches=[n for n in z.namelist() if n.endswith('/net_commit_sharded_hbm.cpp')]
  assert matches and all(z.read(n)==source.read_bytes() for n in matches),matches
 sol=D/'commit_temp/commit/dieroute_net_commit_sharded_hbm/dieroute_net_commit_sharded_hbm/solution'
 rtl=sol/'syn/verilog/dieroute_net_commit_sharded_hbm_p_anonymous_namespace_insert.v'
 t=rtl.read_text()
 pos=re.search(r'\.pos_r\((pos_reg_\d+)\)',t);err=re.search(r'\.p_read\((this_error_ret_reg_\d+)\)',t)
 assert pos and err
 pattern=r"always @ \(posedge ap_clk\) begin\s+if \(\(1'b1 == (ap_CS_fsm_state\d+)\)\) begin\s+"+pos[1]+r' <= grp_p_anonymous_namespace_locate_fu_\d+_ap_return_0;\s+'+err[1]+r' <= grp_p_anonymous_namespace_locate_fu_\d+_ap_return_1;'
 capture=re.search(pattern,t);assert capture,'lookup result capture missing'
 for f in [D/'commit.xo',B/'commit.xo',D/'protocol.json',D/'manifest.json',source,rtl,Path(__file__)]:sha(f)
 result={'status':'actual_XO_ABI_embedded_source_and_caller_capture_verified','arguments':len(b['args']),'ports':len(b['ports']),'caller_capture_state':capture[1],'caller_capture_registers':[pos[1],err[1]],'HLS_resources':b['resources'],'HLS_estimated_period_ns':b['estimated_ns'],'resource_delta_vs_parent':{k:b['resources'][k]-v for k,v in a['resources'].items()},'source_sha256':refs,'scope':'Actual hw XO compile with exact embedded candidate CPP and same external ABI. Caller lookup registers present in generated compile RTL; physical synthesis preservation, routed timing and board operation remain unproven.','adopted':False,'research_complete':False}
 with (D/'compiled_XO_review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
