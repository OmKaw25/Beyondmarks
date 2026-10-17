from pathlib import Path
import html
import io
import json
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SHOTS=ROOT/'docs'/'screenshots'
# Screenshot names, captions and crop coordinates are traceable to unchanged app captures.
SCREENS=[
 ('R1 · Reasoning evidence','Investigate the explanation','03-investigation-1440-light.png',
  'The learner identifies a flawed explanation, categorizes the issue and explains their thinking. Confidence and context add their perspective; a correct answer alone is not treated as proof of understanding.',(260,710,1405,1580)),
 ('R2 · Learner agency','Keep more than one explanation open','04-interpretation-1440-light.png',
  'Competing interpretations remain provisional. Evidence summaries and learner disagreement preserve what the system believed and what the learner says. These authored weights are not probabilities of ability.',(260,720,1405,1540)),
 ('R3 · Diagnostic interaction','Ask one useful next question','05-follow-up-1440-light.png',
  'The selected probe asks for new evidence. Its rationale exposes competing predictions and the burden tradeoff. Different output, reading and unhurried probes test different possible explanations.',(260,1120,1405,2080)),
 ('R4 · Supported learning','Make the reasoning visible','11-support-1440-light.png',
  'A worked example leads to a learner prediction and feedback. Learners read the feedback before continuing. A failed practice response leads to another example rather than an unsupported success label.',(260,620,1405,1390)),
 ('R4 · Transfer','Apply the idea in a changed context','12-transfer-1440-light.png',
  'Transfer requires applying the rule to a different task. The learner supplies a repair, output and structured reasoning; failed checks return to support and fresh practice.',(260,730,1405,1710)),
 ('R4 · Independent check','Check what the learner can do alone','06-independent-1440-light.png',
  'Independent work removes current hints and answer reveals. The learner supplies a solution and reasoning. Filled fields are demonstration responses, not measured participant outcomes.',(260,640,1405,1610)),
 ('R4 · Reflection','Challenge an overgeneralized claim','17-reflection-1440-light.png',
  'A reflection task asks the learner to test a claim and justify a counterexample. Completion requires structured evidence across the investigation, rather than advancing after an incorrect response.',(260,650,1405,1670)),
 ('R4 · Real elapsed time','Return after seven and thirty days','22-delayed-checks-1440-light.png',
  'This actual recording account completed the flow on 17 October. The server scheduled checks for 24 October and 16 November 2026. These are future appointments, not completed retention outcomes. The account is demonstration activity, not a pilot participant.',(260,700,1405,1050)),
 ('R4 · Adaptation','Keep the earlier evidence when support changes','08-adaptation-1440-light.png',
  'The adaptation view preserves earlier and revised interpretations and directs the learner to changed support. Historical seeded examples are synthetic demonstrations; genuine delayed failures use separately persisted observations.',(260,670,1405,1560)),
 ('Teacher workspace','Review a learner’s reasoning history','09-teacher-evidence-1440-light.png',
  'Only an assigned teacher can inspect the learner’s evidence. The timeline preserves earlier reasoning and interpretations; pagination loads bounded pages across evidence types.',(260,250,1405,930)),
 ('Teacher roster','Find the student who needs your attention','24-teacher-roster-1440-light.png',
  'Teachers can search their own students by username, hide sample accounts and navigate bounded roster pages. Search does not expose students from another class. Enrollment guidance points directly to the reusable class code.',(260,210,1405,1120)),
 ('Classroom extension','Create learning beyond the initial curriculum','18-class-quiz-1440-light.png',
  'Teachers can add subjects and lessons, then publish quizzes with answer keys and reasoning guidance. Students see only published quizzes in their assigned class and submit answers with explanations.',(260,350,1405,1250)),
 ('Human review of AI','Correct feedback without erasing its origin','23-teacher-feedback-review-1440-light.png',
  'This actual teacher review awards partial reasoning credit while preserving an incorrect answer. A student concern is resolved, the teacher’s reason stays in the audit trail, and the original AI feedback remains available.',(260,1760,1405,2480)),
 ('Evidence-informed next steps','Recommend a course to revisit','19-course-recommendations-1440-light.png',
  'The classroom orders courses using the learner’s latest eligible quiz evidence. Teacher corrections refresh the stored course summary. This is an individual learning recommendation, not a ranking of students.',(260,600,1405,1360)),
 ('Responsive interface','Keep practice usable on a phone','21-fresh-practice-390-dark.png',
  'The mobile dark theme retains the same saved task, feedback and recovery path. Screenshots are captured from the actual app at 390px and 1440px; presentation does not replace accessibility or classroom usability evaluation.',None),
]

pdfmetrics.registerFont(TTFont('Segoe', 'C:/Windows/Fonts/segoeui.ttf'))
pdfmetrics.registerFont(TTFont('SegoeBold', 'C:/Windows/Fonts/segoeuib.ttf'))
W,H=landscape(A4)
BG=HexColor('#F6F3EB'); GREEN=HexColor('#245C43'); TEXT=HexColor('#182B23'); MUTED=HexColor('#526158'); BORDER=HexColor('#CAD2C5')
style=ParagraphStyle('caption',fontName='Segoe',fontSize=11,leading=16,textColor=TEXT)
small=ParagraphStyle('small',parent=style,fontSize=9,leading=13,textColor=MUTED)
c=canvas.Canvas(str(OUT/'frontend-pack.pdf'),pagesize=(W,H),pageCompression=1)
c.setTitle('Beyond Marks | Captioned Frontend Pack');c.setAuthor('Beyond Marks')

def base(number,kicker,title):
 c.setFillColor(BG);c.rect(0,0,W,H,fill=1,stroke=0)
 c.setFillColor(GREEN);c.setFont('SegoeBold',10);c.drawString(34,H-31,'BEYOND MARKS  /  FRONTEND PACK')
 c.setFont('Segoe',9);c.drawRightString(W-34,H-31,f'{number:02d}  /  17 OCT 2026')
 c.setFillColor(MUTED);c.setFont('SegoeBold',10);c.drawString(34,H-59,kicker.upper())
 c.setFillColor(TEXT);c.setFont('SegoeBold',24);c.drawString(34,H-91,title)
 c.setStrokeColor(BORDER);c.line(34,31,W-34,31)
 c.setFillColor(MUTED);c.setFont('Segoe',8);c.drawString(34,18,'Actual application captures · Demonstration and test accounts · No longitudinal outcome claim')

def para(text,x,y,width,sty=style):
 p=Paragraph(html.escape(text),sty);_,height=p.wrap(width,500);p.drawOn(c,x,y-height);return height

def picture(im,x,y,width,height):
 scale=min(width/im.width,height/im.height);dw=im.width*scale;dh=im.height*scale
 c.setFillColor(HexColor('#FFFEFA'));c.setStrokeColor(BORDER);c.roundRect(x-4,y-4,width+8,height+8,8,fill=1,stroke=1)
 c.drawImage(ImageReader(im),x+(width-dw)/2,y+(height-dh)/2,dw,dh,mask='auto')

base(1,'Reasoning, agency and learning over time','Understanding comes first')
para('A persistent learning workspace for introductory programming learners and their teachers.',34,H-120,W-68)
cover=PILImage.open(SHOTS/'01-landing-1440-light.png').convert('RGB')
picture(cover,34,140,480,285)
para('What the interface makes visible',542,417,265,ParagraphStyle('coverhead',parent=style,fontName='SegoeBold',fontSize=15,leading=20))
para('1. Reasoning behind an answer\n2. Competing interpretations\n3. A useful diagnostic probe\n4. Support, transfer and real delayed checks'.replace('\n',' • '),542,378,265)
para('Teachers also publish class quizzes and append audited corrections to AI feedback. Learners can challenge an interpretation and request help.',542,269,265)
para('This pack uses unchanged screenshots from the local Next.js/FastAPI/PostgreSQL application. The following pages pair full-screen context with enlarged excerpts. No capture is evidence of a genuine classroom pilot.',34,111,W-68)
c.showPage()

for number,(kicker,title,filename,caption,crop) in enumerate(SCREENS,2):
 base(number,kicker,title)
 im=PILImage.open(SHOTS/filename).convert('RGB')
 if crop:
  picture(im,34,137,236,342)
  x1,y1,x2,y2=crop;crop=(x1,min(y1,im.height-1),min(x2,im.width),min(y2,im.height))
  picture(im.crop(crop),294,137,W-328,342)
 else:
  picture(im,34,137,270,342)
  detail=im.crop((0,max(0,im.height-1000),im.width,im.height))
  picture(detail,330,137,220,342)
  para('Full mobile screen and enlarged lower task section.',580,450,220)
  para('Dark theme: near-black surfaces, rose-gold primary actions and restrained accent colors. The design keeps task state and feedback visible.',580,385,220)
 para(caption,34,117,W-68)
 c.setFont('Segoe',7);c.setFillColor(MUTED);c.drawString(34,42,'Source: docs/screenshots/'+filename+'  |  Full screen at left; enlarged excerpt at right.')
 c.showPage()

base(len(SCREENS)+2,'Implementation and evidence','What this demonstration establishes')
sections=[('Implemented','Teacher assessment during AI outages, tab-scoped draft recovery, searchable student rosters; authored diagnosis, distinct probes, learner perspective and agency; interactive support with fresh practice; real 7/30-day scheduling and due-time enforcement; teacher-created lessons/quizzes; audited AI feedback corrections; schema-isolated pilot provisioning.'),
 ('Evidence boundary','All shown accounts are demonstrations or automation fixtures. The scheduled dates show actual persisted future appointments. There are no fabricated elapsed-time outcomes and no completed longitudinal classroom pilot.'),
 ('Next validation','Educator review of content and rules, consented classroom participation, actual delayed observations and measured false interpretations. Template difficulty, learning efficacy and production load remain unvalidated.'),
 ('Review artifacts','Repository README: setup, upgrade/backfill instructions, risk limits and riddle mapping. Companion video: beyond-marks-demo.mp4. Public hosting has not been verified; the supported review path is local setup and downloadable artifacts.')]
y=H-127
for title,body in sections:
 para(title,34,y,180,ParagraphStyle('section',parent=style,fontName='SegoeBold',fontSize=13,leading=18))
 h=para(body,220,y,W-254);y-=max(h,25)+30
c.showPage();c.save()

rows=[]
for kicker,title,filename,caption,crop in SCREENS:
 rows.append(f'<section><p class="eyebrow">{html.escape(kicker)}</p><h2>{html.escape(title)}</h2><p>{html.escape(caption)}</p><a href="../screenshots/{filename}"><img src="../screenshots/{filename}" alt="{html.escape(title)}" loading="lazy"></a><p class="source">Actual app capture: {html.escape(filename)}</p></section>')
html_doc='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Beyond Marks · Frontend Pack</title><style>body{font:16px/1.6 "Segoe UI",Arial,sans-serif;background:#F6F3EB;color:#182B23;margin:0}main{max-width:1100px;margin:auto;padding:48px 24px}h1{font-size:44px;line-height:1.15}h2{font-size:28px}.eyebrow{color:#245C43;font-size:13px;text-transform:uppercase;font-weight:700;letter-spacing:.08em}section{margin:48px 0;padding:28px;background:#FFFEFA;border:1px solid #CAD2C5;border-radius:14px}img{display:block;max-width:100%;max-height:1100px;width:auto;margin:24px auto;border:1px solid #CAD2C5}.source{font-size:13px;color:#526158}a{color:#245C43}@media print{section{break-before:page}img{max-height:75vh}}@media(max-width:600px){main{padding:24px 16px}section{padding:16px}h1{font-size:34px}}</style><main><p class="eyebrow">Beyond Marks · 17 October 2026</p><h1>Understanding comes first</h1><p>A captioned walkthrough of the actual learning workspace. These are demonstration and test accounts, not a longitudinal classroom study. Genuine 7/30-day scheduling is implemented; no delayed learning outcome is claimed.</p><p><a href="frontend-pack.pdf">Download PDF</a> · <a href="beyond-marks-demo.mp4">Project video</a> · <a href="../../README.md">Repository README</a></p>'''+''.join(rows)+'''<section><h2>Evidence and limits</h2><p>Teacher corrections preserve original AI feedback and update recommendations. Learner perspectives remain revisable evidence. Public hosting is not verified; use local setup and downloadable artifacts. A genuine classroom pilot, difficulty calibration and production load study remain future validation work.</p></section></main></html>'''
(OUT/'frontend-pack.html').write_text(html_doc,encoding='utf-8')
md=['# Beyond Marks Frontend Pack','', '[Download the captioned PDF](submission/frontend-pack.pdf) · [Open the HTML gallery](submission/frontend-pack.html) · [Project video](submission/beyond-marks-demo.mp4)','',
 'The pack contains actual screenshots from the local Next.js frontend connected to FastAPI and PostgreSQL. Shown accounts are demonstration or automated-test accounts, not classroom study participants. Full screens accompany enlarged excerpts in the PDF; the original PNGs remain unchanged.','',
 'The 7/30-day screen shows real persisted future dates after a completed recording flow. It does not show completed delayed outcomes. Historical synthetic PASS/FAIL examples are separate from genuine delayed checks.','',
 '| Screen | Actual capture | Caption |','| --- | --- | --- |']
for kicker,title,filename,caption,crop in SCREENS:md.append(f'| {title} | [{filename}](screenshots/{filename}) | {caption} |')
md+=['','Desktop captures use 1440px; representative mobile captures use 390px. Light/dark variants remain in `docs/screenshots`. Screen 22 is the newly captured real scheduling view; screen 23 records an audited teacher correction and resolved student concern.','',
 'Rebuild the PDF and HTML using `.venv/Scripts/python.exe docs/submission/build_frontend_pack.py` with ReportLab and Pillow installed. The generator uses local Segoe UI fonts on Windows. Screenshot capture is performed by the browser suite and the separate recording workflow.','',
 'See the [demo narration](demo-script.md), [judging notes](debate-notes.md) and [verification record](verification.md). Public hosting is not verified.']
(ROOT/'docs'/'frontend-pack.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
(OUT/'frontend-pack-sources.json').write_text(json.dumps([dict(section=k,title=t,screenshot='docs/screenshots/'+f,caption=cap,crop=crop) for k,t,f,cap,crop in SCREENS],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f'Created frontend-pack.pdf ({len(SCREENS)+2} pages), HTML gallery, source manifest and caption index.')
