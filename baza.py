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
        return [], []

def zmien_stan(id_produktu, nowy_stan):
    # max(0, ...) zapobiega stanom ujemnym
    supabase.table("produkty").update({"liczba": max(0, nowy_stan)}).eq("id", id_produktu).execute()
    st.rerun()

# ================== PRZYGOTOWANIE DANYCH ==================
produkty, kategorie = pobierz_dane()
kat_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie}
kat_nazwa_na_id = {k["nazwa"]: k["id"] for k in kategorie}

# ================== UI ==================
st.title("☁️ System magazynowy Chmurka PRO")

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Magazyn", 
    "📊 Statystyki & Wykresy", 
    "➕ Dodaj produkt", 
    "📂 Kategorie"
])

# ================== TAB 1 — MAGAZYN ==================
with tab1:
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Szukaj produktu lub kategorii...", "").lower()
    with col_filter:
        pokaz_braki = st.toggle("⚠️ Pokaż tylko braki (poniżej minimum)")

    st.divider()

    # Filtrowanie i renderowanie
    znaleziono = False
    for p in produkty:
        # BEZPIECZNE POBIERANIE (Rozwiązuje TypeError)
        nazwa_p = p.get('nazwa') or "Produkt bez nazwy"
        obecny_stan = p.get('liczba') if p.get('liczba') is not None else 0
        min_stan = p.get('minimum') if p.get('minimum') is not None else 0
        cena_p = p.get('cena') if p.get('cena') is not None else 0.0
        kat_nazwa = kat_id_na_nazwe.get(p.get('kategoria_id'), "Brak kategorii")

        is_low = obecny_stan <= min_stan
        
        # Logika wyszukiwarki
        if (search_query in nazwa_p.lower() or search_query in kat_nazwa.lower()):
            if not pokaz_braki or is_low:
                znaleziono = True
                with st.container():
                    c1, c2 = st.columns([2, 1])
                    
                    with c1:
                        t_color = "#FF4B4B" if is_low else "#FAFAFA"
                        st.markdown(f"### <span style='color:{t_color}'>{'⚠️ ' if is_low else ''}{nazwa_p}</span>", unsafe_allow_html=True)
                        st.write(f"**Stan:** `{obecny_stan} szt.` | **Próg min:** {min_stan}")
                        st.caption(f"Kategoria: {kat_nazwa} | Cena jedn.: {cena_p} zł")
                        st.write(f"Wartość pozycji: **{round(obecny_stan * cena_p, 2)} zł**")

                    with c2:
                        # Pole ilości
                        zmiana = st.number_input("Ilość", min_value=1, value=1, key=f"v_{p['id']}", label_visibility="collapsed")
                        
                        # Przyciski pod polem ilości
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("➕ Dodaj", key=f"a_{p['id']}", use_container_width=True):
                                zmien_stan(p["id"], obecny_stan + zmiana)
                        with b2:
                            if st.button("➖ Odejmij", key=f"s_{p['id']}", use_container_width=True):
                                zmien_stan(p["id"], obecny_stan - zmiana)
                        
                        # Przycisk usuwania
                        if st.button("🗑️ Usuń produkt", key=f"d_{p['id']}", use_container_width=True, type="secondary"):
                            supabase.table("produkty").delete().eq("id", p['id']).execute()
                            st.rerun()
                st.divider()
    
    if not znaleziono:
        st.info("Nie znaleziono produktów spełniających kryteria.")

# ================== TAB 2 — STATYSTYKI ==================
with tab2:
    st.subheader("Analityka finansowa magazynu")
    
    if produkty:
        # Bezpieczne obliczenia sum
        total_val = sum((p.get('liczba', 0) or 0) * (p.get('cena', 0.0) or 0.0) for p in produkty)
        total_qty = sum(p.get('liczba', 0) or 0 for p in produkty)
        produkty_braki = [p for p in produkty if (p.get('liczba', 0) or 0) <= (p.get('minimum', 0) or 0)]

        m1, m2, m3 = st.columns(3)
        m1.metric("Wartość całkowita", f"{total_val:,.2f} zł")
        m2.metric("Liczba wszystkich sztuk", f"{total_qty} szt.")
        m3.metric("Pozycje do zamówienia", len(produkty_braki))

        st.divider()

        col_ch, col_li = st.columns([2, 1])
        with col_ch:
            st.write("### Wartość towaru per kategoria")
            wykres_data = {}
            for p in produkty:
                k_n = kat_id_na_nazwe.get(p.get('kategoria_id'), "Inne")
                wartość = (p.get('liczba', 0) or 0) * (p.get('cena', 0.0) or 0.0)
                wykres_data[k_n] = wykres_data.get(k_n, 0) + wartość
            st.bar_chart(wykres_data)
        
        with col_li:
            st.write("### 🚨 Krytyczne braki")
            for b in produkty_braki:
                st.error(f"**{b.get('nazwa')}** (Stan: {b.get('liczba')})")
    else:
        st.info("Brak danych do wygenerowania statystyk.")

# ================== TAB 3 — DODAJ PRODUKT ==================
with tab3:
    st.subheader("Dodaj nowy towar do bazy")
    if not kategorie:
        st.warning("Najpierw musisz dodać kategorię w zakładce 'Kategorie'.")
    else:
        with st.form("form_dodaj_nowy", clear_on_submit=True):
            ca, cb = st.columns(2)
            with ca:
                n_nazwa = st.text_input("Nazwa produktu*")
                n_ilosc = st.number_input("Ilość na start", min_value=0, value=0)
                n_cena = st.number_input("Cena zakupu (zł)", min_value=0.0, step=0.01)
            with cb:
                n_min = st.number_input("Minimum (Alert)", min_value=0, value=5)
                n_kat = st.selectbox("Kategoria", list(kat_nazwa_na_id.keys()))
            
            if st.form_submit_button("✅ Dodaj produkt do magazynu"):
                if n_nazwa.strip():
                    try:
                        supabase.table("produkty").insert({
                            "nazwa": n_nazwa.strip(),
                            "liczba": n_ilosc,
                            "cena": n_cena,
                            "kategoria_id": kat_nazwa_na_id[n_kat],
                            "minimum": n_min
                        }).execute()
                        st.success("Produkt został dodany!")
                        st.rerun()
                    except Exception as e:
                        st.error("Błąd bazy danych. Sprawdź czy kolumna 'minimum' istnieje.")
                else:
                    st.error("Nazwa produktu jest wymagana!")

# ================== TAB 4 — KATEGORIE ==================
with tab4:
    cl, cr = st.columns(2)
    with cl:
        st.subheader("Lista kategorii")
        for k in kategorie:
            with st.expander(f"📂 {k['nazwa']}"):
                st.write(k.get('opis', 'Brak opisu'))
                if st.button("Usuń", key=f"del_k_{k['id']}"):
                    # Sprawdzenie czy kategoria jest pusta
                    ma_produkty = any(p.get('kategoria_id') == k['id'] for p in produkty)
                    if ma_produkty:
                        st.error("Nie można usunąć kategorii, która zawiera produkty!")
                    else:
                        supabase.table("kategorie").delete().eq("id", k['id']).execute()
                        st.rerun()
    with cr:
        st.subheader("Dodaj kategorię")
        with st.form("form_kat"):
            kn = st.text_input("Nazwa")
            ko = st.text_area("Opis")
            if st.form_submit_button("Zapisz kategorię"):
                if kn:
                    supabase.table("kategorie").insert({"nazwa": kn, "opis": ko}).execute()
                    st.rerun()
