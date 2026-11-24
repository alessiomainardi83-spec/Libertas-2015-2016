"""Legge da fip.it calendario e risultati della DR1 Toscana (girone del Val di Cornia). Nessun dato personale: solo squadre, date, orari, palestre, punteggi."""
import re,html,sys,json,glob,os
MESI={m:i+1 for i,m in enumerate(['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'])}
def lines_of(h):
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S); t=re.sub(r'<[^>]+>','\n',t); t=html.unescape(t)
    return [re.sub(r'\s+',' ',l).strip() for l in t.split('\n') if l.strip()]
def parse(path,ar,n):
    L=lines_of(open(path,encoding='utf-8',errors='replace').read()); out=[]
    for i,l in enumerate(L):
        if l!='Squadra di casa' or L[i-1]!='Info': continue
        casa=L[i+1]; assert L[i+2]=='Squadra ospite'; osp=L[i+3]
        campo=''
        if L[i+4]=='Campo di gioco':
            j=i+5; parts=[]
            while j<len(L) and not L[j].startswith('1° Arbitro') and L[j]!='Info' and len(parts)<8:
                parts.append(L[j]); j+=1
            s=' '.join(parts); s=re.sub(r'\s*\(\s*','(',s).replace('( ','(')
            campo=re.sub(r'\s+',' ',s).strip()
        # backward
        k=i-2; stato=[]
        while not re.fullmatch(r'\d{6}',L[k]): stato.append(L[k]); k-=1
        gara=L[k]; ora=L[k-1]; data=L[k-2]
        m=re.fullmatch(r'(\d{1,2}) (\w+) (\d{4})',data)
        d='%s-%02d-%02d'%(m.group(3),MESI[m.group(2).lower()],int(m.group(1))) if m else ''
        if not re.fullmatch(r'\d{1,2}:\d{2}',ora): ora=''
        seq=L[k-6:k-2] if k>=6 else []
        pc=po=None
        if len(seq)==4 and seq[0]==casa and seq[2]==osp and seq[1].isdigit() and seq[3].isdigit(): pc,po=int(seq[1]),int(seq[3])
        out.append(dict(gara=gara,ar=ar,giornata=n,data=d,ora=ora,casa=casa,ospite=osp,pt_casa=pc,pt_ospite=po,campo=campo,stato=' · '.join(reversed(stato))))
    return out
URL='https://fip.it/risultati/?group=campionati-regionali&regione_codice=TO&comitato_codice=RTO&sesso=M&codice_campionato=D&codice_fase=1&codice_girone=%s&codice_ar=%d&giornata=%d'
def scarica(girone,cartella):
    import subprocess,concurrent.futures as cf
    os.makedirs(cartella,exist_ok=True)
    def one(a):
        ar,n=a; p=os.path.join(cartella,'d_%d_%d.html'%(ar,n))
        for _ in range(3):
            r=subprocess.run(['curl','-s','-m','30','-o',p,URL%(girone,ar,n)])
            if r.returncode==0 and os.path.getsize(p)>50000: return True
        return False
    with cf.ThreadPoolExecutor(8) as ex: ok=list(ex.map(one,[(ar,n) for ar in (0,1) for n in range(1,16)]))
    return all(ok)
if __name__=='__main__':
    # uso: python3 fip_dr1.py <girone FIP> <cartella temporanea> <file json di uscita>
    girone,cartella,uscita=sys.argv[1],sys.argv[2],sys.argv[3]
    if not scarica(girone,cartella): sys.exit('ERRORE: pagine FIP non scaricate')
    res=[]
    for ar in (0,1):
        for n in range(1,16): res+=parse(os.path.join(cartella,'d_%d_%d.html'%(ar,n)),ar,n)
    if len(res)<100: sys.exit('ERRORE: troppe poche gare lette (%d)'%len(res))
    for x in res: x['campo']=re.sub(r'\s*Arbitri.*$','',x['campo'])
    json.dump(res,open(uscita,'w'),ensure_ascii=False,indent=0)
    print('gare lette:',len(res),'giocate:',sum(1 for x in res if x['pt_casa'] is not None))
