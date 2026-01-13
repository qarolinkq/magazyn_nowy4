import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets! Sprawdź ustawienia na Streamlit Cloud.")
    st.stop()

st.title("📦 Panel Zarządzania Bazą")

# --- FUNKCJA POMOCNICZA DO OBSŁUGI BŁĘDÓW ---
def safe_execute(query_func):
    try:
        return query_func()
    except Exception as e:
        # To wyciągnie prawdziwy powód błędu z Supabase
        st.error(f"Błąd bazy danych: {e}")
        return None

# --- KATEGORIE ---
st.header("1. Kategorie")
nazwa_kat = st.text_input("Nazwa nowej kategorii")
if st.button("Dodaj Kategorię"):
    if nazwa_kat:
        safe_execute(lambda: supabase.table("Kategorie").insert({"nazwa": nazwa_kat}).execute())
        st.rerun()

# --- PRODUKTY ---
st.divider()
st.header("2. Produkty")

# Pobieranie kategorii do listy (z obsługą błędów)
kat_data = safe_execute(lambda: supabase.table("Kategorie").select("*").execute())
kategorie = kat_data.data if kat_data else []

if kategorie:
    kat_dict = {k['nazwa']: k['id'] for k in kategorie}
    
    with st.form("produkt_form"):
        nazwa_p = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Liczba", step=1)
        # UWAGA: Sprawdź w Supabase czy ta kolumna to 'cena' czy 'Ce...'
        cena = st.number_input("Cena (numeryczne)", format="%.2f")
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        submit = st.form_submit_button("Dodaj Produkt")
        
        if submit:
            nowy_produkt = {
                "nazwa": nazwa_p,
                "liczba": ilosc,
                "cena": cena,  # ZMIANA: Sprawdź dokładną nazwę w Supabase!
                "kategoria_id": kat_dict[wybrana_kat]
            }
            res = safe_execute(lambda: supabase.table("Produkty").insert(nowy_produkt).execute())
            if res:
                st.success("Produkt dodany!")
                st.rerun()
else:
    st.warning("Najpierw dodaj kategorię, aby móc dodać produkty.")

# --- USUWANIE (Lista) ---
st.divider()
st.subheader("Lista produktów w bazie")
prod_data = safe_execute(lambda: supabase.table("Produkty").select("id, nazwa").execute())
if prod_data and prod_data.data:
    for p in prod_data.data:
        col1, col2 = st.columns([4, 1])
        col1.write(p['nazwa'])
        if col2.button("Usuń", key=f"del_{p['id']}"):
            safe_execute(lambda: supabase.table("Produkty").delete().eq("id", p['id']).execute())
            st.rerun()
