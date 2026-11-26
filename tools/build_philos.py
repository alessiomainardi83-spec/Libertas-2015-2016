"""Crea philos.html (app per Massimo) partendo da index.html (app Libertas 2015-2016)
e aggiungendo calendario, risultati e classifica della DR3 Toscana (girone del Philos Livorno)
piu' una scheda "Philos" con i punti dei giocatori presi dai referti (tools/philos_stats.json).
uso: python3 tools/build_philos.py   (dalla cartella del repository; legge tools/dr3.json e tools/philos_stats.json)
index.html non viene modificato."""
import json, re, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, 'index.html')
DST = os.path.join(BASE, 'philos.html')
DATI = os.path.join(BASE, 'tools', 'dr3.json')
STATS = os.path.join(BASE, 'tools', 'philos_stats.json')

GIRONE_TXT = "Girone B"
GIRONE_URL = "https://fip.it/risultati/?group=campionati-regionali&regione_codice=TO&comitato_codice=RTO&sesso=M&codice_campionato=1DM&codice_fase=1&codice_girone=85903"

NOMI = {  # nomi brevi, senza sponsor e sigle
    'GIGA ENERGIA PHILOS LIVORNO': 'Philos Livorno',
    'A.S.D.PERIGNANO': 'Perignano',
    'BASKET POMARANCE': 'Basket Pomarance',
    'CUS PISA': 'CUS Pisa',
    'DREAM BASKET PISA': 'Dream Basket Pisa',
    'FORTEZZA BASKET': 'Fortezza Basket Livorno',
    'GMV BASKET': 'GMV Basket',
    'POLISPORTIVA NICOLA CHIMENTI': 'Pol. Nicola Chimenti',
    'VICOPISANO BASKET 2011': 'Vicopisano Basket',
}

def fail(msg):
    sys.exit('ERRORE build_philos: ' + msg)

def campo_txt(s):
    s = re.sub(r'\s*Arbitri.*$', '', s).strip()
    s = re.sub(r'[^\x20-\x7EÀ-ÿ]', '', s)  # toglie caratteri sporchi del sito FIP
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
    ST = json.load(open(STATS, encoding='utf-8'))
    if 'PHILOS' not in json.dumps(G):
        fail('Philos non trovato nei dati')

    squadre = {}
    nomi = sorted(set(x['casa'] for x in G) | set(x['ospite'] for x in G))
    i = 1
    for n in nomi:
        if 'PHILOS' in n:
            squadre[n] = 'PH'
        else:
            squadre[n] = 'Q%02d' % i; i += 1
    campi = {}
    for c in sorted(set(campo_txt(x['campo']) for x in G)):
        campi[c] = 'H%02d' % (len(campi) + 1)

    dmin = {}
    for x in G:
        if x['data']:
            dmin[x['ar']] = min(dmin.get(x['ar'], '9999'), x['data'])
    ar_andata = min(dmin, key=lambda k: dmin[k])

    righe = []
    gare_ph = set()
    for x in sorted(G, key=lambda x: (x['data'], x['ora'], x['gara'])):
        if not x['data']:
            continue
        g = ('A' if x['ar'] == ar_andata else 'R') + str(x['giornata'])
        pc = '' if x['pt_casa'] is None else str(x['pt_casa'])
        po = '' if x['pt_ospite'] is None else str(x['pt_ospite'])
        r = '|'.join([x['gara'], 'P', x['data'], x['ora'] or '00:00', squadre[x['casa']], squadre[x['ospite']], pc, po, campi[campo_txt(x['campo'])], g])
        if r.count('|') != 9 or '"' in r:
            fail('riga non valida: ' + r)
        righe.append(r)
        if 'PHILOS' in x['casa'] + x['ospite']:
            gare_ph.add(x['gara'])

    # statistiche giocatori (dai referti)
    stats = []
    for p in ST.get('partite', []):
        if p.get('gara') not in gare_ph:
            fail('statistiche: gara %r non trovata tra le gare del Philos' % p.get('gara'))
        punti = p.get('punti') or {}
        for k, v in punti.items():
            if not isinstance(v, int) or v < 0 or v > 99 or not k.strip():
                fail('statistiche: valore non valido %r=%r nella gara %s' % (k, v, p['gara']))
        stats.append({'gara': p['gara'], 'punti': punti})

    sq_js = ',\n '.join('%s:%s' % (c, json.dumps(NOMI.get(n, n.title()), ensure_ascii=False)) for n, c in sorted(squadre.items(), key=lambda t: t[1]))
    ca_js = ',\n '.join('%s:%s' % (c, json.dumps(n, ensure_ascii=False)) for n, c in sorted(campi.items(), key=lambda t: t[1]))
    blocco = (
        '/* ====== PHILOS DR3 (generato da tools/build_philos.py, dati fip.it + referti) ====== */\n'
        'var PH_SQUADRE={' + sq_js + '};\n'
        'var PH_CAMPI={' + ca_js + '};\n'
        'var PH_RAW=[\n' + ',\n'.join(json.dumps(r) for r in righe) + '\n];\n'
        'var PH_STATS=' + json.dumps(stats, ensure_ascii=False) + ';\n'
        'Object.keys(PH_SQUADRE).forEach(function(k){SQUADRE[k]=PH_SQUADRE[k]});\n'
        'Object.keys(PH_CAMPI).forEach(function(k){CAMPI[k]=PH_CAMPI[k]});\n'
        'GIRONI.P={nome:"Philos DR3",anno:"",girone:' + json.dumps('DR3 Toscana · ' + GIRONE_TXT) + ',url:' + json.dumps(GIRONE_URL) + '};\n'
        'RAW=RAW.concat(PH_RAW);\n'
    )

    vphilos = r'''
function vPhilos(){var G=GIRONI.P,r=classifica("P"),pos=0,me=null;
  r.forEach(function(x,i){if(x.k==="PH"){pos=i+1;me=x}});
  var gare={};P.forEach(function(p){if(p.c==="P")gare[p.gara]=p});
  var h='<section><h2>Philos Livorno · DR3</h2><div class="card"><div class="tabhead"><b>'+(me?pos+'° posto':'')+'</b><span class="note">'+esc(G.girone)+'</span></div>'+
    '<p class="note tabfoot">'+(me?me.g+' partite · '+me.v+' vinte · '+me.p+' perse · '+me.pt+' punti in classifica':'')+'</p></div></section>';
  var T={},list=PH_STATS.filter(function(s){return gare[s.gara]}).sort(function(a,b){return sortP(gare[b.gara],gare[a.gara])});
  list.forEach(function(s){Object.keys(s.punti).forEach(function(n){var v=s.punti[n];if(!T[n])T[n]={n:n,pg:0,tot:0,max:0};T[n].pg++;T[n].tot+=v;if(v>T[n].max)T[n].max=v})});
  var gioc=Object.keys(T).map(function(k){return T[k]}).sort(function(a,b){return b.tot-a.tot||b.tot/b.pg-a.tot/a.pg||a.n.localeCompare(b.n)});
  if(!list.length){return h+'<section><h2>Punti dei giocatori</h2><div class="card"><div class="empty">Le statistiche arrivano dai referti e vengono inserite dopo ogni partita. Per ora non ce ne sono.</div></div></section>'}
  h+='<section><h2>Punti dei giocatori · totali</h2><div class="card"><div class="tablewrap"><table><thead><tr><th>#</th><th>Giocatore</th><th>Punti</th><th>Partite</th><th>Media</th><th>Max</th></tr></thead><tbody>'+
    gioc.map(function(x,i){return '<tr><td>'+(i+1)+'</td><td>'+esc(x.n)+'</td><td><b>'+x.tot+'</b></td><td>'+x.pg+'</td><td>'+(x.tot/x.pg).toFixed(1).replace(".",",")+'</td><td>'+x.max+'</td></tr>'}).join("")+
    '</tbody></table></div><p class="note tabfoot">Calcolati su '+list.length+(list.length===1?' partita':' partite')+' con il referto inserito. Partite = partite in cui il giocatore è entrato in campo.</p></div></section>';
  h+='<section><h2>Partita per partita</h2>'+list.map(function(s){var p=gare[s.gara],pr=parts(p.data),casa=p.casa==="PH",avv=casa?p.osp:p.casa;
    var a=casa?p.pc:p.po,b=casa?p.po:p.pc,ris=played(p)?'<span class="badge '+(a>b?"ph":"")+'">'+(a>b?"vinta ":a<b?"persa ":"")+a+'-'+b+'</span>':'';
    var righe=Object.keys(s.punti).map(function(n){return [n,s.punti[n]]}).sort(function(x,y){return y[1]-x[1]||x[0].localeCompare(y[0])});
    var somma=righe.reduce(function(t,x){return t+x[1]},0);
    return '<div class="card tor"><div class="line">'+ris+'<span class="note">'+pr.wd+' '+pr.g+' '+MESI[pr.m]+' · '+(casa?'in casa':'fuori')+' · '+gior(p.g)+'</span></div><b>'+esc(SQUADRE[avv])+'</b>'+
      tbl(righe.map(function(x){return [x[0],String(x[1])]}),["Giocatore","Punti"])+
      (played(p)&&somma!==a?'<span class="note">Somma dei punti del referto: '+somma+' (punteggio FIP: '+a+')</span>':'')+'</div>'}).join("")+'</section>';
  return h}
'''

    def sub(old, new, count=1):
        nonlocal h
        n = h.count(old)
        if n != count:
            fail('pezzo di codice non trovato (%d volte invece di %d): %s' % (n, count, old[:80]))
        h = h.replace(old, new)

    sub('/* ====== FINE DATI ====== */', blocco + '/* ====== FINE DATI ====== */')
    sub('<title>Libertas Livorno 2015·2016</title>', '<title>Libertas 2015·2016 + Philos</title>')
    sub('<div class="sub">Aquilotti Big 2016 · Esordienti 2015 · stagione 2026/27</div>',
        '<div class="sub">Aquilotti Big 2016 · Esordienti 2015 · Philos DR3 · 2026/27</div>')
    sub('<a href="#tornei" data-v="tornei">Tornei</a>', '<a href="#tornei" data-v="tornei">Tornei</a><a href="#philos" data-v="philos">Philos</a>')
    sub('.badge.gold{', '.badge.ph{background:#1d6b3a;color:#fff}\n.teams .t.ph{color:#1d6b3a}\n@media (prefers-color-scheme: dark){.badge.ph{background:#2f9457}.teams .t.ph{color:#8fdcab}}\n.badge.gold{')
    sub('function isLib(p){return p.casa==="LI"||p.osp==="LI"}',
        'function us(k){return k==="LI"||k==="PH"}\nfunction isLib(p){return us(p.casa)||us(p.osp)}')
    sub('var a=p.casa==="LI"?p.pc:p.po,b=p.casa==="LI"?p.po:p.pc;', 'var a=us(p.casa)?p.pc:p.po,b=us(p.casa)?p.po:p.pc;')
    sub('var k=p.c==="E"?"E":"A";', 'var k=p.c==="E"?"E":p.c==="P"?"P":"A";')
    sub(""":'<span class="badge '+(p.c==="A"?"aq":"")+'">'+GIRONI[p.c].nome+"</span>";""",
        """:'<span class="badge '+(p.c==="A"?"aq":p.c==="P"?"ph":"")+'">'+GIRONI[p.c].nome+"</span>";""")
    sub("""<span class="t '+(p.casa==="LI"?"lib":"")+'">'""", """<span class="t '+(p.casa==="LI"?"lib":p.casa==="PH"?"ph":"")+'">'""")
    sub("""<span class="t '+(p.osp==="LI"?"lib":"")+'">'""", """<span class="t '+(p.osp==="LI"?"lib":p.osp==="PH"?"ph":"")+'">'""")
    sub('if(f==="lib")return isLib(p);return true', 'if(f==="ph")return p.c==="P"&&isLib(p);if(f==="lib")return isLib(p);return true')
    sub('var nota=f==="girone"?"Tutte le partite dei due gironi, comprese quelle tra le altre squadre."',
        'var nota=f==="girone"?"Tutte le partite dei tre gironi, comprese quelle tra le altre squadre."')
    sub('mode==="cal"&&(f==="lib"||f==="aq")?', 'mode==="cal"&&f==="lib"?')
    sub('"«Doppio impegno» segnala solo i giorni in cui giocano sia gli Esordienti 2015 sia gli Aquilotti Big 2016 (anche se gli Aquilotti sono a un torneo). Più partite dello stesso torneo nello stesso giorno non sono un doppio impegno. Le partite «Torneo» non contano in classifica."',
        '"«Doppio impegno» segnala i giorni in cui giocano almeno due tra Esordienti 2015, Aquilotti Big 2016 (anche a un torneo) e Philos. Più partite della stessa squadra nello stesso giorno non sono un doppio impegno. Le partite «Torneo» non contano in classifica."')
    sub("""fb("lib","2015 + 2016")+fb("aq","Aquilotti Big")+fb("es","Esordienti")+""",
        """fb("lib","Tutti")+fb("aq","Aquilotti Big")+fb("es","Esordienti")+fb("ph","Philos")+""")
    sub('return ["A","E"].map(function(c){', 'return ["P","A","E"].map(function(c){')
    sub("""'<tr class="'+(x.k==="LI"?"lib":"")+'">""", """'<tr class="'+(us(x.k)?"lib":"")+'">""")
    sub('<b>\'+G.nome+" "+G.anno+\'</b>', '<b>\'+(G.nome+" "+G.anno).trim()+\'</b>')
    sub('localStorage.getItem("lib1516-filter")', 'localStorage.getItem("philos-filter")')
    sub('localStorage.setItem("lib1516-filter",S.filter)', 'localStorage.setItem("philos-filter",S.filter)')
    sub('["lib","aq","es","girone"].indexOf(f0)', '["lib","aq","es","ph","girone"].indexOf(f0)')
    sub('["calendario","risultati","classifiche","tornei"].indexOf(v)', '["calendario","risultati","classifiche","tornei","philos"].indexOf(v)')
    sub('v==="tornei"?vTornei():vClass();', 'v==="tornei"?vTornei():v==="philos"?vPhilos():vClass();')
    sub('dati FIP Toscana e organizzatori dei tornei.', 'dati FIP Toscana, organizzatori dei tornei e referti Philos.')
    sub('</style>', '@media (max-width:420px){nav.tabs a{font-size:12.5px;padding-left:2px;padding-right:2px}}\n</style>')
    sub('function route(){', vphilos.strip() + '\n\nfunction route(){')
    open(DST, 'w', encoding='utf-8').write(h)
    print('philos.html scritto:', len(righe), 'gare DR3,', sum(1 for r in righe if r.split('|')[6] != ''), 'con risultato,', len(stats), 'referti')

if __name__ == '__main__':
    main()
