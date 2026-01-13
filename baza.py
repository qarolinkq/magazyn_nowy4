import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets!")
    st.stop()

st.title("📦 Panel Zarządzania Bazą")

# --- FUNKCJA POMOCNICZA ---
def safe_execute(query_func):
    try:
        return query_func()
    except Exception as e:
        st.error(f"Błąd bazy: {e}")
        return None

# --- 1. KATEGORIE ---
st.header("1. Kategorie")
nazwa_kat = st.text_input("Nazwa nowej kategorii", key="kat_input")
if st.button("Dodaj Kategorię"):
    if nazwa_kat:
        # Zgodnie z poprzednim błędem: 'kategorie' małymi literami
        safe_execute(lambda: supabase.table("kategorie").insert({"nazwa": nazwa_kat}).execute())
        st.success(f"Dodano: {nazwa_kat}")
        st.rerun()

st.divider()

# --- 2. PRODUKTY ---
st.header("2. Produkty")

# Pobieranie kategorii
kat_res = safe_execute(lambda: supabase.table("kategorie").select("*").execute())
kategorie = kat_res.data if kat_res else []

if kategorie:
    kat_dict = {k['nazwa']: k['id'] for k in kategorie}
    
    with st.form("produkt_form"):
        nazwa_p = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Liczba", min_value=0, step=1)
        # Sprawdź w Supabase czy kolumna to 'cena' czy 'Ce...'
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        submit = st.form_submit_button("Zapisz produkt")
        
        if submit:
            if nazwa_p:
                nowy_produkt = {
                    "nazwa": nazwa_p,
                    "liczba": ilosc,
                    "cena": cena, # Jeśli wywali błąd kolumny, zmień na "Ce..."
                    "kategoria_id": kat_dict[wybrana_kat]
                }
                # ZMIANA: 'Produkty' wielką literą zgodnie z błędem PGRST205
                res = safe_execute(lambda: supabase.table("Produkty").insert(nowy_produkt).execute())
                if res:
                    st.success("Dodano produkt!")
                    st.rerun()
            else:
                st.error("Podaj nazwę produktu!")
else:
    st.info("Baza kategorii jest pusta.")

# --- 3. LISTA I USUWANIE ---
st.divider()
st.subheader("Lista produktów")
# ZMIANA: 'Produkty' wielką literą
prod_res = safe_execute(lambda: supabase.table("Produkty").select("id, nazwa").execute())

if prod_res and prod_res.data:
    for p in prod_res.data:
        c1, c2 = st.columns([4, 1])
        c1.write(f"ID: {p['id']} | **{p['nazwa']}**")
        if c2.button("Usuń", key=f"del_{p['id']}"):
            # ZMIANA: 'Produkty' wielką literą
            safe_execute(lambda: supabase.table("Produkty").delete().eq("id", p['id']).execute())
            st.rerun()
