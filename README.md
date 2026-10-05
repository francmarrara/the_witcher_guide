# The Witcher 3 — Guida 100% in italiano

Sito statico (HTML/CSS/JS puro) con walkthrough completa al 100% di **The Witcher 3: Wild Hunt**, tradotta e riorganizzata per il web.

- **38 sequenze** walkthrough: Kaer Morhen → Velen → Novigrad → Skellige → Kaer Morhen → DLC
- **78 obiettivi** (base + Hearts of Stone + Blood and Wine)
- **169 carte Gwent**, **34 contratti**, missioni missabili, finali, build Marcia della Morte
- Stima: **140–180 ore**, una sola partita a **Death March** senza mai abbassare la difficoltà

Fonte testi: guida di **Cynic 0055 (Cynical Guides)** su Steam — https://steamcommunity.com/sharedfiles/filedetails/?id=3162226469 (+ checklist https://steamcommunity.com/sharedfiles/filedetails/?id=3162875051). Sito non ufficiale, senza asset coperti da copyright. The Witcher è un marchio di CD PROJEKT RED.

## Struttura repo

```
the_witcher/
├── README.md
├── witcher3-wild-hunt-100-achievement-guide.it.md  # sorgente IT della guida
├── witcher3-wild-hunt-100-achievement-guide.md      # originale EN
├── witcher3-clean-en.md
└── sito-witcher3/
    ├── index.html        # walkthrough completa (38 sequenze)
    ├── obiettivi.html    # checklist 78 obiettivi (salvataggio in localStorage)
    ├── build.html        # build Marcia della Morte
    ├── contratti.html    # contratti da witcher
    ├── carte.html        # tutte le carte Gwent
    ├── gwent.html        # strategia Gwent + High Stakes
    ├── missioni.html     # indice missioni
    ├── dlc-finali.html   # DLC, 3 finali, punti missabili
    ├── assets/styles.css + assets/app.js
    └── tools/genera.py + tools/build_page.py  # script di generazione
```

## Uso locale

Nessuna build, nessun server richiesto. Apri `sito-witcher3/index.html` nel browser, oppure servi la cartella:

```bash
cd sito-witcher3
python3 -m http.server 8000
# → http://localhost:8000
```

Checklist e progresso lettura si salvano nel `localStorage` del browser.

## Rigenerare il sito

Il sito è generato dal sorgente `.it.md`. Dopo aver modificato la guida:

```bash
cd sito-witcher3
python3 tools/genera.py      # rigenera index + obiettivi, contratti, carte, gwent, missioni, dlc-finali
python3 tools/build_page.py  # rigenera build.html
```

Solo stdlib Python, nessun dipendenza.

## Avvisi critici (spoiler)

- **High Stakes (Gwent):** entra solo a ~165 carte con mazzo forte, salva prima — sconfitta = `Card Collector` perso.
- **Full Crew:** Keira Metz non deve morire + tutti i 6 alleati a Kaer Morhen.
- **Blood and Wine:** salvataggio manuale a `Capture the Castle` (doppio finale) + prima di parlare con la Ragazza della selce (nastro di Syanna).
