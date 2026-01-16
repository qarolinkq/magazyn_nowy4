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
        # Pobieramy produkty i kategorie
        produkty = supabase.table("produkty").select("*").execute().data
        kategorie = supabase.table("kategorie").select("*").execute().data
        return produkty, kategorie
    except Exception:
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
    # Sortowanie produktów ręcznie w Pythonie dla pewności
    produkty_posortowane = sorted(produkty, key=lambda x: (x.get('nazwa') or "").lower())

    for p in produkty_posortowane:
        # WYŚWIETLANIE NAZWY - sprawdzamy wszystkie opcje
        nazwa_p = p.get('nazwa') or p.get('Nazwa') or "PRODUKT BEZ NAZWY"
        
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
                        # Główne wyświetlanie nazwy
                        t_color = "#FF4B4B" if is_low else "#FAFAFA"
                        st.markdown(f"### <span style='color:{t_color}'>{nazwa_p}</span>", unsafe_allow_html=True)
                        st.write(f"**Stan:** `{obecny_stan} szt.` | **Min:** {min_stan} | **Cena:** {cena_p} zł")
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
                st.divider()

# ================== TAB 3 — DODAJ PRODUKT (POPRAWIONY) ==================
with tab3:
    st.subheader("Nowy towar")
    # Formularz bez clear_on_submit, żeby mieć pewność, że dane nie znikną przed zapisem
    with st.form("form_add_v2"):
        ca, cb = st.columns(2)
        with ca:
            f_nazwa = st.text_input("Nazwa produktu*")
            f_ilosc = st.number_input("Ilość", min_value=0, value=0)
            f_cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
        with cb:
            f_min = st.number_input("Próg alarmowy", min_value=0, value=5)
            f_kat = st.selectbox("Kategoria", list(kat_nazwa_na_id.keys()))
        
        submit = st.form_submit_button("Zapisz produkt")
        
        if submit:
            # Bardzo ważne: sprawdzamy czy nazwa nie jest pusta
            nazwa_do_zapisu = f_nazwa.strip()
            if nazwa_do_zapisu:
                try:
                    data = {
                        "nazwa": nazwa_do_zapisu,
                        "liczba": f_ilosc,
                        "cena": f_cena,
                        "kategoria_id": kat_nazwa_na_id[f_kat],
                        "minimum": f_min
                    }
                    res = supabase.table("produkty").insert(data).execute()
                    if res.data:
                        st.success(f"Pomyślnie dodano produkt: {nazwa_do_zapisu}")
                        st.rerun()
                    else:
                        st.error("Baza danych nie zwróciła potwierdzenia zapisu.")
                except Exception as e:
                    st.error(f"Błąd podczas zapisu: {e}")
            else:
                st.warning("Musisz podać nazwę produktu przed zapisem!")

# ================== TAB 2 i 4 (BEZ ZMIAN) ==================
with tab2:
    if produkty:
        total_val = sum((p.get('liczba', 0) or 0) * (p.get('cena', 0.0) or 0.0) for p in produkty)
        st.metric("Wartość magazynu", f"{total_val:,.2f} zł")
        wykres_data = {}
        for p in produkty:
            k_n = kat_id_na_nazwe.get(p.get('kategoria_id'), "Inne")
            wartość = (p.get('liczba', 0) or 0) * (p.get('cena', 0.0) or 0.0)
            wykres_data[k_n] = wykres_data.get(k_n, 0) + wartość
        st.bar_chart(wykres_data)

with tab4:
    st.subheader("Dodaj nową kategorię")
    with st.form("kat_add"):
        kn = st.text_input("Nazwa kategorii")
        ko = st.text_area("Opis")
        if st.form_submit_button("Dodaj"):
            if kn:
                supabase.table("kategorie").insert({"nazwa": kn, "opis": ko}).execute()
                st.rerun()
