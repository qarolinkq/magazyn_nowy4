import streamlit as st
from supabase import create_client, Client

# ================== KONFIGURACJA ==================
st.set_page_config(
    page_title="☁️ System magazynowy Chmurka",
    layout="wide"
)

# Inicjalizacja połączenia
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Błąd połączenia: {e}")
        return None

supabase = init_connection()

if not supabase:
    st.stop()

# ================== FUNKCJE OPERACYJNE ==================

def pobierz_dane():
    # Dodajemy order, żeby lista nie skakała przy każdej aktualizacji
    produkty = supabase.table("produkty").select("*").order("nazwa").execute().data
    kategorie = supabase.table("kategorie").select("*").order("nazwa").execute().data
    return produkty, kategorie

def zmien_stan(id_produktu, nowy_stan):
    supabase.table("produkty").update({"liczba": max(0, nowy_stan)}).eq("id", id_produktu).execute()
    st.rerun()

def usun_produkt(id_produktu):
    supabase.table("produkty").delete().eq("id", id_produktu).execute()
    st.rerun()

# ================== POBIERANIE DANYCH ==================
# Pobieramy dane na początku każdego odświeżenia strony
produkty, kategorie = pobierz_dane()
kat_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie}
kat_nazwa_na_id = {k["nazwa"]: k["id"] for k in kategorie}

# ================== INTERFEJS UŻYTKOWNIKA ==================
st.title("☁️ System magazynowy Chmurka")

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Magazyn", 
    "📊 Statystyki",
    "➕ Dodaj produkt", 
    "📂 Kategorie"
])

# ================== TAB 1 — MAGAZYN ==================
with tab1:
    search_query = st.text_input("🔍 Wyszukiwarka (nazwa produktu lub kategorii)", "").lower()
    
    # Filtrowanie w locie
    filtrowane = [
        p for p in produkty 
        if search_query in p['nazwa'].lower() or 
        search_query in kat_id_na_nazwe.get(p['kategoria_id'], "").lower()
    ]

    if not filtrowane:
        st.info("Brak produktów do wyświetlenia.")
    else:
        for p in filtrowane:
            # Kontener dla każdego produktu
            with st.container():
                col_info, col_actions = st.columns([2, 1])
                
                with col_info:
                    st.subheader(p['nazwa'])
                    st.write(f"**Stan:** `{p['liczba']} szt.` | **Cena:** {p['cena']} zł")
                    st.write(f"**Wartość:** {round(p['liczba'] * p['cena'], 2)} zł")
                    st.caption(f"Kategoria: {kat_id_na_nazwe.get(p['kategoria_id'], 'Brak')}")

                with col_actions:
                    # Pole ilości (bezpośrednio nad przyciskami)
                    ilosc_zmiany = st.number_input(
                        "Ile sztuk?", min_value=1, value=1, 
                        key=f"val_{p['id']}"
                    )
                    
                    # Przyciski DODAJ / ODEJMIJ (w jednym rzędzie pod polem)
                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if st.button("➕ Dodaj", key=f"add_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], p["liczba"] + ilosc_zmiany)
                    with b_col2:
                        if st.button("➖ Odejmij", key=f"sub_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], p["liczba"] - ilosc_zmiany)
                    
                    # Opcje dodatkowe
                    exp = st.expander("Opcje usuwania")
                    with exp:
                        if st.button("🔄 Wyzeruj stan", key=f"reset_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], 0)
                        if st.button("🗑️ Usuń produkt", key=f"del_{p['id']}", use_container_width=True, type="primary"):
                            usun_produkt(p["id"])
                
                st.divider()

# ================== TAB 2 — STATYSTYKI ==================
with tab2:
    st.header("Podsumowanie finansowe")
    total_val = sum(p['liczba'] * p['cena'] for p in produkty)
    total_qty = sum(p['liczba'] for p in produkty)
    
    c1, c2 = st.columns(2)
    c1.metric("Łączna wartość magazynu", f"{total_val:,.2f} zł")
    c2.metric("Suma wszystkich sztuk", f"{total_qty} szt.")

    if produkty:
        # Prosty wykres wartości per kategoria
        wykres_data = {}
        for p in produkty:
            kat_n = kat_id_na_nazwe.get(p['kategoria_id'], "Nieprzypisane")
            wykres_data[kat_n] = wykres_data.get(kat_n, 0) + (p['liczba'] * p['cena'])
        st.bar_chart(wykres_data)

# ================== TAB 3 — DODAJ PRODUKT ==================
with tab3:
    st.subheader("Dodawanie nowego produktu")
    if not kategorie:
        st.error("Musisz najpierw dodać przynajmniej jedną kategorię!")
    else:
        with st.form("form_dodaj_prod", clear_on_submit=True):
            nazwa = st.text_input("Nazwa produktu")
            ilosc = st.number_input("Ilość", min_value=0, value=0)
            cena = st.number_input("Cena za sztukę", min_value=0.0, step=0.01)
            kat_wybor = st.selectbox("Kategoria", list(kat_nazwa_na_id.keys()))
            
            if st.form_submit_button("Dodaj produkt"):
                if nazwa:
                    supabase.table("produkty").insert({
                        "nazwa": nazwa, "liczba": ilosc, 
                        "cena": cena, "kategoria_id": kat_nazwa_na_id[kat_wybor]
                    }).execute()
                    st.success("Dodano!")
                    st.rerun()
                else:
                    st.warning("Podaj nazwę!")

# ================== TAB 4 — KATEGORIE ==================
with tab4:
    st.subheader("Zarządzanie kategoriami")
    
    col_l, col_r = st.columns(2)
    
    with col_r:
        with st.form("form_kat", clear_on_submit=True):
            n_kat = st.text_input("Nazwa nowej kategorii")
            o_kat = st.text_area("Opis")
            if st.form_submit_button("Utwórz kategorię"):
                if n_kat:
                    supabase.table("kategorie").insert({"nazwa": n_kat, "opis": o_kat}).execute()
                    st.rerun()

    with col_l:
        for k in kategorie:
            with st.expander(f"📂 {k['nazwa']}"):
                st.write(k['opis'])
                if st.button("Usuń kategorię", key=f"del_kat_{k['id']}"):
                    # Sprawdź czy pusta
                    ma_produkty = any(p['kategoria_id'] == k['id'] for p in produkty)
                    if ma_produkty:
                        st.error("Kategoria nie jest pusta!")
                    else:
                        supabase.table("kategorie").delete().eq("id", k['id']).execute()
                        st.rerun()
