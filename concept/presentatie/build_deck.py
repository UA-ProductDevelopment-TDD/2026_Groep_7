"""Bouwt de conceptpresentatie (Nederlands) uit de UAntwerpen-template + materials.json.
Gebruik: python build_deck.py <template.pptx> <uit.pptx>
Draai opnieuw na het aanpassen van materials.json (prijzen, links, foto's) of de tekst in CONCEPTS/EXTRA."""
import copy, json, os, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY, STEEL, RED, LT, TINT, WHITE = (RGBColor.from_string(c) for c in
    ("002E65", "82A1AD", "EA2C38", "BBCCCC", "EEF3F5", "FFFFFF"))
DATA = json.load(open(os.path.join(HERE, "materials.json"), encoding="utf-8"))
ICON = lambda n: os.path.join(HERE, "assets", n + ".png")

SHORT = dict(cam="ESP32-S3-camera", tof="VL53L0X ToF-sensor", mag="Magneetkabel USB-C",
             qi="Qi-oplaadset", piezo="Piëzo-buzzer", speaker="Degelijke speaker", mmwave="mmWave-radar")
TEAMS = {"hw": "Wannes, Arno", "el": "Ben, Ward", "ux": "Joren, Jolan"}
TEAM_TITLE = {"hw": "Hardware", "el": "Elektronica", "ux": "UI/UX"}

CONCEPTS = [
 dict(key="coop", icon="icon-coop", short="Kippenhok", name="Kippenhok-waakhond",
  pitch="Een robothond die 's nachts het kippenhok bewaakt en vossen wegjaagt.",
  problem="Vossen vallen 's nachts hokken aan. Een kippenhouder kan niet blijven waken.",
  answer="Bittle loopt een vaste ronde, herkent vos, kip of mens en schakelt over op afschrikmodus.",
  boundary="Bittle schrikt af en waarschuwt. Hij verdedigt niet.",
  target="Kippenhouders en kleine boerderijen met vossen in de buurt.",
  hw=dict(tasks=["Robuuster loopalgoritme voor oneffen grond", "Aangepaste voeten voor grip op gras",
                 "Beschermkap tegen vocht, stof en stro", "Houders voor camera, speaker en leds",
                 "Dockingstation met laadcontacten"],
          challenge="Ruw terrein en weer. Of de Bittle X een vochtig hok overleeft, is niet bevestigd.",
          test="Korte, begeleide wandeling op stro of zand, plus een proefhok in simulatie."),
  el=dict(tasks=["ESP32-S3-camera (eigen 5 V) via I2C/UART aan de BiBoard", "Herkenning op de camera: vos, kip, mens; IR-verlichting 's nachts",
                 "ToF-afstandssensor langs de omheining (XSHUT voor adressen)", "Draadloos laden: Qi-ontvanger en -zender, magneetkabel",
                 "Alarmgeluid (buzzer of cameraspeaker) en leds"],
          challenge="Betrouwbare herkenning 's nachts en de koppeling van de aparte camera met de BiBoard.",
          test="Herkenning testen op opgenomen beelden van een hok, voor we iets bouwen."),
  ux=dict(tasks=["Dashboard: livebeeld, meldingen, patrouillezones", "Afschrikmodus en gevoeligheid instellen",
                 "Melding bij een gedetecteerde vos", "Handmatig ingrijpen en noodstop",
                 "Deskresearch naar de noden van kippenhouders (fora, artikels)"],
          challenge="Welke prikkels (licht, geluid, beweging) schrikken vossen echt af?",
          test="Literatuur over vossen afschrikken; klikbaar prototype van het dashboard."),
  plan=dict(embodiment=["3D-geprinte grijpvoeten en beschermkap", "Patrouilleroute met dreigingsniveaus",
                        "Afschrikgedrag: flitslicht, alarmgeluid, dreigende houding"],
            interface=["Webdashboard met livebeeld", "Pushmeldingen per detectie", "Gevoeligheid en zones instellen"])),
 dict(key="museum", icon="icon-museum", short="Museumgids", name="Museumgids",
  pitch="Een robotgids die een rondleiding op maat van jouw voorkeuren plant.",
  problem="Bezoekers volgen één vaste route of een statische audiogids.",
  answer="De bezoeker kiest thema, duur en taal. Bittle berekent een route en vertelt bij elk kunstwerk een verhaal.",
  boundary="Werkt op vlakke, bewaakte vloeren. Geen trappen, geen drukte.",
  target="Musea en tentoonstellingen; gezinnen en scholen.",
  hw=dict(tasks=["Rustige, stabiele gang op een vlakke vloer", "Houder voor de camera", "Houder voor een luidere speaker",
                 "Dockingstation voor automatisch laden", "Uitstraling die bezoekers aanspreekt"],
          challenge="Een wandelende robot drijft af, dus de positie is niet exact.",
          test="Een afgeplakte route 10 keer lopen en de afwijking meten."),
  el=dict(tasks=["Camera met herkenning van markers en bezoekers", "ToF-sensor om bezoekers en muren te ontwijken",
                 "Positie schatten met IMU en markers", "Speaker met een verhaal per kunstwerk",
                 "Draadloos laden: Qi-ontvanger en -zender, magneetkabel"],
          challenge="Nauwkeurig navigeren met markers en IMU.",
          test="Bereik en hoek van de markerherkenning meten met de ESP32-S3-camera."),
  ux=dict(tasks=["Voorkeurenapp: thema, duur, taal", "Route berekenen uit de voorkeuren",
                 "Verloop: kiezen, route, begeleiden, terug naar het dock", "Inhoud: een verhaal per kunstwerk",
                 "Feedback van medestudenten op het prototype"],
          challenge="Hoe zetten we voorkeuren om in een goede route?",
          test="Papieren prototype van de app, getest met medestudenten."),
  plan=dict(embodiment=["Rustige gang en gebaren die naar kunstwerken wijzen", "Stopt, kijkt en spreekt bij elk kunstwerk",
                        "Keert na de rondleiding terug naar het dock"],
            interface=["Voorkeurenapp in 4 stappen", "Routeoverzicht en voortgang", "Taal en duur instellen"])),
 dict(key="home", icon="icon-home", short="Waakhond thuis", name="Waakhond voor thuis",
  pitch="Een robothond die het huis volgens een vaste route bewaakt en alarm slaat.",
  problem="Mensen willen weten wat er thuis gebeurt als ze weg zijn of slapen.",
  answer="Bittle volgt een vaste route per kamer, herkent mensen en open deuren en slaat alarm.",
  boundary="Bittle detecteert en meldt. Hij confronteert niemand. Beeldherkenning gebeurt lokaal, voor de privacy.",
  target="Gezinnen en alleenwonenden, ook tijdens reizen.",
  hw=dict(tasks=["Compacte sensorhouder voor camera en radar", "Gang over drempels, tapijt en gladde vloeren",
                 "Dockingstation en alarmbehuizing", "Trappen onderzoeken: klimmen of vermijden?"],
          challenge="Drempels, tapijt, routes en trappen.",
          test="Bittle over een drempel en een tapijt laten lopen en de fouten noteren."),
  el=dict(tasks=["Camera die mensen en open deuren herkent", "mmWave-radar (LD2410C, UART) voor beweging achter dunne wanden",
                 "Alarm: sirene (buzzer) en led", "Draadloos laden: Qi-ontvanger en -zender, magneetkabel",
                 "ToF-sensor om obstakels te ontwijken"],
          challenge="De radar ziet beweging achter dunne wanden maar geeft geen beeld. Het bereik door wanden is enkel van de leverancier gekend.",
          test="Een mmWave-module testen achter een gipsplaat."),
  ux=dict(tasks=["Route per kamer instellen", "Modus thuis/weg", "Alarmmelding met snapshot",
                 "Privacy: lokale verwerking, duidelijke indicatoren", "Handmatige besturing en stop"],
          challenge="Privacy en vertrouwen: mensen moeten de controle houden.",
          test="Deskresearch naar privacyregels; klikbaar prototype getest met medestudenten."),
  plan=dict(embodiment=["Compacte sensorkop op de rug", "Vaste patrouilleroute met stops per kamer",
                        "Alarmgedrag: sirene, led, houding"],
            interface=["Routeeditor per kamer", "Schakelaar thuis/weg", "Alarmmeldingen met snapshot"])),
]

EXTRA = {
 "coop": dict(
  story="Valavond: de kippen zijn binnen en Bittle verlaat zijn dock voor een patrouilleronde. Om 02.10 u ziet de camera een vos aan de omheining: leds flitsen, een alarm klinkt en Bittle neemt een dreigende houding aan. De houder krijgt een snapshot en Bittle keert terug naar het dock.",
  opts=["Eieren in de nesten tellen", "Kippen tellen bij het sluiten van het hok", "De hokdeur laten sluiten",
        "Het hok in kaart brengen tijdens de eerste ronde"],
  rq=dict(hw=["Hoeveel gewicht kan een kap toevoegen voor de gang onstabiel wordt?", "Welk voetmateriaal grijpt op nat gras?"],
          el=["Werkt de IR-verlichting van de camera 's nachts buiten?", "Hoe lang kan Bittle patrouilleren op één lading?"],
          ux=["Waarvoor willen kippenhouders gewekt worden?", "Hoe reageren kippen op een bewegende robot?"])),
 "museum": dict(
  story="Een gezin komt binnen en kiest in de app een thema, 45 minuten en Nederlands. Bittle stapt naar het eerste kunstwerk, draait ernaartoe en vertelt het verhaal. Daarna leidt hij verder, ontwijkt bezoekers en keert aan het einde terug naar het dock.",
  opts=["Kindermodus met quiz of speurtocht", "Rondleidingen in meerdere talen", "Korte, middellange en lange routes",
        "Statistieken voor de conservator"],
  rq=dict(hw=["Hoe stabiel is de gang op gepolijste vloeren?", "Waar kan de speaker zitten zonder de poten te hinderen?"],
          el=["Op welke afstand en hoek worden markers herkend?", "Hoe luid moet de speaker zijn in een stille zaal?"],
          ux=["Hoe willen bezoekers door een robot aangesproken worden?", "Welke opties tellen het meest (thema, duur, taal, toegankelijkheid)?"])),
 "home": dict(
  story="Een bewoner vertrekt voor het weekend en zet de wegmodus aan. Bittle patrouilleert door hal, living en keuken. In de hal ziet de camera een open deur en meet de radar beweging: er gaat een melding met snapshot naar de gsm.",
  opts=["Deuren en ramen controleren tijdens elke ronde", "Huisdierfilter tegen valse alarmen",
        "Schema: 's nachts patrouilleren, overdag rusten", "Escalatie: eerst een melding, dan de sirene"],
  rq=dict(hw=["Welke drempelhoogte haalt Bittle?", "Kan Bittle na een val op tapijt weer opstaan?"],
          el=["Hoe ver ziet de radar door gipsplaat, en welke zones vermijden de buurkamer?", "Hoe vermijden we valse alarmen door huisdieren?"],
          ux=["Welke privacywaarborgen hebben bewoners nodig?", "Hoe loopt een alarm op in niveaus?"])),
}

prs = Presentation(sys.argv[1])
LAY = {l.name: l for l in prs.slide_layouts}["UAntwerpen_onlytext"]
numsp = next(sh for sh in prs.slides[1].shapes if sh.name.startswith("Slide Number"))._element


def num(v):
    return (f"{v:g}" if v == int(v) else f"{v:.2f}").replace(".", ",")


def eur(lo, hi, it=None):
    if lo is None:
        return "UA*" if it is None or it.get("supplier") == "UA" else "nog uit te zoeken"
    return f"€ {num(lo)}" if lo == hi else f"€ {num(lo)}–{num(hi)}"


def total(keys):
    its = [DATA["items"][k] for k in keys]
    lo = round(sum(i["price_min"] or 0 for i in its), 2)
    hi = round(sum(i["price_max"] or 0 for i in its), 2)
    ua = any(i["price_min"] is None and i.get("supplier") == "UA" for i in its)
    tbd = [i for i in its if i["price_min"] is None and i.get("supplier") != "UA"]
    return lo, hi, ua, tbd


def total_str(keys):
    lo, hi, ua, tbd = total(keys)
    return eur(lo, hi) + (" + UA-onderdelen" if ua else "") + (" + nog te prijzen onderdeel" if tbd else "")


def paras(tf, items, size=16, color=NAVY, bullet=False, after=6, bold=False, align=None):
    """items: lijst van str of (str, dict(size,color,bold,bullet,after))"""
    first = True
    for it in items:
        txt, o = (it, {}) if isinstance(it, str) else it
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        r = p.add_run(); r.text = txt
        f = r.font
        f.size = Pt(o.get("size", size)); f.bold = o.get("bold", bold)
        f.color.rgb = o.get("color", color)
        p.space_after = Pt(o.get("after", after))
        p.alignment = align or PP_ALIGN.LEFT
        if o.get("bullet", bullet):
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", "228600"); pPr.set("indent", "-228600")
            bc = etree.SubElement(pPr, qn("a:buClr")); etree.SubElement(bc, qn("a:srgbClr")).set("val", "82A1AD")
            etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
            etree.SubElement(pPr, qn("a:buChar")).set("char", "•")


def box(s, x, y, w, h, fill=None, items=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=None, anchor=MSO_ANCHOR.TOP,
        pad=0.2, name=None, **kw):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: sh.adjustments[0] = 0.05
    sh.shadow.inherit = False
    if fill is None: sh.fill.background()
    else: sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line: sh.line.color.rgb = line; sh.line.width = Pt(1.5); sh.line.dash_style = 4
    else: sh.line.fill.background()
    tf = sh.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(pad); tf.margin_top = tf.margin_bottom = Inches(pad * 0.8)
    if items: paras(tf, items, **kw)
    if name: sh.name = name
    return sh


def new_slide(title):
    s = prs.slides.add_slide(LAY)
    s.shapes.title.text = title
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx == 11: ph._element.getparent().remove(ph._element)
    s.shapes._spTree.append(copy.deepcopy(numsp))
    return s


def icon_circle(s, x, y, d, icon):
    box(s, x, y, d, d, NAVY, shape=MSO_SHAPE.OVAL)
    pad = d * 0.22
    s.shapes.add_picture(ICON(icon), Inches(x + pad), Inches(y + pad), Inches(d - 2 * pad), Inches(d - 2 * pad))


# ---------- template-slides: titel + rollen ----------
def set_runs(par, texts):
    runs = par.runs
    while len(runs) < len(texts):
        par.runs[-1]._r.addnext(copy.deepcopy(par.runs[-1]._r)); runs = par.runs
    for r, t in zip(runs, texts): r.text = t
    for r in runs[len(texts):]: r._r.getparent().remove(r._r)


def fill_roles(slide, roles):
    body = next(sh for sh in slide.placeholders if sh.placeholder_format.idx == 11)
    ps = body.text_frame.paragraphs
    for i, (role, name, desc) in enumerate(roles):
        set_runs(ps[2 * i], [role, ": ", name]); ps[2 * i].runs[2].font.italic = True
        ps[2 * i].runs[1].font.bold = ps[2 * i].runs[2].font.bold = False
        set_runs(ps[2 * i + 1], [desc])


t = prs.slides[0]
set_runs(t.shapes.title.text_frame.paragraphs[0], ["Bittle X upgraden"])
sub = [p for p in t.placeholders if p.placeholder_format.idx != 0][0]
set_runs(sub.text_frame.paragraphs[0], ["Technology Driven Design (M2) · Groep 7"])
set_runs(prs.slides[1].shapes.title.text_frame.paragraphs[0], ["Team & rollen (1/2)"])
set_runs(prs.slides[2].shapes.title.text_frame.paragraphs[0], ["Team & rollen (2/2)"])
fill_roles(prs.slides[1], [
 ("Project Manager", "Wannes", "Procescoördinatie, planning, communicatie met de docenten"),
 ("Simulatie/Test Manager", "Joren", "Digital twins: concepten en animaties veilig testen"),
 ("GitHub Manager", "Jolan", "Zet GitHub op en coördineert de documentatie van de subteams"),
 ("Robot (Bittle) Manager", "Arno", "Zorgt voor de robot: uitlenen, controle, kalibratie, opslag, transport"),
 ("Presentatie Manager", "Ben", "Tussentijdse en finale presentaties"),
])
fill_roles(prs.slides[2], [
 ("Hardware Manager", "nog te bepalen", "Verantwoordelijk voor de taken van het HW-subteam"),
 ("Elektronica Manager", "nog te bepalen", "Verantwoordelijk voor de taken van het EL-subteam"),
 ("UI/UX Manager", "nog te bepalen", "Verantwoordelijk voor de taken van het UI/UX-subteam"),
 ("Module Manager", "Ward", "Uitlenen, bestellen en beheren van extra modules (sensoren/actuatoren)"),
 ("Movie Manager", "Ben", "Regie van het filmpje"),
])

# ---------- overzicht ----------
s = new_slide("Drie concepten in één blik")
for i, c in enumerate(CONCEPTS):
    x = 0.68 + i * 4.08
    box(s, x, 1.66, 3.81, 5.1, TINT)
    icon_circle(s, x + 0.25, 1.9, 1.0, c["icon"])
    box(s, x + 0.2, 3.05, 3.4, 0.5, None, [(c["name"], dict(size=20, bold=True))], pad=0.05)
    box(s, x + 0.2, 3.6, 3.4, 1.3, None, [c["pitch"]], size=16, pad=0.05)
    box(s, x + 0.2, 5.1, 3.4, 1.6, None,
        [("Onderdelen: " + total_str(DATA["concepts"][c["key"]]), dict(size=15, bold=True)),
         ("Grootste risico: " + c["hw"]["challenge"].split(".")[0] + ".", dict(size=14))], pad=0.05)

# ---------- per concept ----------
H = dict(size=12, bold=True, color=STEEL, after=6)
for c in CONCEPTS:
    ex = EXTRA[c["key"]]
    s = new_slide(f"{c['name']}: concept")
    icon_circle(s, 0.68, 1.75, 1.2, c["icon"])
    box(s, 2.15, 1.75, 9.0, 1.2, None, [c["pitch"]], size=22, bold=True, pad=0.05, anchor=MSO_ANCHOR.MIDDLE)
    box(s, 0.68, 3.25, 4.15, 3.55, None,
        [("IN HET KORT", H)]
        + [(f"{l}: {t}", dict(bullet=True)) for l, t in (("Probleem", c["problem"]), ("Antwoord", c["answer"]),
                                                          ("Doelgroep", c["target"]), ("Grens", c["boundary"]))],
        size=15, after=8, pad=0.05)
    box(s, 5.05, 3.25, 3.1, 3.55, None,
        [("OPTIES DIE WE ONDERZOEKEN", H)] + [(o, dict(bullet=True)) for o in ex["opts"]],
        size=15, after=8, pad=0.05)
    box(s, 8.45, 3.25, 4.2, 3.55, None,
        [("Moodboard / collage", dict(size=20, bold=True, color=STEEL)),
         ("(foto's volgen van het team)", dict(size=14, color=STEEL))],
        line=STEEL, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, name="Moodboard placeholder")
    s.notes_slide.notes_text_frame.text = "Verhaal: " + ex["story"]

    for tk in ("hw", "el", "ux"):
        d = c[tk]
        s = new_slide(f"{c['short']}: team {TEAM_TITLE[tk]}")
        box(s, 0.68, 1.66, 7.4, 0.5, None, [(f"Team {TEAM_TITLE[tk]}: {TEAMS[tk]}", dict(size=16, bold=True))], pad=0.0)
        box(s, 0.68, 2.3, 7.4, 4.5, TINT,
            [("TAKEN", dict(size=12, bold=True, color=STEEL, after=6))] + [(x, dict(bullet=True)) for x in d["tasks"]]
            + [("ONZE ONDERZOEKSVRAGEN", dict(size=12, bold=True, color=STEEL, after=6))]
            + [(x, dict(bullet=True, size=15)) for x in ex["rq"][tk]],
            size=16, after=7)
        box(s, 8.4, 2.3, 4.25, 4.5, NAVY,
            [("GROOTSTE UITDAGING", dict(size=12, bold=True, color=LT, after=6)), (d["challenge"], dict(size=18, after=22)),
             ("EERSTE TEST", dict(size=12, bold=True, color=LT, after=6)), (d["test"], dict(size=16))],
            color=WHITE)

    s = new_slide(f"{c['short']}: plan van aanpak")
    keys = DATA["concepts"][c["key"]]
    cols = [("Fysieke vormgeving / gedrag", c["plan"]["embodiment"]),
            ("Interface / bediening", c["plan"]["interface"]),
            ("Materiaal", [SHORT.get(k, k) for k in keys] + ["3D-printen / lasersnijden"])]
    for j, (h, its) in enumerate(cols):
        x = 0.68 + j * 4.06
        box(s, x, 1.66, 3.85, 0.7, NAVY, [(h, dict(size=16, bold=True))], color=WHITE, anchor=MSO_ANCHOR.MIDDLE, pad=0.15)
        box(s, x, 2.45, 3.85, 3.55, TINT, [(i, dict(bullet=True)) for i in its], size=18, after=12)
    box(s, 0.68, 6.15, 11.97, 0.6, None,
        [("Geschat budget onderdelen: " + total_str(keys) + "  (excl. 3D-printen en lasersnijden)", dict(size=16, bold=True))],
        pad=0.05, anchor=MSO_ANCHOR.MIDDLE)

    s = new_slide(f"{c['short']}: materiaal en budget")
    its = [DATA["items"][k] for k in keys]
    heads = ["Onderdeel", "Doel", "Geschatte prijs", "Link"]
    widths = [4.3, 4.1, 1.8, 1.77]
    nrow = len(its) + 2
    top, hrow, rh = 1.66, 0.45, (0.68 if nrow <= 7 else 0.58)
    gt = s.shapes.add_table(nrow, len(heads), Inches(0.68), Inches(top), Inches(sum(widths)),
                            Inches(hrow + rh * (nrow - 1)))
    tbl = gt.table
    for j, w in enumerate(widths): tbl.columns[j].width = Inches(w)
    tbl.rows[0].height = Inches(hrow)
    for r in range(1, nrow): tbl.rows[r].height = Inches(rh)

    def cell(r, j, text, bold=False, color=NAVY, fill=WHITE, url=None, size=13):
        ce = tbl.cell(r, j); ce.fill.solid(); ce.fill.fore_color.rgb = fill
        ce.vertical_anchor = MSO_ANCHOR.MIDDLE
        ce.margin_left = ce.margin_right = Inches(0.1)
        p = ce.text_frame.paragraphs[0]; ru = p.add_run(); ru.text = text
        ru.font.size = Pt(size); ru.font.bold = bold; ru.font.color.rgb = color
        if url: ru.hyperlink.address = url

    for j, h in enumerate(heads): cell(0, j, h, True, WHITE, NAVY)
    for r, it in enumerate(its, 1):
        row = [it["name"], it["purpose"], eur(it["price_min"], it["price_max"], it), "Link" if it["url"] else "nog toe te voegen"]
        for j, v in enumerate(row):
            cell(r, j, v, fill=TINT if r % 2 == 0 else WHITE, url=it["url"] if (it["url"] and j == 3) else None)
    last = nrow - 1
    for j in range(len(heads)): cell(last, j, "", fill=LT)
    cell(last, 0, "Totaal (schatting)", True, fill=LT)
    cell(last, 2, total_str(keys), True, fill=LT)
    box(s, 0.68, 6.5, 11.97, 0.4, None,
        [("* UA = beschikbaar via de Universiteit Antwerpen. Prijzen met een link: onderzocht op 25 okt 2026, incl. btw. "
          "Andere prijzen: schatting van het team.", dict(size=12, color=STEEL))], pad=0.0)

# ---------- afsluiter ----------
s = new_slide("Open punten en volgende stappen")
cols = [("Beslissen", ["Eén concept kiezen (criteria: innovatie, verkoopbaarheid, haalbaarheid)", "Radarmodel en dockingsysteem kiezen (open)"]),
        ("Toetsen", ["Waterbestendigheid toetsen aan de veiligheidsregels voor de robot", "IR-bereik van de camera en bereik van de radar door wanden testen"]),
        ("Voorbereiden", ["Onderdelen bestellen na de conceptkeuze", "Digital twin opzetten voor de gekozen route"])]
for j, (h, its) in enumerate(cols):
    x = 0.68 + j * 4.06
    box(s, x, 1.66, 3.85, 0.7, NAVY, [(h, dict(size=18, bold=True))], color=WHITE, anchor=MSO_ANCHOR.MIDDLE, pad=0.15)
    box(s, x, 2.45, 3.85, 3.6, TINT, [(i, dict(bullet=True)) for i in its], size=18, after=14)

# originele template-slides 4-9 weg; volgorde: titel, rollen, nieuwe slides
ids = prs.slides._sldIdLst
for sid in list(ids)[3:9]:
    prs.part.drop_rel(sid.rId); ids.remove(sid)
prs.save(sys.argv[2])
print("opgeslagen", sys.argv[2], len(prs.slides), "slides")
