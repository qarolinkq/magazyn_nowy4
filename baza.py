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
        # Pobieramy wszystko bez sztywnego sortowania w SQL, by uniknąć błędów wielkości liter
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
    # Sortujemy produkty w Pythonie, aby mieć pewność, że nazwa nie zniknie z widoku
    posortowane = sorted(produkty, key=lambda x: str(x.get('nazwa') or x.get('Nazwa') or "").lower())

    for p in posortowane:
        # --- POBIERANIE NAZWY ---
        nazwa_p = p.get('nazwa') or p.get('Nazwa') or p.get('name') or "BEZ NAZWY"
        
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
                        
                        if st.button("🗑️ Usuń", key=f"d_{p['id']}", use_container_width=True, type="secondary"):
                            supabase.table("produkty").delete().eq("id", p['id']).execute()
                            st.rerun()
                st.divider()
    
    if not znaleziono:
        st.info("Brak produktów.")

# ================== TAB 3 — DODAJ PRODUKT (NAPRAWIONY) ==================
with tab3:
    st.subheader("Nowy towar")
    # USUNIĘTO clear_on_submit, aby zapobiec znikania nazwy przed zapisem
    with st.form("form_dodaj_v3", clear_on_submit=False):
        ca, cb = st.columns(2)
        with ca:
            f_nazwa = st.text_input("Nazwa produktu (wymagane)*")
            f_ilosc = st.number_input("Ilość początkowa", min_value=0, value=0)
            f_cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
        with cb:
            f_min = st.number_input("Próg alarmowy", min_value=0, value=5)
            # Obsługa błędu jeśli nie ma kategorii
            opcje_kat = list(kat_nazwa_na_id.keys()) if kat_nazwa_na_id else ["Brak kategorii"]
            f_kat = st.selectbox("Kategoria", opcje_kat)
        
        # Przycisk wysyłania
        zapisz = st.form_submit_button("✅ Zapisz produkt w magazynie")
        
        if zapisz:
            czysta_nazwa = f_nazwa.strip()
            if not czysta_nazwa:
                st.error("❌ BŁĄD: Nazwa produktu nie może być pusta!")
            elif not kat_nazwa_na_id:
                st.error("❌ BŁĄD: Musisz najpierw dodać kategorię!")
            else:
                try:
                    # Wysyłamy dane jawnie przypisane do zmiennych
                    nowy_rekord = {
                        "nazwa": czysta_nazwa,
                        "liczba": f_ilosc,
                        "cena": f_cena,
                        "kategoria_id": kat_nazwa_na_id[f_kat],
                        "minimum": f_min
                    }
                    supabase.table("produkty").insert(nowy_rekord).execute()
                    st.success(f"✅ Dodano produkt: {czysta_nazwa}")
                    # Odświeżamy stronę, co wyczyści formularz i pokaże produkt w magazynie
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Błąd zapisu: {e}")

# ================== TAB 2 & 4 (PODSTAWOWE) ==================
with tab2:
    st.subheader("Analityka")
    total_val = sum((p.get('liczba', 0) or 0) * (p.get('cena', 0.0) or 0.0) for p in produkty)
    st.metric("Wartość magazynu", f"{total_val:,.2f} zł")
    # Prosty wykres
    if produkty:
        wykres_data = {}
        for p in produkty:
            kn = kat_id_na_nazwe.get(p.get('kategoria_id'), "Inne")
            wykres_data[kn] = wykres_data.get(kn, 0) + ((p.get('liczba', 0) or 0) * (p.get('cena', 0.0) or 0.0))
        st.bar_chart(wykres_data)

with tab4:
    st.subheader("Zarządzanie kategoriami")
    with st.form("add_k_safe"):
        kn = st.text_input("Nazwa nowej kategorii")
        ko = st.text_area("Opis")
        if st.form_submit_button("Dodaj"):
            if kn.strip():
                supabase.table("kategorie").insert({"nazwa": kn.strip(), "opis": ko}).execute()
                st.rerun()
