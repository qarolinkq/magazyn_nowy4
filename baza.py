import streamlit as st
from supabase import create_client, Client

# ================== KONFIGURACJA ==================
st.set_page_config(
    page_title="☁️ System Chmurka PRO",
    layout="wide"
)

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Brak połączenia z Supabase: {e}")
        return None

supabase = init_connection()
if not supabase:
    st.stop()

# ================== FUNKCJE ==================
def pobierz_dane():
    try:
        produkty = supabase.table("produkty").select("*").order("nazwa").execute().data
        kategorie = supabase.table("kategorie").select("*").order("nazwa").execute().data
        return produkty, kategorie
    except Exception:
        # Próba pobrania bez sortowania, jeśli kolumna 'nazwa' ma inną wielkość liter
        try:
            produkty = supabase.table("produkty").select("*").execute().data
            kategorie = supabase.table("kategorie").select("*").execute().data
            return produkty, kategorie
        except:
            return [], []

def zmien_stan(id_produktu, nowy_stan):
    supabase.table("produkty").update({"liczba": max(0, nowy_stan)}).eq("id", id_produktu).execute()
    st.rerun()

# ================== PRZYGOTOWANIE DANYCH ==================
produkty, kategorie = pobierz_dane()
kat_id_na_nazwe = {k.get("id"): k.get("nazwa") or k.get("Nazwa") for k in kategorie}
kat_nazwa_na_id = {k.get("nazwa") or k.get("Nazwa"): k.get("id") for k in kategorie}

# ================== UI ==================
st.title("☁️ System magazynowy Chmurka PRO")

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Magazyn", 
    "📊 Statystyki", 
    "➕ Dodaj produkt", 
    "📂 Kategorie"
])

# ================== TAB 1 — MAGAZYN ==================
with tab1:
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Szukaj produktu...", "").lower()
    with col_filter:
        pokaz_braki = st.toggle("⚠️ Pokaż tylko braki")

    st.divider()

    znaleziono = False
    for p in produkty:
        # --- POPRAWKA WYŚWIETLANIA NAZWY ---
        # Sprawdzamy różne możliwe klucze (nazwa, Nazwa, name)
        nazwa_p = p.get('nazwa') or p.get('Nazwa') or p.get('name') or "Nieznany produkt"
        
        obecny_stan = p.get('liczba') if p.get('liczba') is not None else 0
        min_stan = p.get('minimum') if p.get('minimum') is not None else 0
        cena_p = p.get('cena') if p.get('cena') is not None else 0.0
        kat_nazwa = kat_id_na_nazwe.get(p.get('kategoria_id'), "Brak kategorii")

        is_low = obecny_stan <= min_stan
        
        if (search_query in nazwa_p.lower() or search_query in kat_nazwa.lower()):
            if not pokaz_braki or is_low:
                znaleziono = True
                with st.container():
                    c1, c2 = st.columns([2, 1])
                    
                    with c1:
                        t_color = "#FF4B4B" if is_low else "#FAFAFA"
                        # WYRAŹNY NAGŁÓWEK Z NAZWĄ
                        st.markdown(f"### <span style='color:{t_color}'>{nazwa_p}</span>", unsafe_allow_html=True)
                        
                        col_stats1, col_stats2 = st.columns(2)
                        with col_stats1:
                            st.write(f"**Stan:** `{obecny_stan} szt.`")
                            st.write(f"**Minimum:** {min_stan}")
                        with col_stats2:
                            st.write(f"**Cena:** {cena_p} zł")
                            st.write(f"**Wartość:** {round(obecny_stan * cena_p, 2)} zł")
                        
                        st.caption(f"Kategoria: {kat_nazwa}")

                    with c2:
                        zmiana = st.number_input("Ilość", min_value=1, value=1, key=f"v_{p['id']}", label_visibility="collapsed")
                        
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("➕ Dodaj", key=f"a_{p['id']}", use_container_width=True):
                                zmien_stan(p["id"], obecny_stan + zmiana)
                        with b2:
                            if st.button("➖ Odejmij", key=f"s_{p['id']}", use_container_width=True):
                                zmien_stan(p["id"], obecny_stan - zmiana)
                        
                        if st.button("🗑️ Usuń", key=f"d_{p['id']}", use_container_width=True, type="secondary"):
                            supabase.table("produkty").delete().eq("id", p['id']).execute()
                            st.rerun()
                st.divider()
    
    if not znaleziono:
        st.info("Brak produktów.")

# ================== TAB 2 — STATYSTYKI ==================
with tab2:
    st.subheader("Analityka")
    if produkty:
        total_val = sum((p.get('liczba', 0) or 0) * (p.get('cena', 0.0) or 0.0) for p in produkty)
        st.metric("Całkowita wartość magazynu", f"{total_val:,.2f} zł")
        
        # Wykres
        wykres_data = {}
        for p in produkty:
            k_n = kat_id_na_nazwe.get(p.get('kategoria_id'), "Inne")
            wartość = (p.get('liczba', 0) or 0) * (p.get('cena', 0.0) or 0.0)
            wykres_data[k_n] = wykres_data.get(k_n, 0) + wartość
        st.bar_chart(wykres_data)

# ================== TAB 3 — DODAJ PRODUKT ==================
with tab3:
    st.subheader("Nowy towar")
    with st.form("form_add", clear_on_submit=True):
        ca, cb = st.columns(2)
        with ca:
            n_nazwa = st.text_input("Nazwa produktu*")
            n_ilosc = st.number_input("Ilość", min_value=0, value=0)
            n_cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
        with cb:
            n_min = st.number_input("Próg alarmowy", min_value=0, value=5)
            n_kat = st.selectbox("Kategoria", list(kat_nazwa_na_id.keys()))
        
        if st.form_submit_button("Zapisz produkt"):
            if n_nazwa:
                supabase.table("produkty").insert({
                    "nazwa": n_nazwa,
                    "liczba": n_ilosc,
                    "cena": n_cena,
                    "kategoria_id": kat_nazwa_na_id[n_kat],
                    "minimum": n_min
                }).execute()
                st.success(f"Dodano: {n_nazwa}")
                st.rerun()

# ================== TAB 4 — KATEGORIE ==================
with tab4:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Kategorie")
        for k in kategorie:
            with st.expander(f"📂 {k.get('nazwa') or k.get('Nazwa')}"):
                st.write(k.get('opis', 'Brak opisu'))
                if st.button("Usuń", key=f"del_k_{k['id']}"):
                    supabase.table("kategorie").delete().eq("id", k['id']).execute()
                    st.rerun()
    with col_r:
        st.subheader("Dodaj")
        with st.form("add_k"):
            kn = st.text_input("Nazwa")
            ko = st.text_area("Opis")
            if st.form_submit_button("Dodaj kategorię"):
                if kn:
                    supabase.table("kategorie").insert({"nazwa": kn, "opis": ko}).execute()
                    st.rerun()
