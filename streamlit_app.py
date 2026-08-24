import streamlit as st
import requests
import pandas as pd
from datetime import date

st.set_page_config(page_title="Match Comparator", page_icon="⚽", layout="centered", initial_sidebar_state="collapsed")

LEAGUES = {"🇮🇹 Serie A":135,"🏴 Premier League":39,"🇪🇸 La Liga":140,"🇩🇪 Bundesliga":78,
           "🇫🇷 Ligue 1":61,"🇵🇹 Primeira Liga":94,"🇳🇱 Eredivisie":88,
           "🏆 Champions League":2,"🏆 Europa League":3,"🏆 Conference League":848}
BASE="https://v3.football.api-sports.io"

st.markdown("""<style>
.block-container{padding-top:1rem;padding-left:.8rem;padding-right:.8rem;max-width:760px}
[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.25);border-radius:14px;padding:10px}
.match-card{border:1px solid rgba(128,128,128,.28);border-radius:16px;padding:14px;margin:9px 0}
.big{font-size:1.25rem;font-weight:700}.muted{opacity:.7}.score{font-size:1.5rem;font-weight:800}
</style>""", unsafe_allow_html=True)

st.title("⚽ Match Comparator")
st.caption("Analisi statistica • ottimizzato per iPhone")

with st.expander("⚙️ Filtri", expanded=True):
    api_key=st.text_input("API-Football API Key",type="password",label_visibility="collapsed",placeholder="Inserisci API key")
    day=st.date_input("📅 Data",date.today())
    leagues=st.multiselect("🏆 Campionati",list(LEAGUES),default=list(LEAGUES)[:5])
    load=st.button("🔎 ANALIZZA PARTITE",use_container_width=True,type="primary")

@st.cache_data(ttl=900,show_spinner=False)
def api(endpoint,params,key):
    r=requests.get(f"{BASE}/{endpoint}",headers={"x-apisports-key":key},params=params,timeout=25)
    r.raise_for_status(); d=r.json()
    if d.get("errors"): raise RuntimeError(str(d["errors"]))
    return d.get("response",[])

def n(x):
    try:return float(str(x).replace("%",""))
    except:return 0
def ranking(pred):
    p=(pred or {}).get("predictions",{}); q=p.get("percent",{})
    h,d,a=n(q.get("home")),n(q.get("draw")),n(q.get("away"))
    idx=min(100,round(40+max(h,d,a)*.45+(3 if p.get("advice") else 0)))
    sig="1" if h>=d and h>=a else ("X" if d>=a else "2")
    return idx,h,d,a,sig

if not api_key:
    st.info("Inserisci la tua API key per iniziare.")
    st.stop()
if not leagues:
    st.warning("Seleziona almeno un campionato.")
    st.stop()

if load:
    rows=[]
    with st.spinner("Recupero partite…"):
        for name in leagues:
            for f in api("fixtures",{"league":LEAGUES[name],"season":day.year,"date":day.isoformat(),"timezone":"Europe/Rome"},api_key):
                if f["fixture"]["status"]["short"] in {"PST","CANC","ABD"}: continue
                rows.append({"Campionato":name,"Ora":f["fixture"]["date"][11:16],
                             "Partita":f'{f["teams"]["home"]["name"]} - {f["teams"]["away"]["name"]}',
                             "Fixture":f["fixture"]["id"],"HomeID":f["teams"]["home"]["id"],
                             "AwayID":f["teams"]["away"]["id"]})
    if not rows:
        st.warning("Nessuna partita trovata.")
        st.stop()

    data=[]
    with st.spinner("Calcolo ranking…"):
        for r in rows:
            try:
                p=api("predictions",{"fixture":r["Fixture"]},api_key)
                idx,h,d,a,s=ranking(p[0] if p else None)
            except: idx,h,d,a,s=0,0,0,0,"—"
            data.append({**r,"Indice":idx,"1":h,"X":d,"2":a,"Segnale":s})
    df=pd.DataFrame(data).sort_values("Indice",ascending=False).reset_index(drop=True)

    st.subheader(f"🔥 Migliori match — {day.strftime('%d/%m/%Y')}")
    for i,r in df.iterrows():
        st.markdown(f"""<div class="match-card">
        <div class="muted">{r.Campionato} • {r.Ora}</div>
        <div class="big">{r.Partita}</div>
        <div>⭐ <b>{r.Indice}/100</b> &nbsp; • &nbsp; 🎯 <b>{r.Segnale}</b></div>
        <div class="muted">1 {r['1']:.0f}% &nbsp; X {r['X']:.0f}% &nbsp; 2 {r['2']:.0f}%</div>
        </div>""",unsafe_allow_html=True)

    st.divider()
    opts=[f"{i+1}. {r.Partita}" for i,r in df.iterrows()]
    choice=st.selectbox("📌 Apri analisi completa",opts)
    r=df.iloc[opts.index(choice)]

    st.header(r.Partita)
    c1,c2,c3=st.columns(3)
    c1.metric("1",f"{r['1']:.0f}%");c2.metric("X",f"{r['X']:.0f}%");c3.metric("2",f"{r['2']:.0f}%")
    st.metric("⭐ Indice Match",f"{r.Indice}/100")

    tabs=st.tabs(["📈 Analisi","📊 Statistiche","🆚 H2H","🏥 Assenze","💰 Quote"])
    with tabs[0]:
        p=api("predictions",{"fixture":int(r.Fixture)},api_key)
        if p:
            x=p[0].get("predictions",{})
            st.write("**Indicazione API:**",x.get("advice","—"))
            st.write("**Gol previsti:**",x.get("goals",{}).get("home","—"),"—",x.get("goals",{}).get("away","—"))
            st.write("**Under/Over:**",x.get("under_over","—"))
            st.write("**Forma:**",x.get("form","—"))
    with tabs[1]:
        s=api("fixtures/statistics",{"fixture":int(r.Fixture)},api_key)
        if s:
            rows2=[]
            for t in s:
                d={"Squadra":t["team"]["name"]}
                d.update({x["type"]:x["value"] for x in t.get("statistics",[])})
                rows2.append(d)
            st.dataframe(pd.DataFrame(rows2),use_container_width=True,hide_index=True)
        else: st.info("Non disponibili.")
    with tabs[2]:
        h=api("fixtures/headtohead",{"h2h":f"{int(r.HomeID)}-{int(r.AwayID)}","last":10},api_key)
        if h:
            st.dataframe(pd.DataFrame([{"Data":x["fixture"]["date"][:10],"Casa":x["teams"]["home"]["name"],
              "Risultato":f'{x["goals"]["home"]}-{x["goals"]["away"]}',"Trasferta":x["teams"]["away"]["name"]} for x in h]),
                         use_container_width=True,hide_index=True)
        else: st.info("Non disponibili.")
    with tabs[3]:
        inj=api("injuries",{"fixture":int(r.Fixture)},api_key)
        if inj: st.dataframe(pd.DataFrame([{"Giocatore":x["player"]["name"],"Squadra":x["team"]["name"],"Motivo":x["player"].get("reason","")} for x in inj]),use_container_width=True,hide_index=True)
        else: st.info("Nessuna assenza restituita.")
    with tabs[4]:
        odds=api("odds",{"fixture":int(r.Fixture)},api_key)
        st.json(odds if odds else {"info":"Quote non disponibili."})

st.divider()
st.caption("⚠️ Le percentuali sono statistiche, non garanzie di risultato.")
