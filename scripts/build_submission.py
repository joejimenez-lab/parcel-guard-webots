"""Build the final paper from checked evaluation reports and editable Markdown."""
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderPDF, renderSVG

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf'
INK=colors.HexColor('#19302e'); TEAL=colors.HexColor('#146b57'); MUTED=colors.HexColor('#526662'); LIGHT=colors.HexColor('#edf4f1')

def load(name):
    d=json.loads((ROOT/'results'/f'{name}.json').read_text())
    if not d.get('passed'): raise SystemExit(f'Refusing to publish failed evidence: {name}')
    return d


def diagram():
    d=Drawing(504,240)
    def node(x,y,w,h,title,subtitle):
        d.add(Rect(x,y,w,h,fillColor=LIGHT,strokeColor=TEAL,strokeWidth=.7))
        d.add(String(x+w/2,y+h-16,title,textAnchor='middle',fontName='Helvetica-Bold',fontSize=9,fillColor=INK))
        for i,line in enumerate(subtitle.split('\n')):
            d.add(String(x+w/2,y+h-30-i*11,line,textAnchor='middle',fontName='Helvetica',fontSize=8,fillColor=INK))
    def arrow(x1,y1,x2,y2,label='',lx=None,ly=None):
        d.add(Line(x1,y1,x2,y2,strokeColor=TEAL,strokeWidth=1))
        import math
        a=math.atan2(y2-y1,x2-x1);q=5
        d.add(Polygon([x2,y2,x2-q*math.cos(a-.5),y2-q*math.sin(a-.5),x2-q*math.cos(a+.5),y2-q*math.sin(a+.5)],fillColor=TEAL,strokeColor=TEAL))
        if label:d.add(String(lx if lx is not None else (x1+x2)/2,ly if ly is not None else (y1+y2)/2+5,label,textAnchor='middle',fontSize=7.5,fillColor=MUTED))
    node(0,168,136,62,'Virtual devices','Distance / joint position\nDoor acceleration')
    node(182,168,136,62,'P1 Sensor filter','Validity / hysteresis\nConsecutive samples')
    node(364,168,140,62,'P2 Controller','Access / event rules\nMotor targets / status')
    arrow(136,199,182,199,'samples')
    arrow(318,199,364,199,'states')
    node(364,65,140,58,'Owner / courier UI','Role + code + request ID\nStatus / event history')
    arrow(418,168,418,123,'status',396,143);arrow(455,123,455,168,'request',479,143)
    node(182,65,136,58,'D1 Pending outbox','Session + event ID\nRetain until ACK')
    arrow(364,177,318,113,'events',327,151)
    node(0,65,136,58,'P3 Local endpoint','D2 Unique receipt IDs\nDeduplicate / acknowledge')
    arrow(182,104,136,104,'retry',158,110);arrow(136,82,182,82,'ACK',159,68)
    node(0,0,504,35,'Independent Supervisor fixture and test runners','Scene stimuli and motor faults; truth labels go only to the scorer')
    # Fixture-to-devices path sits outside the endpoint, with no classifier label input.
    d.add(Line(340,35,340,143,strokeColor=MUTED,strokeWidth=.7))
    d.add(Line(340,143,68,143,strokeColor=MUTED,strokeWidth=.7))
    arrow(68,143,68,168,'scene stimuli',217,132)
    return d


def main():
    s=load('webots_sensor_trials'); c=load('webots_classification'); b=load('webots_benchmark')['checks']
    load('webots_edge_cases'); r=load('robustness'); load('evaluation_manifest')
    values={'PRESENCE':f"{s['correct']}/50",'F1':f"{c['macro_f1']:.2f}",'FALSE':str(c['false_alarms']),
            'CYCLES':str(b['motor_cycles']['successful']),'LATENCY':str(b['alert_latency']['within_1s']),
            'RECOVERED':str(b['connection_recovery']['recovered_events']),'UNAUTHORIZED':str(b['access_security']['unauthorized_unlocks']),
            'BASELINE':f"{c['motion_only_macro_f1']:.2f}",'OBSERVER':f"{b['alert_latency']['max_stimulus_to_observer_s']:.3f}",'REGRESSIONS':str(len(r['checks']))}
    labels=('benign_motion','delivery','retrieval','tamper')
    for i,a in enumerate(labels):
        for j,z in enumerate(labels):values[f'CM{i}{j}']=str(c['confusion_matrix'][a][z])
    text=(ROOT/'docs/report_source.md').read_text()
    for k,v in values.items(): text=text.replace('@'+k+'@',v)
    if re.search(r'@[A-Z0-9]+@',text):raise SystemExit('Unresolved report field')
    (ROOT/'docs/FINAL_REPORT.md').write_text(text)
    OUT.mkdir(exist_ok=True,parents=True)
    d=diagram();renderPDF.drawToFile(d,str(ROOT/'docs/assets/data-flow.pdf'));renderSVG.drawToFile(d,str(ROOT/'docs/assets/data-flow.svg'))
    styles={
        'body':ParagraphStyle('Body',fontName='Helvetica',fontSize=10,leading=13.1,textColor=INK,spaceAfter=6),
        'h1':ParagraphStyle('Heading',fontName='Helvetica-Bold',fontSize=22,leading=26,textColor=TEAL,spaceAfter=14),
        'h2':ParagraphStyle('Subheading',fontName='Helvetica-Bold',fontSize=12.3,leading=16,textColor=INK,spaceBefore=8,spaceAfter=6),
        'table':ParagraphStyle('Cell',fontName='Helvetica',fontSize=8.7,leading=11.0,textColor=INK),
        'cover':ParagraphStyle('Cover',fontName='Helvetica-Bold',fontSize=40,leading=46,textColor=TEAL,spaceAfter=12),
    }
    def fmt(t):
        t=escape(t)
        t=re.sub(r'`([^`]+)`',r'<font face="Courier" size="8.6">\1</font>',t)
        t=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',t)
        # Wrap long reference URLs at meaningful boundaries without changing their text.
        t=re.sub(r'https://[^\s]+',lambda m:'<link href="'+m.group(0).rstrip('.')+'" color="#146b57">'+m.group(0)+'</link>',t)
        return t
    story=[];lines=text.splitlines();i=0;page=1
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line:continue
        if line=='<!-- page -->':story.append(PageBreak());page+=1;continue
        if line.startswith('# '):story.append(Paragraph(fmt(line[2:]),styles['cover' if page==1 else 'h1']));continue
        if line.startswith('## '):story.append(Paragraph(fmt(line[3:]),styles['h2']));continue
        if line.startswith('!['):
            target=re.search(r'\]\((.+)\)',line).group(1)
            if target.endswith('data-flow.svg'):story.append(diagram())
            else:
                im=Image(str(ROOT/'docs'/target));scale=min(504/im.imageWidth,285/im.imageHeight);im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale;story.append(im)
            story.append(Spacer(1,12));continue
        if line.startswith('|'):
            rows=[line]
            while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i].strip());i+=1
            rows=[r for r in rows if not re.match(r'^\|[\s:|\-]+\|$',r)]
            parsed=[[Paragraph(fmt(c.strip()),styles['table']) for c in r.strip('|').split('|')] for r in rows]
            n=len(parsed[0]);widths={2:[170,334],3:[174,205,125],4:[28,272,102,102],5:[164,85,85,85,85]}.get(n,[504/n]*n)
            if n==2 and 'Section' in rows[0]:widths=[440,64]
            if n==3 and 'ID' in rows[0]:widths=[30,242,232]
            if n==3 and 'Measure' in rows[0]:widths=[270,145,89]
            table=Table(parsed,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.8,TEAL),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#cbd8d3')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.extend([table,Spacer(1,13)]);continue
        para=[line]
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','![','<!--')):para.append(lines[i].strip());i+=1
        story.append(Paragraph(fmt(' '.join(para)),styles['body']))
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#cbd8d3'));canvas.line(54,43,558,43)
        canvas.setFont('Helvetica',8);canvas.setFillColor(MUTED);canvas.drawString(54,29,'PARCEL GUARD  /  CS 5650  /  FINAL REPORT');canvas.drawRightString(558,29,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(OUT/'Parcel Guard - Final Report.pdf'),pagesize=(612,792),leftMargin=54,rightMargin=54,topMargin=48,bottomMargin=57,title='Parcel Guard: Package Delivery Security Box',author='Joshua Guico, Joe Jimenez, Brandon Lopez')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print('Built final report from current evaluation data')

if __name__=='__main__':main()
