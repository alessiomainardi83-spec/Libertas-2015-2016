"""Legge da fip.it calendario e risultati della DR3 Toscana, Girone B (girone del Philos Livorno).
Usa lo stesso lettore di fip_dr1.py. Nessun dato personale: solo squadre, date, orari, palestre, punteggi.
uso: python3 tools/fip_dr3.py <cartella temporanea> <file json di uscita>"""
import os, sys, re, json, subprocess, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fip_dr1 as f

GIRONE = '85903'          # DR3 Toscana, Prima Fase, Girone B
GIORNATE = 9              # 9 squadre: 9 giornate per girone (una squadra riposa ogni turno)
URL = f.URL.replace('codice_campionato=D', 'codice_campionato=1DM')

def scarica(cartella):
    os.makedirs(cartella, exist_ok=True)
    def one(a):
        ar, n = a; p = os.path.join(cartella, 'd_%d_%d.html' % (ar, n))
        for _ in range(3):
            r = subprocess.run(['curl', '-s', '-m', '30', '-o', p, URL % (GIRONE, ar, n)])
            if r.returncode == 0 and os.path.exists(p) and os.path.getsize(p) > 50000: return True
        return False
    with cf.ThreadPoolExecutor(6) as ex:
        return all(ex.map(one, [(ar, n) for ar in (0, 1) for n in range(1, GIORNATE + 1)]))

if __name__ == '__main__':
    cartella, uscita = sys.argv[1], sys.argv[2]
    if not scarica(cartella): sys.exit('ERRORE: pagine FIP DR3 non scaricate')
    res = []
    for ar in (0, 1):
        for n in range(1, GIORNATE + 1):
            res += f.parse(os.path.join(cartella, 'd_%d_%d.html' % (ar, n)), ar, n)
    if len(res) < 60: sys.exit('ERRORE: troppe poche gare DR3 lette (%d)' % len(res))
    if not any('PHILOS' in x['casa'] + x['ospite'] for x in res): sys.exit('ERRORE: Philos non trovato')
    for x in res: x['campo'] = re.sub(r'\s*Arbitri.*$', '', x['campo'])
    json.dump(res, open(uscita, 'w'), ensure_ascii=False, indent=0)
    print('gare DR3 lette:', len(res), 'giocate:', sum(1 for x in res if x['pt_casa'] is not None))
