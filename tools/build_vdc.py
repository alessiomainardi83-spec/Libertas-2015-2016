"""Crea valdicornia.html (app per Nicola) partendo da index.html (app Libertas 2015-2016)
e aggiungendo calendario, risultati e classifica della DR1 Toscana (girone del Val di Cornia).
uso: python3 tools/build_vdc.py   (dalla cartella del repository; legge tools/dr1.json)
index.html non viene modificato."""
import json, re, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, 'index.html')
DST = os.path.join(BASE, 'valdicornia.html')
DATI = os.path.join(BASE, 'tools', 'dr1.json')

GIRONE_TXT = "Girone B"
GIRONE_URL = "https://fip.it/risultati/?group=campionati-regionali&regione_codice=TO&comitato_codice=RTO&sesso=M&codice_campionato=D&codice_fase=1&codice_girone=85200"

NOMI = {  # nomi brevi, senza sponsor e sigle
    'STUDIO ARCADIA VALDICORNIA': 'Val di Cornia Basket',
    'BASKET CALCINAIA': 'Basket Calcinaia',
    'BASKET DONORATICO': 'Basket Donoratico',
    'BCL LAB LUCCA': 'BCL Lucca',
    'CENTRO MINIBK CARRARA': 'Centro Minibasket Carrara',
    'CESTISTICA AUDACE PESCIA': 'Audace Pescia',
    'CUS PISA': 'CUS Pisa',
    'FORTEZZA BASKET': 'Fortezza Basket Livorno',
    'JUVE PONTEDERA': 'Juve Pontedera',
    'LIBERTAS BASKET LUCCA': 'Libertas Lucca',
    'LUCCA SKY WALKERS': 'Lucca Sky Walkers',
    'MONTEMURLO BASKET': 'Montemurlo Basket',
    'SHOEMAKERS BASKET MONSUMMANO': 'Shoemakers Monsummano',
    'VALMEC SM SRL SEI ROSE': 'Sei Rose Rosignano',
    'VELA BASKET': 'Vela Basket Viareggio',
}

def fail(msg):
    sys.exit('ERRORE build_vdc: ' + msg)

def campo_txt(s):
    s = re.sub(r'\s*Arbitri.*$', '', s).strip()
    m = re.match(r'^(.*?)\s+\d{5}\s+(.+?)\s*\((\w\w)\)\s*$', s)
    if not m:
        return s
    luogo, citta = m.group(1).strip().rstrip(','), m.group(2).strip().title()
    luogo = re.sub(r'\([A-Z]{2}\)', '', luogo).strip()
    if luogo.isupper():
        luogo = luogo.title()
    return luogo + ', ' + citta

def main():
    h = open(SRC, encoding='utf-8').read()
    G = json.load(open(DATI, encoding='utf-8'))
    if 'VALDICORNIA' not in json.dumps(G):
        fail('Val di Cornia non trovato nei dati')

    # codici squadre e campi
    squadre = {}
    nomi = sorted(set(x['casa'] for x in G) | set(x['ospite'] for x in G))
    i = 1
    for n in nomi:
        if 'VALDICORNIA' in n:
            squadre[n] = 'VC'
        else:
            squadre[n] = 'D%02d' % i; i += 1
    campi = {}
    for c in sorted(set(campo_txt(x['campo']) for x in G)):
        campi[c] = 'K%02d' % (len(campi) + 1)

    # andata = la metà con le date più vecchie
    dmin = {}
    for x in G:
        if x['data']:
            dmin[x['ar']] = min(dmin.get(x['ar'], '9999'), x['data'])
    ar_andata = min(dmin, key=lambda k: dmin[k])

    righe = []
    for x in sorted(G, key=lambda x: (x['data'], x['ora'], x['gara'])):
        if not x['data']:
            continue
        g = ('A' if x['ar'] == ar_andata else 'R') + str(x['giornata'])
        pc = '' if x['pt_casa'] is None else str(x['pt_casa'])
        po = '' if x['pt_ospite'] is None else str(x['pt_ospite'])
        r = '|'.join([x['gara'], 'V', x['data'], x['ora'] or '00:00', squadre[x['casa']], squadre[x['ospite']], pc, po, campi[campo_txt(x['campo'])], g])
        if r.count('|') != 9 or '"' in r:
            fail('riga non valida: ' + r)
        righe.append(r)

    sq_js = ',\n '.join('%s:%s' % (c, json.dumps(NOMI.get(n, n.title()), ensure_ascii=False)) for n, c in sorted(squadre.items(), key=lambda t: t[1]))
    ca_js = ',\n '.join('%s:%s' % (c, json.dumps(n, ensure_ascii=False)) for n, c in sorted(campi.items(), key=lambda t: t[1]))
    blocco = (
        '/* ====== VAL DI CORNIA DR1 (generato da tools/build_vdc.py, dati fip.it) ====== */\n'
        'var VDC_SQUADRE={' + sq_js + '};\n'
        'var VDC_CAMPI={' + ca_js + '};\n'
        'var VDC_RAW=[\n' + ',\n'.join(json.dumps(r) for r in righe) + '\n];\n'
        'Object.keys(VDC_SQUADRE).forEach(function(k){SQUADRE[k]=VDC_SQUADRE[k]});\n'
        'Object.keys(VDC_CAMPI).forEach(function(k){CAMPI[k]=VDC_CAMPI[k]});\n'
        'GIRONI.V={nome:"Val di Cornia DR1",anno:"",girone:' + json.dumps('DR1 Toscana · ' + GIRONE_TXT) + ',url:' + json.dumps(GIRONE_URL) + '};\n'
        'RAW=RAW.concat(VDC_RAW);\n'
    )

    def sub(old, new, count=1):
        nonlocal h
        n = h.count(old)
        if n != count:
            fail('pezzo di codice non trovato (%d volte invece di %d): %s' % (n, count, old[:80]))
        h = h.replace(old, new)

    sub('/* ====== FINE DATI ====== */', blocco + '/* ====== FINE DATI ====== */')
    sub('<title>Libertas Livorno 2015·2016</title>', '<title>Libertas 2015·2016 + Val di Cornia</title>')
    sub('<div class="sub">Aquilotti Big 2016 · Esordienti 2015 · stagione 2026/27</div>',
        '<div class="sub">Aquilotti Big 2016 · Esordienti 2015 · Val di Cornia DR1 · 2026/27</div>')
    sub('.badge.gold{', '.badge.vc{background:#0d5c8a;color:#fff}\n.teams .t.vc{color:#0d5c8a}\n@media (prefers-color-scheme: dark){.badge.vc{background:#2b7fb3}.teams .t.vc{color:#7cc4ff}}\n.badge.gold{')
    sub('function isLib(p){return p.casa==="LI"||p.osp==="LI"}',
        'function us(k){return k==="LI"||k==="VC"}\nfunction isLib(p){return us(p.casa)||us(p.osp)}')
    sub('var a=p.casa==="LI"?p.pc:p.po,b=p.casa==="LI"?p.po:p.pc;', 'var a=us(p.casa)?p.pc:p.po,b=us(p.casa)?p.po:p.pc;')
    sub('var k=p.c==="E"?"E":"A";', 'var k=p.c==="E"?"E":p.c==="V"?"V":"A";')
    sub(""":'<span class="badge '+(p.c==="A"?"aq":"")+'">'+GIRONI[p.c].nome+"</span>";""",
        """:'<span class="badge '+(p.c==="A"?"aq":p.c==="V"?"vc":"")+'">'+GIRONI[p.c].nome+"</span>";""")
    sub("""<span class="t '+(p.casa==="LI"?"lib":"")+'">'""", """<span class="t '+(p.casa==="LI"?"lib":p.casa==="VC"?"vc":"")+'">'""")
    sub("""<span class="t '+(p.osp==="LI"?"lib":"")+'">'""", """<span class="t '+(p.osp==="LI"?"lib":p.osp==="VC"?"vc":"")+'">'""")
    sub('if(f==="lib")return isLib(p);return true', 'if(f==="vc")return p.c==="V"&&isLib(p);if(f==="lib")return isLib(p);return true')
    sub('var nota=f==="girone"?"Tutte le partite dei due gironi, comprese quelle tra le altre squadre."',
        'var nota=f==="girone"?"Tutte le partite dei tre gironi, comprese quelle tra le altre squadre."')
    sub('mode==="cal"&&(f==="lib"||f==="aq")?', 'mode==="cal"&&f==="lib"?')
    sub('"«Doppio impegno» segnala solo i giorni in cui giocano sia gli Esordienti 2015 sia gli Aquilotti Big 2016 (anche se gli Aquilotti sono a un torneo). Più partite dello stesso torneo nello stesso giorno non sono un doppio impegno. Le partite «Torneo» non contano in classifica."',
        '"«Doppio impegno» segnala i giorni in cui giocano almeno due tra Esordienti 2015, Aquilotti Big 2016 (anche a un torneo) e Val di Cornia. Più partite della stessa squadra nello stesso giorno non sono un doppio impegno. Le partite «Torneo» non contano in classifica."')
    sub("""fb("lib","2015 + 2016")+fb("aq","Aquilotti Big")+fb("es","Esordienti")+""",
        """fb("lib","Tutti")+fb("aq","Aquilotti Big")+fb("es","Esordienti")+fb("vc","Val di Cornia")+""")
    sub('return ["A","E"].map(function(c){', 'return ["V","A","E"].map(function(c){')
    sub("""'<tr class="'+(x.k==="LI"?"lib":"")+'">""", """'<tr class="'+(us(x.k)?"lib":"")+'">""")
    sub('<b>\'+G.nome+" "+G.anno+\'</b>', '<b>\'+(G.nome+" "+G.anno).trim()+\'</b>')
    sub('localStorage.getItem("lib1516-filter")', 'localStorage.getItem("vdc-filter")')
    sub('localStorage.setItem("lib1516-filter",S.filter)', 'localStorage.setItem("vdc-filter",S.filter)')
    sub('["lib","aq","es","girone"].indexOf(f0)', '["lib","aq","es","vc","girone"].indexOf(f0)')
    open(DST, 'w', encoding='utf-8').write(h)
    print('valdicornia.html scritto:', len(righe), 'gare DR1,', sum(1 for r in righe if r.split('|')[6] != ''), 'con risultato')

if __name__ == '__main__':
    main()
