"""Build the Progress Report 2 workflow as matching SVG, PDF and PNG exports.

Run with Python containing reportlab; PNG export also requires pdftoppm.
The diagram describes lockbox/core.py and lockbox/security.py, not a hardware
security certification. All timing values refer to simulation time.
"""
from html import escape
from pathlib import Path
import math
import subprocess

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/assets'
STEM = DEST / 'progress2-security-flow'
W, H = 1920, 1200
NAVY, CYAN, INK = '#102D45', '#087E92', '#15364E'
MUTED, LINE = '#50677B', '#BDCDD7'
RED, PALE_RED = '#A32B3A', '#FFF0F2'
FONT = Path.home() / 'Library/Fonts/AlbertSans-Regular.ttf'
BOLD = Path.home() / 'Library/Fonts/AlbertSans-ExtraBold.ttf'
if FONT.is_file() and BOLD.is_file():
    pdfmetrics.registerFont(TTFont('Flow', str(FONT)))
    pdfmetrics.registerFont(TTFont('FlowBold', str(BOLD)))
else:
    pdfmetrics.registerFont(pdfmetrics.Font('Flow', 'Helvetica', 'WinAnsiEncoding'))
    pdfmetrics.registerFont(pdfmetrics.Font('FlowBold', 'Helvetica-Bold', 'WinAnsiEncoding'))

DEST.mkdir(parents=True, exist_ok=True)
pdf = canvas.Canvas(str(STEM.with_suffix('.pdf')), pagesize=(W / 2, H / 2))
pdf.setTitle('Parcel Guard - Progress Report 2 Security Flow')
pdf.setAuthor('Parcel Guard - CS 5650')
pdf.setSubject('Owner-managed access, delivery, tamper lockdown and restart recovery')
pdf.scale(.5, .5)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
       '<title id="title">Parcel Guard security workflow</title>',
       '<desc id="desc">Password-only owner sign-in creates one-use codes. Access requires code, policy and measured device checks. Tampering revokes all codes and enters persistent lockdown. A fresh owner sign-in and measured secure state are required to clear it. Restart restores incidents and queued events, but cancels active access.</desc>']


def rect(x, y, w, h, fill, stroke=None, radius=0):
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke or fill)
    pdf.setLineWidth(2)
    pdf.roundRect(x, H - y - h, w, h, radius, fill=1, stroke=bool(stroke))
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="2"/>')


def text(x, y, label, size=24, color=INK, bold=False, anchor='start'):
    font = 'FlowBold' if bold else 'Flow'
    pdf.setFont(font, size)
    pdf.setFillColor(color)
    width = pdfmetrics.stringWidth(label, font, size)
    dx = width / 2 if anchor == 'middle' else width if anchor == 'end' else 0
    assert 0 <= x - dx and x - dx + width <= W, ('text outside canvas', label)
    pdf.drawString(x - dx, H - y, label)
    svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Albert Sans, Arial, sans-serif" font-size="{size}" font-weight="{800 if bold else 400}" text-anchor="{anchor}">{escape(label)}</text>')


def path(points, color=CYAN, arrow=True, dashed=False):
    pdf.setStrokeColor(color)
    pdf.setLineWidth(3)
    pdf.setDash([8, 6] if dashed else [])
    p = pdf.beginPath()
    p.moveTo(points[0][0], H - points[0][1])
    for x, y in points[1:]:
        p.lineTo(x, H - y)
    pdf.drawPath(p)
    pdf.setDash([])
    svg.append('<polyline points="' + ' '.join(f'{x},{y}' for x, y in points) + f'" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"' + (' stroke-dasharray="8 6"' if dashed else '') + '/>')
    if arrow:
        x, y = points[-1]
        px, py = points[-2]
        angle = math.atan2(y - py, x - px)
        wing = [(x, y), (x - 13 * math.cos(angle) + 6 * math.sin(angle), y - 13 * math.sin(angle) - 6 * math.cos(angle)),
                (x - 13 * math.cos(angle) - 6 * math.sin(angle), y - 13 * math.sin(angle) + 6 * math.cos(angle))]
        p = pdf.beginPath()
        p.moveTo(wing[0][0], H - wing[0][1])
        for xx, yy in wing[1:]:
            p.lineTo(xx, H - yy)
        p.close()
        pdf.setFillColor(color)
        pdf.drawPath(p, fill=1, stroke=0)
        svg.append('<polygon points="' + ' '.join(f'{xx},{yy}' for xx, yy in wing) + f'" fill="{color}"/>')


def box(x, y, w, h, title, details=(), danger=False):
    color = RED if danger else CYAN
    rect(x, y, w, h, PALE_RED if danger else '#EFF7FA', color, 12)
    title_size = min(27, 27 * (w - 48) / pdfmetrics.stringWidth(title, 'FlowBold', 27))
    assert title_size >= 22, ('title too long', title)
    text(x + 24, y + 34, title, title_size, RED if danger else INK, True)
    for i, label in enumerate(details):
        size = min(23, 23 * (w - 48) / pdfmetrics.stringWidth(label, 'Flow', 23))
        assert size >= 21, ('detail too long', title, label)
        text(x + 24, y + 66 + i * 28, label, size, MUTED)


def diamond(x, y, w, h, label, color=CYAN):
    points = [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
    pdf.setFillColor('#FFFFFF')
    pdf.setStrokeColor(color)
    pdf.setLineWidth(3)
    p = pdf.beginPath()
    p.moveTo(points[0][0], H - points[0][1])
    for xx, yy in points[1:]:
        p.lineTo(xx, H - yy)
    p.close()
    pdf.drawPath(p, fill=1, stroke=1)
    svg.append('<polygon points="' + ' '.join(f'{xx},{yy}' for xx, yy in points) + f'" fill="#FFFFFF" stroke="{color}" stroke-width="3"/>')
    text(x + w / 2, y + h / 2 + 9, label, 27, color, True, 'middle')


rect(0, 0, W, H, '#FFFFFF')
rect(0, 0, W, 160, NAVY)
rect(64, 33, 6, 25, '#48D4D3')
text(86, 54, 'PARCEL GUARD  /  PROGRESS REPORT 2', 22, '#76E0DD', True)
text(64, 111, 'Layered security: access, delivery and recovery', 46, '#FFFFFF', True)
text(1855, 140, 'CS 5650', 21, '#C1D8E3', anchor='end')

for x, number, label in [(70, '01', 'OWNER PROVISIONS ACCESS'), (665, '02', 'BOX VALIDATES & OPERATES'), (1330, '03', 'TAMPER & OWNER RECOVERY')]:
    text(x, 212, number, 24, CYAN, True)
    text(x + 48, 212, label, 23, INK, True)
path([(610, 190), (610, 1115)], LINE, False)
path([(1290, 190), (1290, 1115)], LINE, False)

# Owner path. Rejected passwords never establish an owner session.
box(70, 250, 450, 122, 'Password-only owner sign-in', ['Invalid password: deny sign-in.', '5 failures: pause for 60 s.'])
path([(295, 372), (295, 425)])
text(311, 407, 'VALID PASSWORD', 19, CYAN, True)
box(70, 425, 450, 94, 'Owner session: 300 s', ['Re-sign-in replaces the old session.'])
path([(295, 519), (295, 575)])
box(70, 575, 450, 124, 'Create / revoke access codes', ['Courier delivery or owner collection.', 'Lifetime: 30-3600 simulated s.'])
path([(295, 699), (295, 777)])
box(70, 777, 450, 124, 'Share an 8-digit one-use code', ['Plaintext is shown only once.', 'Only its keyed digest is saved.'])
path([(520, 839), (575, 839), (575, 295), (665, 295)])
text(70, 967, 'Owner authentication', 24, INK, True)
text(70, 1002, 'controls code creation and recovery.', 23, MUTED)
text(70, 1037, 'A separate one-use code controls', 23, MUTED)
text(70, 1072, 'the physical access request.', 23, MUTED)

# Access policy branches. A denial is not automatically a tamper incident.
box(665, 250, 430, 94, 'Request access', ['Code + role + fresh request ID.'])
path([(880, 344), (880, 420)])
diamond(665, 420, 430, 140, 'Access permitted?')
path([(1095, 490), (1130, 490)], RED)
text(1100, 474, 'NO', 18, RED, True)
rect(1130, 438, 133, 104, PALE_RED, RED, 10)
text(1196, 470, 'Deny', 26, RED, True, 'middle')
text(1196, 500, 'access', 26, RED, True, 'middle')
text(1196, 528, 'Log reason', 20, MUTED, anchor='middle')
path([(880, 560), (880, 640)])
text(898, 602, 'YES', 20, CYAN, True)
box(665, 640, 430, 94, 'Consume code; grant access', ['20 s access window; code used once.'])
path([(880, 734), (880, 788)])
box(665, 788, 430, 94, 'Open; place or collect parcel', ['Sensors track the authorized action.'])
path([(880, 882), (880, 936)])
box(665, 936, 430, 122, 'Close door; confirm bolt locked', ['Delivery confirmed only when secure.', 'Ready for a fresh delivery code.'])
text(665, 1093, 'Checks: code, role, expiry, replay, cooldown;', 22, MUTED)
text(665, 1122, 'no lockdown; healthy storage + secure devices.', 22, MUTED)

# Tamper monitoring is concurrent with normal operation.
box(1330, 250, 500, 122, 'Tamper detected during monitoring', ['Impact or unapproved door / parcel action.', 'Strong impact also during granted access.'], True)
path([(1580, 372), (1580, 425)], RED)
box(1330, 425, 500, 150, 'Enter persistent lockdown', ['Revoke every code; sign out the owner.', 'Cancel active access; request closure.', 'Save the incident; queue the alert.'], True)
path([(1580, 575), (1580, 648)], RED)
box(1330, 648, 500, 122, 'Owner signs in again with password', ['Close the door and confirm bolt locking.', 'Resolve sensor, actuator and storage faults.'])
path([(1580, 770), (1580, 817)])
diamond(1360, 817, 440, 134, 'Signed in + secured?')
path([(1800, 884), (1860, 884), (1860, 709), (1830, 709)], RED)
text(1820, 870, 'NO', 19, RED, True)
path([(1580, 951), (1580, 1003)])
text(1597, 984, 'YES', 20, CYAN, True)
box(1330, 1003, 500, 94, 'Clear lockdown; issue fresh codes', ['Old codes stay revoked. Reset cannot bypass.'])

path([(64, 1148), (1856, 1148)], LINE, False)
text(64, 1183, 'RESTART', 19, CYAN, True)
text(172, 1183, 'Restore incidents, code state and unacknowledged events; cancel access and owner sessions. Faults block new access. All times are simulated.', 21, MUTED)

svg.append('</svg>')
STEM.with_suffix('.svg').write_text('\n'.join(svg) + '\n')
pdf.showPage()
pdf.save()
subprocess.run(['pdftoppm', '-singlefile', '-scale-to', '2880', '-png', str(STEM.with_suffix('.pdf')), str(STEM)], check=True)
print(f'Built {STEM}.svg / .pdf / .png')
