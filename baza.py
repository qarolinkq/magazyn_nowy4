import streamlit as st
from supabase import create_client, Client

# ================== KONFIGURACJA ==================
st.set_page_config(page_title="☁️ System Chmurka PRO", layout="wide")

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"❌ Brak połączenia z Supabase: {e}")
        return None

supabase = init_connection()
if not supabase: st.stop()

# ================== FUNKCJE ==================
def pobierz_dane():
    try:
        produkty = supabase.table("produkty").select("*").order("nazwa").execute().data
        kategorie = supabase.table("kategorie").select("*").order("nazwa").execute().data
        return produkty, kategorie
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return [], []

def zmien_stan(id_produktu, nowy_stan):
    supabase.table("produkty").update({"liczba": max(0, nowy_stan)}).eq("id", id_produktu).execute()
    st.rerun()

# ================== DANE ==================
produkty, kategorie = pobierz_dane()
kat_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie}
kat_nazwa_na_id = {k["nazwa"]: k["id"] for k in kategorie}

# ================== UI ==================
st.title("☁️ System magazynowy Chmurka PRO")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Magazyn", "📊 Statystyki & Wykresy", "➕ Dodaj produkt", "📂 Kategorie"])

# ================== TAB 1 — MAGAZYN ==================
with tab1:
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Szukaj produktu...", "").lower()
    with col_filter:
        pokaz_braki = st.toggle("⚠️ Pokaż tylko braki")

    st.divider()

    filtrowane = [
        p for p in produkty 
        if (search_query in p['nazwa'].lower() or search_query in kat_id_na_nazwe.get(p['kategoria_id'], "").lower())
        and (not pokaz_braki or p['liczba'] <= p.get('minimum', 0))
    ]

    if not filtrowane:
        st.info("Brak produktów spełniających kryteria.")
    else:
        for p in filtrowane:
            min_stan = p.get('minimum', 0)
            is_low = p['liczba'] <= min_stan
            
            with st.container():
                c1, c2 = st.columns([2, 1])
                with c1:
                    t_color = "#FF4B4B" if is_low else "#FFFFFF"
                    st.markdown(f"### <span style='color:{t_color}'>{'⚠️ ' if is_low else ''}{p['nazwa']}</span>", unsafe_allow_html=True)
                    st.write(f"**Stan:** `{p['liczba']} szt.` | **Minimum:** {min_stan}")
                    st.caption(f"Kategoria: {kat_id_na_nazwe.get(p['kategoria_id'], '—')} | Cena: {p['cena']} zł")
                
                with c2:
                    # Pole ilości i przyciski w jednym bloku
                    val = st.number_input("Ilość", min_value=1, value=1, key=f"v_{p['id']}", label_visibility="collapsed")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("➕ Dodaj", key=f"a_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], p["liczba"] + val)
                    with b2:
                        if st.button("➖ Odejmij", key=f"s_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], p["liczba"] - val)
                    
                    if st.button("🗑️ Usuń", key=f"d_{p['id']}", use_container_width=True, type="secondary"):
                        supabase.table("produkty").delete().eq("id", p['id']).execute()
                        st.rerun()
            st.divider()

# ================== TAB 2 — ANALITYKA ==================
with tab2:
    st.subheader("Analityka zapasów")
    
    if not produkty:
        st.info("Brak danych do analizy.")
    else:
        total_val = sum(p['liczba'] * p['cena'] for p in produkty)
        total_items = sum(p['liczba'] for p in produkty)
        braki_lista = [p for p in produkty if p['liczba'] <= p.get('minimum', 0)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Wartość magazynu", f"{total_val:,.2f} zł")
        m2.metric("Suma sztuk", f"{total_items} szt.")
        m3.metric("Krytyczne braki", len(braki_lista))

        st.divider()
        
        col_chart, col_list = st.columns([2, 1])
        with col_chart:
            st.write("### Wartość towaru w kategoriach")
            wykres_data = {}
            for p in produkty:
                kat_n = kat_id_na_nazwe.get(p['kategoria_id'], "Nieprzypisane")
                wykres_data[kat_n] = wykres_data.get(kat_n, 0) + (p['liczba'] * p['cena'])
            st.bar_chart(wykres_data)
        
        with col_list:
            st.write("### 🚨 Lista braków")
            for b in braki_lista:
                st.error(f"**{b['nazwa']}** (Stan: {b['liczba']})")

# ================== TAB 3 — DODAJ PRODUKT (BEZPIECZNY) ==================
with tab3:
    st.subheader("Nowy produkt")
    with st.form("safe_add_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            nowa_nazwa = st.text_input("Nazwa produktu*")
            nowa_ilosc = st.number_input("Ilość", min_value=0, value=0)
            nowa_cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
        with col_b:
            nowe_min = st.number_input("Minimum (Alert)", min_value=0, value=5)
            wybrana_kat = st.selectbox("Kategoria", list(kat_nazwa_na_id.keys()))
        
        if st.form_submit_button("Zapisz produkt"):
            if not nowa_nazwa:
                st.warning("Podaj nazwę produktu!")
            else:
                try:
                    dane_do_wyslania = {
                        "nazwa": nowa_nazwa,
                        "liczba": nowa_ilosc,
                        "cena": nowa_cena,
                        "kategoria_id": kat_nazwa_na_id[wybrana_kat],
                        "minimum": nowe_min # Upewnij się, że ta kolumna jest w Supabase!
                    }
                    supabase.table("produkty").insert(dane_do_wyslania).execute()
                    st.success("Dodano produkt!")
                    st.rerun()
                except Exception as e:
                    st.error("❌ Błąd zapisu!")
                    st.info("Prawdopodobna przyczyna: brak kolumny 'minimum' w tabeli 'produkty' w Supabase.")
                    st.code("Wejdź w Supabase -> Table Editor -> produkty -> Add Column -> Name: 'minimum', Type: 'int8', Default: 0")

# ================== TAB 4 — KATEGORIE ==================
with tab4:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Twoje kategorie")
        for kat in kategorie:
            with st.expander(f"📂 {kat['nazwa']}"):
                st.write(kat['opis'])
                if st.button("Usuń", key=f"dk_{kat['id']}"):
                    supabase.table("kategorie").delete().eq("id", kat['id']).execute()
                    st.rerun()
    with col_r:
        st.subheader("Dodaj kategorię")
        with st.form("add_k"):
            nk = st.text_input("Nazwa")
            ok = st.text_area("Opis")
            if st.form_submit_button("Dodaj"):
                if nk:
                    supabase.table("kategorie").insert({"nazwa": nk, "opis": ok}).execute()
                    st.rerun()
