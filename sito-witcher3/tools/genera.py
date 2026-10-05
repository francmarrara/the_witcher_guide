#!/usr/bin/env python3
"""Rigenera l'intero sito dalla guida italiana. Uso: python3 tools/genera.py"""
import re, html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "witcher3-wild-hunt-100-achievement-guide.it.md"
text = SRC.read_text(encoding="utf-8")

def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r'\[([^\]]+)\]\((https?[^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'(?<!\w)_([^_\n]+)_(?!\w)', r'<em>\1</em>', s)
    return s

def cls_of(line: str) -> str:
    l = line.lower()
    if "obiettivo" in l: return "card-obiettivo"
    if "missione" in l: return "card-missione"
    if "carta gwent" in l or "carta unica" in l or "gwent" in l: return "card-gwent"
    if "contratto" in l: return "card-contratto"
    return ""

def badge_of(line: str) -> str:
    ls = line.lower()
    if line.startswith("**Obiettivo"): return "<span class='badge b-ob'>Obiettivo</span>"
    if line.startswith("**Missione"): return "<span class='badge b-miss'>Missione</span>"
    if "carta gwent" in ls or "carta unica" in ls or "gwent" in ls: return "<span class='badge b-gwent'>Gwent</span>"
    if "contratto" in ls: return "<span class='badge b-contr'>Contratto</span>"
    return ""

def md_to_html(raw: str) -> str:
    out = []
    for rawline in raw.splitlines():
        line = rawline.strip()
        if not line: continue
        if re.match(r'^\\?-{3,}\\?$', line) or (set(line.replace("\\","").replace(" ","")) <= {"-"} and len(line) >= 5):
            out.append("<hr class='sep'/>"); continue
        if line.startswith(">"):
            out.append(f"<blockquote>{inline(line.lstrip('> ').strip())}</blockquote>"); continue
        if re.match(r'^\*\*\\?\d+\\?\.?.*\*\*$', line):
            out.append(f"<p class='meta'>{inline(line.strip('*').strip())}</p>"); continue
        cls, bd, h = cls_of(line), badge_of(line), inline(line)
        if cls: out.append(f"<div class='card {cls}'>{bd}<p>{h}</p></div>")
        elif line.startswith("**") and len(line) < 90: out.append(f"<h4 class='luogo'>{h}</h4>")
        else: out.append(f"<p>{h}</p>")
    return "\n".join(out)

parts = re.split(r'(?m)^(Sequenza\s+\d+\s*:.*)$', text)
intro_raw = parts[0].strip()
sections = []
for i in range(1, len(parts), 2):
    title = parts[i].strip(); body = parts[i+1].strip() if i+1 < len(parts) else ""
    m = re.match(r'Sequenza\s+(\d+)\s*:\s*(.*)', title)
    num, name = (int(m.group(1)), m.group(2).strip()) if m else (i, title)
    metas = re.findall(r'\*\*\\?(\d+)\\?\.\s*([^*]+)\*\*', body[:1500])
    sections.append({"num": num, "title": name, "html": md_to_html(body),
                     "meta": [x[1].strip() for x in metas[:6]]})
intro_html = md_to_html(intro_raw)
seq_of_pos = []
for s in sections: seq_of_pos.append((len("\n".join([sections[j]["html"] for j in range(len(sections))])), s["num"]))
# mappa posizione->sequenza tramite offset nel testo
offsets, pos = [], 0
acc = len(intro_raw)
for s in sections:
    offsets.append((acc, s["num"]))
    # lunghezza raw approssimata: la ricaviamo dal testo originale
def seq_at(idx: int) -> int:
    n = sections[0]["num"]
    for off, sn in offsets:
        if idx >= off: n = sn
    return n
# ricalcola offsets reali
offsets, cursor = [], len(intro_raw)
for i in range(1, len(parts), 2):
    offsets.append((cursor + len(parts[i]), int(re.match(r'Sequenza\s+(\d+)', parts[i]).group(1))))
    cursor += len(parts[i]) + (len(parts[i+1]) if i+1 < len(parts) else 0)

def unique_hits(pattern):
    seen, out = {}, []
    for m in re.finditer(pattern, text):
        try: g1 = m.group(1)
        except IndexError: g1 = None
        try: g2 = m.group(2)
        except IndexError: g2 = None
        num = int(g1) if g1 and g1.isdigit() else None
        nome = (g2 if g2 is not None else (g1 or "")).strip().rstrip(":").strip()
        key = (num, nome.lower())
        ctx = text[m.end():m.end()+320].replace("\n", " ").strip()
        ctx = re.sub(r'\s+', ' ', ctx)
        if len(ctx) > 300: ctx = ctx[:300].rsplit(" ", 1)[0] + "…"
        if key not in seen:
            seen[key] = {"num": num, "nome": nome, "desc": ctx, "seq": seq_at(m.start()), "n": 1}
        else:
            seen[key]["n"] += 1
            if seq_at(m.start()) not in seen[key].get("seqs", [seen[key]["seq"]]):
                seen[key].setdefault("seqs", [seen[key]["seq"]]).append(seq_at(m.start()))
    return list(seen.values())

contratti = unique_hits(r'\*\*Contratto da Witcher\s*[#n.]?\s*(\d+)?\s*[–\-—:]?\s*([^*]{2,80}?)\s*:?\s*\*\*')
carte = unique_hits(r'\*\*Carta (?:Gwent )?unica\s*[n#.]?\s*°?\s*(\d+)?\s*[–\-—:]?\s*([^*]{2,90}?)\s*\*\*')
missioni = unique_hits(r'\*\*Missione principale\s*[#n.]?\s*(\d+)?\s*[–\-—:]?\s*([^*]{2,80}?)\s*:?\s*\*\*')
ciri = unique_hits(r'\*\*Missione [Dd]i Ciri\s*[#n.]?\s*(\d+)?\s*[–\-—:]?\s*([^*]{2,80}?)\s*:?\s*\*\*')
bw = unique_hits(r'\*\*Missione B&W\s*[#n.]?\s*(\d+)?\s*[–\-—:]?\s*([^*]{2,80}?)\s*:?\s*\*\*')
dlcq = unique_hits(r'\*\*Missione DLC\s*[–\-—:]?\s*([^*]{2,80}?)\s*:?\s*\*\*')
# secondarie uniche per nome
sec_seen, secondarie = {}, []
for m in re.finditer(r'\*\*Missione secondaria\s*[–\-—:]\s*([^*]{2,80}?)\s*:?\s*\*\*', text):
    nome = m.group(1).strip().rstrip(":")
    if nome.lower() not in sec_seen:
        sec_seen[nome.lower()] = {"nome": nome, "seq": seq_at(m.start()), "n": 1}
    else: sec_seen[nome.lower()]["n"] += 1
secondarie = list(sec_seen.values())
# missabili: blocchi che contengono la parola
missabili = []
for blk in re.split(r'\n\s*\n', text):
    if re.search(r'Mancabil|Missable|missable', blk):
        b = re.sub(r'\s+', ' ', blk).strip()
        if len(b) > 40: missabili.append(b[:420] + ("…" if len(b) > 420 else ""))
# dedup missabili simili
uniq_miss = []
for b in missabili:
    if not any(b[:80] in u or u[:80] in b for u in uniq_miss): uniq_miss.append(b)
# obiettivi
obiettivi, seen_ob = [], {}
for m in re.finditer(r'\*\*Obiettivo\s*(?:n\.|#)?\s*(\d+)\s*[–\-—:]?\s*([^*]+?)\s*:\s*\*\*', text):
    num, nome = int(m.group(1)), m.group(2).strip().rstrip(":")
    ctx = re.sub(r'\s+', ' ', text[m.end():m.end()+220].replace("\n", " ")).strip()
    seen_ob[num] = {"num": num, "nome": nome, "desc": ctx[:220]}
obiettivi = [seen_ob[k] for k in sorted(seen_ob)]

def fonte_carta(c):
    s = (c["nome"] + " " + c["desc"]).lower()
    if "mazzo base" in s or "starter" in s: return "base"
    if "acquist" in s or "purchase" in s or "compra" in s or "corone" in s or "crowns" in s: return "acquisto"
    if "torneo" in s or "high stakes" in s or "sasha" in s or "tybalt" in s: return "torneo"
    if "complet" in s or "ricompensa" in s or "guadagn" in s: return "missione"
    return "vittoria"

for c in carte: c["fonte"] = fonte_carta(c)

print(f"sezioni={len(sections)} contratti={len(contratti)} carte={len(carte)} missioni={len(missioni)} ciri={len(ciri)} bw={len(bw)} dlc={len(dlcq)} secondarie={len(secondarie)} missabili={len(uniq_miss)} obiettivi={len(obiettivi)}")

NAV = [("index.html","Guida"),("obiettivi.html","Obiettivi"),("build.html","Build Death March"),("contratti.html","Contratti"),("carte.html","Carte Gwent"),("gwent.html","Strategia Gwent"),("missioni.html","Missioni"),("dlc-finali.html","DLC & Finali")]
def top(active):
    links = "".join(f'<a href="{h}" class="{"active" if h==active else ""}">{l}</a>' for h, l in NAV)
    return f"""<header class="topbar"><div class="topbar-in">
<a class="brand" href="index.html"><span class="brand-mark">🐺</span><span><b>The Witcher 3 — Guida 100%</b><small>Wild Hunt · in italiano</small></span></a>
<nav class="main">{links}</nav></div></header>"""
FOOT = """<footer><div class="wrap">
<p><b style="color:var(--cream)">The Witcher 3: Wild Hunt — Guida completa in italiano al 100% degli obiettivi.</b><br>
Contenuti della walkthrough tradotti e adattati dalla guida di <b>Cynic 0055</b> (Cynical Guides) — fonte originale su Steam: <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=3162226469" target="_blank" rel="noopener">steamcommunity.com/sharedfiles/?id=3162226469</a>. Checklist obiettivi: <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=3162875051" target="_blank" rel="noopener">Achievement Checklist</a>.</p>
<p>The Witcher è un marchio di CD PROJEKT RED. Sito non ufficiale creato per uso personale, senza immagini coperte da copyright.</p>
</div></footer><button id="backtop" class="backtop" title="Torna su">↑</button><script src="assets/app.js"></script>"""
HEAD = lambda t, d: f"""<!DOCTYPE html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}</title><meta name="description" content="{d}"><link rel="stylesheet" href="assets/styles.css"></head><body>"""

# ---------- INDEX ----------
toc = "\n".join(f'<li><a href="#seq-{s["num"]}"><span class="n">{s["num"]:02d}</span> {html.escape(s["title"])}</a></li>' for s in sections)
idx_cards = "\n".join(f'<li style="margin:6px 0"><a href="#seq-{s["num"]}"><b style="color:var(--gold)">Sequenza {s["num"]}</b> — {html.escape(s["title"])}</a></li>' for s in sections)
reader = "\n".join(f"""<article class="section" id="seq-{s["num"]}" data-title="Sequenza {s["num"]} {html.escape(s["title"])}">
<p class="kicker">Sequenza {s["num"]}</p><h2><span class="seq">🐺</span> {html.escape(s["title"])}</h2>
{s["html"]}
<div class="sec-foot"><label class="mark"><input type="checkbox" class="seq-check" data-sec="seq-{s["num"]}"> Segna come completata</label>
<a href="#top">↑ Torna all'indice</a></div></article>""" for s in sections)
(ROOT/"index.html").write_text(HEAD("The Witcher 3: Wild Hunt — Guida completa 100% in italiano","Guida completa in italiano a The Witcher 3: walkthrough 100%, Death March, Gwent, contratti, DLC Hearts of Stone e Blood and Wine.")+f"""{top('index.html')}<div class="wrap" id="top">
<section class="hero"><p class="kicker">Guida completa · {len(sections)} capitoli · {len(obiettivi)} obiettivi · 2 DLC</p>
<h1>The Witcher 3: <span>Wild Hunt</span><br>Guida al 100% in italiano</h1>
<p>Walkthrough passo-passo da Kaer Morhen a Toussaint: missioni principali, {len(contratti)} contratti da witcher, 169 carte Gwent, risse, corse, missioni <em>missabili</em>, difficoltà <b>Death March (Marcia della Morte)</b> e tutti i finali. Tradotta e riorganizzata per la lettura sul web.</p>
<div class="cta"><a class="btn" href="#leggi">📖 Inizia la guida</a><a class="btn ghost" href="obiettivi.html">🏆 Checklist obiettivi</a><a class="btn ghost" href="carte.html">🃏 Tutte le carte Gwent</a></div>
<div class="stats">
<div class="stat"><b>{len(sections)}</b><span>sequenze walkthrough</span></div>
<div class="stat"><b>{len(obiettivi)}</b><span>obiettivi (base+DLC)</span></div>
<div class="stat"><b>{len(carte)}</b><span>carte Gwent citate</span></div>
<div class="stat"><b>{len(contratti)}</b><span>contratti citati</span></div>
<div class="stat"><b>140–180</b><span>ore stimate</span></div>
</div></section>
<div class="layout">
<aside class="sidebar"><h3>🔎 Cerca nella guida</h3><input id="q" class="search" placeholder="Cerca: es. Barone, Gwent, Death March…">
<h3>Progresso lettura</h3><div class="progress-line"><i id="seq-bar"></i></div><p id="seq-label" style="font-size:13px;color:var(--muted);margin:0 6px 10px"></p>
<h3>Indice sequenze</h3><ol class="toc" style="list-style:none;padding:0">{toc}</ol>
<h3>Pagine della guida</h3><ol class="toc" style="list-style:none;padding:0">{"".join(f'<li><a href="{h}">📄 {l}</a></li>' for h,l in NAV[1:])}</ol></aside>
<main class="content" id="leggi">
<div class="intro-box"><p class="kicker">Prima di giocare</p><h2 style="margin:0 0 8px;color:var(--cream)">Introduzione e regole del 100%</h2>{intro_html}</div>
<div class="intro-box"><p class="kicker">Indice</p><h2 style="margin:0 0 8px;color:var(--cream)">Tutte le sequenze</h2><ol id="index-list">{idx_cards}</ol>
<div class="warn"><b>⚠️ Attenzione spoiler:</b> la guida racconta l'intera trama, i finali e le scelte missabili. Usala seguendo l'ordine delle sequenze, una sola partita a <b>Marcia della Morte</b> senza mai abbassare la difficoltà.</div></div>
{reader}
<div class="intro-box"><h2 style="color:var(--cream)">Fonte</h2><p>Testi della walkthrough: <b>Cynic 0055 — Cynical Guides</b>, <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=3162226469" target="_blank" rel="noopener">guida originale su Steam</a> (tradotta in italiano). Se la guida ti aiuta, lascia una valutazione all'autore originale.</p></div>
</main></div></div>{FOOT}</body></html>""", encoding="utf-8")

# ---------- OBIETTIVI ----------
def tipo_ob(nome):
    n = nome.lower()
    if any(k in n for k in ["gwent","card","all in","killed it","problem"]): return "gwent"
    if any(k in n for k in ["slayer","butcher","can't touch","even odds","bombardier","fire in","triple","pest","moo","dendrolog","mutant","rad steez","environmentally","overkill","marksman","humpty","enemy of my","quit anytime","return to sender","hasta la","fiend","vampire","ashes"]): return "combattimento"
    if any(k in n for k in ["lilac","walked the path","passed the trial","ran the gauntlet","ugly baby","something more","xenonaut","king of the dead","witcher's gone south","pacta","sommelier","knight to remember","last action","kling of"]): return "storia"
    return "secondari"
rows = "\n".join(f"""<div class="ob-row" data-tipo="{tipo_ob(o['nome'])}"><input type="checkbox" class="ob-check" data-ob="{o['num']}"><span class="num">{o['num']}</span>
<div><div class="oname">{html.escape(o['nome'])}</div><div class="odesc">{html.escape(o['desc'])}</div></div></div>""" for o in obiettivi)
(ROOT/"obiettivi.html").write_text(HEAD("Checklist 78 obiettivi — The Witcher 3 Guida 100%","Tutti i 78 obiettivi di TW3 con checklist interattiva.")+f"""{top('obiettivi.html')}<div class="wrap">
<section class="hero"><p class="kicker">Checklist interattiva · salvataggio automatico</p><h1>🏆 Tutti i <span>{len(obiettivi)} obiettivi</span></h1>
<p>Spunta gli obiettivi ottenuti: il progresso resta salvato in questo browser. Una sola partita a <b>Marcia della Morte</b> + DLC Hearts of Stone e Blood &amp; Wine.</p>
<div class="progress-line" style="max-width:520px"><i id="ob-bar"></i></div><p id="ob-label" style="color:var(--muted)"></p>
<div class="toolbar"><input id="q" class="search" style="max-width:340px;margin:0" placeholder="Filtra obiettivi…">
<select id="f-tipo"><option value="">Tutte le categorie</option><option value="storia">Storia</option><option value="secondari">Secondari / esplorazione</option><option value="combattimento">Combattimento</option><option value="gwent">Gwent</option></select>
<button class="btn ghost" id="btn-all">Seleziona tutti</button><button class="btn ghost" id="btn-none">Azzera</button></div></section>
<main class="content">{rows}
<div class="warn"><b>Missabili critici:</b> vedi la pagina <a href="dlc-finali.html#missabili">DLC &amp; Finali → punti missabili</a>: carte del torneo <b>High Stakes</b>, carte della festa Vegelbud, Keira Metz, alleati di Kaer Morhen, doppi salvataggi in Blood &amp; Wine.</div>
</main></div>{FOOT}</body></html>""", encoding="utf-8")

# ---------- CONTRATTI ----------
c_rows = "\n".join(f"""<div class="ob-row"><input type="checkbox" class="ob-check" data-ob="c-{i}"><span class="num">{c['num'] if c['num'] else '•'}</span>
<div><div class="oname">{html.escape(c['nome'] or 'Contratto')} <span style="color:var(--muted);font-weight:normal">· citato {c['n']}× · seq. {c['seq']}</span></div>
<div class="odesc">{html.escape(c['desc'])}</div><div style="margin-top:6px"><a href="index.html#seq-{c['seq']}">→ Vai alla Sequenza {c['seq']}</a></div></div></div>""" for i, c in enumerate(sorted(contratti, key=lambda x: (x['num'] or 999, x['nome']))))
(ROOT/"contratti.html").write_text(HEAD(f"Contratti da witcher ({len(contratti)} citati) — Guida TW3","Tutti i contratti da witcher citati nella guida con checklist.")+f"""{top('contratti.html')}<div class="wrap">
<section class="hero"><p class="kicker">Obiettivo Geralt: The Professional · 26 contratti</p><h1>⚔️ Contratti da <span>witcher</span></h1>
<p>Tutti i contratti citati nella walkthrough, in ordine di comparsa nella guida. Per l'obiettivo <b>Geralt: The Professional</b> servono 26 contratti completati. Spunta quelli chiusi: il progresso resta salvato nel browser.</p>
<div class="progress-line" style="max-width:520px"><i id="ob-bar"></i></div><p id="ob-label" style="color:var(--muted)"></p>
<div class="toolbar"><input id="q" class="search" style="max-width:340px;margin:0" placeholder="Filtra contratti…"><button class="btn ghost" id="btn-all">Seleziona tutti</button><button class="btn ghost" id="btn-none">Azzera</button></div></section>
<main class="content">{c_rows}
<div class="warn"><b>💡 Even Odds:</b> 2 mostri sotto contratto vanno uccisi <b>senza</b> Segni, Pozioni, Bombe, Oli e Mutageni (balestra ok). Il Grifone Reale di White Orchard conta anche se non è un contratto ufficiale — vedi Sequenza 2.</div>
</main></div>{FOOT}</body></html>""", encoding="utf-8")

# ---------- CARTE ----------
FONTE_L = {"base":"🂡 Mazzo base","acquisto":"💰 Acquisto","vittoria":"⚔️ Vittoria vs giocatore","torneo":"🏆 Torneo","missione":"📜 Missione"}
g_rows = "\n".join(f"""<div class="ob-row" data-tipo="{c['fonte']}"><input type="checkbox" class="ob-check" data-ob="g-{i}"><span class="num">{c['num'] if c['num'] else '•'}</span>
<div><div class="oname">{html.escape(c['nome'] or 'Carta')} </div>
<div class="odesc"><b style="color:var(--gold2)">{FONTE_L.get(c['fonte'],'')}</b> · {html.escape(c['desc'])}</div><div style="margin-top:6px"><a href="index.html#seq-{c['seq']}">→ Sequenza {c['seq']}</a></div></div></div>""" for i, c in enumerate(sorted(carte, key=lambda x: (x['num'] is None, x['num'] or 0, x['nome']))))
(ROOT/"carte.html").write_text(HEAD(f"Tutte le carte Gwent ({len(carte)} citate) — Guida TW3","Elenco completo delle carte Gwent con checklist per l'obiettivo Card Collector.")+f"""{top('carte.html')}<div class="wrap">
<section class="hero"><p class="kicker">Obiettivo Card Collector · 169 carte uniche del gioco base</p><h1>🃏 Tutte le <span>carte Gwent</span></h1>
<p>Ogni carta citata nella guida con fonte e sequenza. Contano solo le <b>uniche</b> (illustrazione diversa); i duplicati si impilano e non contano. Le carte dei DLC non contano per l'obiettivo.</p>
<div class="progress-line" style="max-width:520px"><i id="ob-bar"></i></div><p id="ob-label" style="color:var(--muted)"></p>
<div class="toolbar"><input id="q" class="search" style="max-width:340px;margin:0" placeholder="Filtra carte…">
<select id="f-tipo"><option value="">Tutte le fonti</option><option value="base">Mazzo base</option><option value="acquisto">Acquisto</option><option value="vittoria">Vittoria vs giocatore</option><option value="torneo">Torneo</option><option value="missione">Missione</option></select>
<button class="btn ghost" id="btn-all">Seleziona tutte</button><button class="btn ghost" id="btn-none">Azzera</button></div></section>
<main class="content">{g_rows}</main></div>{FOOT}</body></html>""", encoding="utf-8")

# ---------- GWENT (strategia) ----------
(ROOT/"gwent.html").write_text(HEAD("Guida Gwent — 169 carte, Collezionista, High Stakes — TW3","Strategia Gwent: mazzi, spie, torneo High Stakes, carte missabili.")+f"""{top('gwent.html')}<div class="wrap">
<section class="hero"><p class="kicker">Obiettivo Card Collector · 169 carte uniche</p>
<h1>🃏 Gwent: guida <span>strategica</span></h1>
<p>Il Gwent è il vero “boss finale” del 100%: servono <b>169 carte uniche</b> (i duplicati non contano; contano invece le varianti con illustrazione diversa). Elenco completo con checklist nella pagina <a href="carte.html">Carte Gwent</a>.</p>
<div class="cta"><a class="btn" href="carte.html">🃏 Checklist carte</a><a class="btn ghost" href="index.html">📖 Torna alla walkthrough</a></div></section>
<div class="layout"><aside class="sidebar"><h3>In questa pagina</h3><ol class="toc" style="list-style:none;padding:0">
<li><a href="#mazzo">Mazzo iniziale</a></li><li><a href="#regole">Regole d'oro</a></li><li><a href="#casuali">Giocatori casuali</a></li>
<li><a href="#missabili">Carte missabili</a></li><li><a href="#highstakes">Torneo High Stakes</a></li><li><a href="#obgwent">Obiettivi Gwent</a></li></ol></aside>
<main class="content">
<div class="intro-box" id="mazzo"><p class="kicker">Sequenza 1 · White Orchard</p><h2 style="color:var(--cream)">Mazzo iniziale (28 carte)</h2>
<p>Lo studioso nella taverna di White Orchard ti insegna il Gwent e ti consegna il mazzo base <b>Regni Settentrionali + Neutrali</b>: i 4 leader (Foltest, Emhyr, Francesca, Eredin), carte meteo (Gelo, Nebbia, Pioggia, Sereno), Dethmold, 2 Trabucco, 2 Ballista, Ves, Siegfried, Keira, Síle, Stennis, Medico, Sabrina, Sheldon, Commando, Fanteria, 2 Fanti Redaniani, Esperto d'assedio, Yarpen. Battendo lo studioso ottieni <b>Zoltan Chivay</b> + il libro <b>Miraculous Guide to Gwent</b> (la tua checklist in gioco).</p></div>
<div class="intro-box" id="regole"><p class="kicker">Strategia</p><h2 style="color:var(--cream)">Regole d'oro</h2>
<div class="grid2"><div class="tip"><h4>🂡 Mazzo corto (28–36 carte)</h4><p>Non superare le 36 carte: più carte = più probabilità di pescare scarti. Tieni solo le migliori per ogni riga.</p></div>
<div class="tip"><h4>🕵️ Spie + Esche</h4><p>Le Spie si giocano sul campo avversario per pescare 2 carte. Tieni sempre 2–3 <b>Esche (Decoy)</b> per rubare le Spie che il nemico gioca da te (Barone Sanguinario docet).</p></div>
<div class="tip"><h4>🌧️ Meteo vs Mostri</h4><p>I mazzi Mostro puntano tutto su mischia + Richiamo (Muster): rispondi con <b>Gelo Pungente</b>. Corno del comandante e corni multipli vincono i round lunghi.</p></div>
<div class="tip"><h4>💰 Compra tutto</h4><p>Ogni oste/mercante vende carte (10–50 corone): compra sempre tutte quelle con illustrazione nuova. I duplicati si impilano, le uniche no.</p></div></div></div>
<div class="intro-box" id="casuali"><p class="kicker">Come funzionano</p><h2 style="color:var(--cream)">Giocatori casuali (~50)</h2>
<p>Armaioli, fabbri, mercanti e osti danno <b>una carta casuale dal pool di ~50</b> alla prima vittoria (poi solo materiali). Sfida <b>tutti</b> quelli che incontri — è l'unico modo per completare il pool. Se da uno ricevi un duplicato, la carta unica che ti manca arriverà da un altro: la guida segnala “carta ottenuta da X, la tua potrebbe differire”. Controlla il conteggio nel libro Miraculous Guide.</p></div>
<div class="intro-box" id="missabili"><p class="kicker">Da non perdere</p><h2 style="color:var(--cream)">Carte missabili</h2>
<div class="warn"><b>⚠️ Torneo High Stakes (Passiflora, Novigrad):</b> non iscriverti finché non hai ~165 carte e un mazzo fortissimo. <b>Salva prima di entrare</b>: se perdi, le carte sono perse per sempre e addio <b>Card Collector</b>. Non puoi ritirarti una volta dentro.</div>
<ul><li><b>Festa dai Vegelbud (A Matter of Life &amp; Death):</b> mini-torneo dal croupier nel cortile — <b>salva prima</b>, vincilo o perdi le carte.</li>
<li><b>A Dangerous Game (Zoltan):</b> servono 3 carte uniche — <b>non separartene mai</b>, salva spesso.</li>
<li><b>Lambert (Following the Thread):</b> dopo la missione <b>parlagli subito</b> prima che sparisca, o la sua carta slitta a Kaer Morhen.</li>
<li><b>Thaler, Roche, Dijkstra, Zoltan, Crach, Ermion, Gremist:</b> legati alle rispettive missioni — sfidali appena disponibili.</li></ul></div>
<div class="intro-box" id="highstakes"><p class="kicker">Sequenza 27 · fine gioco</p><h2 style="color:var(--cream)">Torneo High Stakes</h2>
<p>Entra solo a collezione quasi completa. Ordine tipico: primo sfidante → “Sasha” (accetta o rifiuta, dovrai comunque vincere leale) → finale contro <b>Tybalt</b>. Vincere sblocca <b>Gwent Master</b> e le ultime carte per <b>Card Collector (tutte le 169)</b>. Le carte dei DLC Hearts of Stone <b>non contano</b> per l'obiettivo.</p></div>
<div class="intro-box" id="obgwent"><p class="kicker">Obiettivi</p><h2 style="color:var(--cream)">Obiettivi legati al Gwent</h2>
<table><tr><th>Obiettivo</th><th>Come</th></tr>
<tr><td><b>Geralt &amp; Friends</b></td><td>Vinci un round usando solo carte Neutrali (meteo + Zoltan). Tentativo facile già contro lo studioso a White Orchard.</td></tr>
<tr><td><b>All In</b></td><td>Gioca 3 carte Eroe in un round e vinci la partita.</td></tr>
<tr><td><b>Killed It</b></td><td>Vinci un round con forza totale ≥ 187.</td></tr>
<tr><td><b>Gwent Master</b></td><td>Batti Tybalt e vinci il torneo High Stakes.</td></tr>
<tr><td><b>Card Collector</b></td><td>Ottieni tutte le 169 carte del gioco base.</td></tr></table></div>
</main></div></div>{FOOT}</body></html>""", encoding="utf-8")

# ---------- MISSIONI ----------
def mrows(lst, anchor):
    return "\n".join(f"""<div class="ob-row"><span class="num">{m['num'] if m['num'] else '•'}</span>
<div><div class="oname">{html.escape(m['nome'] or '—')} <span style="color:var(--muted);font-weight:normal">· seq. {m['seq']}</span></div>
<div class="odesc">{html.escape(m['desc'])}</div><div style="margin-top:6px"><a href="index.html#seq-{m['seq']}">→ Vai alla Sequenza {m['seq']}</a></div></div></div>""" for m in sorted(lst, key=lambda x: (x['num'] is None, x['num'] or 0)))
sec_rows = "\n".join(f"""<div class="ob-row"><span class="num">•</span>
<div><div class="oname">{html.escape(s['nome'])} <span style="color:var(--muted);font-weight:normal">· citata {s['n']}× · prima in seq. {s['seq']}</span></div>
<div style="margin-top:6px"><a href="index.html#seq-{s['seq']}">→ Vai alla Sequenza {s['seq']}</a></div></div></div>""" for s in sorted(secondarie, key=lambda x: x['nome']))
(ROOT/"missioni.html").write_text(HEAD(f"Missioni ({len(missioni)} principali, {len(secondarie)} secondarie) — Guida TW3","Tutte le missioni citate nella guida con rimandi alle sequenze.")+f"""{top('missioni.html')}<div class="wrap">
<section class="hero"><p class="kicker">Trama + Ciri + DLC</p><h1>📜 Tutte le <span>missioni</span></h1>
<p>Ogni missione citata nella walkthrough con rimando diretto alla sequenza che la spiega. Secondarie uniche indicizzate per nome.</p>
<div class="toolbar"><input id="q" class="search" style="max-width:340px;margin:0" placeholder="Filtra missioni…"></div></section>
<main class="content">
<div class="intro-box" id="principali"><p class="kicker">{len(missioni)} voci</p><h2 style="color:var(--cream)">Missioni principali</h2>{mrows(missioni,'p')}</div>
<div class="intro-box" id="ciri"><p class="kicker">{len(ciri)} voci</p><h2 style="color:var(--cream)">Missioni di Ciri (flashback giocabili)</h2>{mrows(ciri,'c')}</div>
<div class="intro-box" id="bw"><p class="kicker">{len(bw)} voci</p><h2 style="color:var(--cream)">Missioni di Blood &amp; Wine</h2>{mrows(bw,'b')}</div>
<div class="intro-box" id="dlc"><p class="kicker">{len(dlcq)} voci</p><h2 style="color:var(--cream)">Missioni DLC (agganci Hearts of Stone)</h2>{mrows(dlcq,'d')}</div>
<div class="intro-box" id="secondarie"><p class="kicker">{len(secondarie)} voci uniche</p><h2 style="color:var(--cream)">Missioni secondarie (indice)</h2>{sec_rows}</div>
</main></div>{FOOT}</body></html>""", encoding="utf-8")

# ---------- DLC & FINALI ----------
miss_html = "\n".join(f"<li style='margin:8px 0'>{inline(b)}</li>" for b in uniq_miss)
hos_seq = [s for s in sections if 32 <= s["num"] <= 36]
bw_seq = [s for s in sections if 37 <= s["num"] <= 43]
def seq_links(lst):
    return "".join(f"<li style='margin:6px 0'><a href='index.html#seq-{s['num']}'><b style='color:var(--gold)'>Sequenza {s['num']}</b> — {html.escape(s['title'])}</a></li>" for s in lst)
(ROOT/"dlc-finali.html").write_text(HEAD("DLC Hearts of Stone, Blood & Wine, finali e missabili — Guida TW3","Finali del gioco base e dei DLC, scelte critiche e lista completa dei punti missabili.")+f"""{top('dlc-finali.html')}<div class="wrap">
<section class="hero"><p class="kicker">12 obiettivi HoS · 13 obiettivi B&amp;W</p><h1>🐺 DLC &amp; <span>Finali</span></h1>
<p>Hearts of Stone (Novigrad) e Blood &amp; Wine (Toussaint) hanno trame <b>altamente missabili</b>: qui trovi finali, scelte critiche e — sotto — <b>ogni singolo avviso missabile</b> estratto dalla guida.</p>
<div class="cta"><a class="btn" href="#missabili">⚠️ Vai ai punti missabili</a><a class="btn ghost" href="index.html#seq-32">📖 Sequenze DLC nella guida</a></div></section>
<div class="layout"><aside class="sidebar"><h3>In questa pagina</h3><ol class="toc" style="list-style:none;padding:0">
<li><a href="#finali-base">Finali gioco base</a></li><li><a href="#hos">Hearts of Stone</a></li>
<li><a href="#bw">Blood &amp; Wine</a></li><li><a href="#missabili">Tutti i missabili</a></li></ol></aside>
<main class="content">
<div class="intro-box" id="finali-base"><p class="kicker">Buono · Interessante · Cattivo</p><h2 style="color:var(--cream)">I 3 finali del gioco base</h2>
<p>Il finale dipende da <b>cosa dici a Ciri in 4 missioni principali</b> verso fine gioco. Se interpreti Geralt “di pancia” rischi il finale peggiore senza accorgertene: segui le indicazioni delle <b>Sequenze 28–31</b> (Riunione, Battaglia di Kaer Morhen, Il Re è Morto, Profezia di Ithlinne). Obiettivi legati: <b>Something More</b> (trova Ciri), <b>Xenonaut</b>, <b>The King of the Dead</b> (sconfiggi Eredin), <b>Passed the Trial / Ran the Gauntlet / Walked the Path</b> (finale a Marcia della Morte).</p>
<div class="warn"><b>⚠️ Full Crew (missabile):</b> porta tutti e 6 gli alleati a Kaer Morhen — Keira Metz <b>non deve morire</b> (Sequenza 9), Triss va convinta in <b>Now or Never</b>, più Roche, Dijkstra/Emhyr, Hjalmar/Cerys. Se ne manca uno, addio 100%.</div></div>
<div class="intro-box" id="hos"><p class="kicker">Sequenze 32–36 · Novigrad</p><h2 style="color:var(--cream)">Hearts of Stone</h2>
<p>Espansione breve: Gaunter O'Dimm ti aggancia dalla bacheca (Sequenza 13) ma va giocata <b>dopo</b> la Wild Hunt. Obiettivi chiave: <b>I'm Not Kissing That</b> (principe-rospo), <b>Shopaholic</b> (asta Borsodi — fai offerte su tutti e 3 i lotti), <b>Let the Good Times Roll!</b> (tutte e 10 le attività al matrimonio), <b>Curator of Nightmares</b> + <b>When It's Many Against One…</b> (gli 8 incubi di Iris nel Mondo Dipinto — non saltare il primo), <b>Pacta Sunt Servanda</b> (completa l'espansione).</p>
<ol>{seq_links(hos_seq)}</ol></div>
<div class="intro-box" id="bw"><p class="kicker">Sequenze 37–43 · Toussaint</p><h2 style="color:var(--cream)">Blood &amp; Wine</h2>
<p>Nuova regione, nuovo mazzo <b>Skellige (38 carte)</b> per <b>I Have A Gwent Problem</b>, mutazioni per <b>Weapon “W”</b>, Corvo Bianco per <b>Playing House</b>, diagrammi Gran Maestro per <b>Turned Every Stone / Dressed to Kill</b>, torneo cavalleresco per <b>A Knight to Remember</b> e Aerondight per <b>Embodiment of the Five Virtues</b> (le 5 virtù tutte completate prima di tornare dall'eremita).</p>
<div class="warn"><b>⚠️ Doppio finale, doppi salvataggi:</b> a <b>Capture the Castle</b> fai un salvataggio manuale al “punto di non ritorno” (due finali = due obiettivi: <b>Last Action Hero</b> e <b>Kling of the Clink</b>); un secondo salvataggio dopo aver parlato con i corvi + un terzo nel mondo delle fiabe <b>prima</b> di parlare con la Ragazza che vende la selce (il Nastro di Syanna decide tutto).</div>
<ol>{seq_links(bw_seq)}</ol></div>
<div class="intro-box" id="missabili"><p class="kicker">{len(uniq_miss)} avvisi estratti dalla guida</p><h2 style="color:var(--cream)">Tutti i punti missabili</h2>
<p style="color:var(--muted)">Ogni paragrafo della guida che segnala contenuti perdibili, nell'ordine di comparsa. Usalo come checklist anti-errori insieme alla walkthrough.</p>
<ol>{miss_html}</ol></div>
</main></div></div>{FOOT}</body></html>""", encoding="utf-8")

print("pagine:", sorted(p.name for p in ROOT.glob("*.html")))
