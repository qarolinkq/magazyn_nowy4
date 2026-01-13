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
        st.error(f"Szczegóły błędu: {e}")
        return None

# --- KATEGORIE ---
st.header("1. Kategorie")
nazwa_kat = st.text_input("Nazwa nowej kategorii")
if st.button("Dodaj Kategorię"):
    if nazwa_kat:
        # Zmieniono na 'Kategorie' (wielka litera)
        safe_execute(lambda: supabase.table("Kategorie").insert({"nazwa": nazwa_kat}).execute())
        st.success(f"Dodano kategorię: {nazwa_kat}")
        st.rerun()

# --- PRODUKTY ---
st.divider()
st.header("2. Produkty")

# Pobieranie kategorii (Wielka litera)
kat_data = safe_execute(lambda: supabase.table("Kategorie").select("*").execute())
kategorie = kat_data.data if kat_data else []

if kategorie:
    kat_dict = {k['nazwa']: k['id'] for k in kategorie}
    
    with st.form("produkt_form"):
        nazwa_p = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Liczba", step=1, value=0)
        
        # UWAGA: Na Twoim schemacie kolumna to "Ce..." (prawdopodobnie "Cena")
        # Jeśli dostaniesz błąd 'column "Cena" does not exist', sprawdź pisownię w Supabase
        cena = st.number_input("Cena", format="%.2f", value=0.0)
        
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        submit = st.form_submit_button("Dodaj Produkt")
        
        if submit:
            nowy_produkt = {
                "nazwa": nazwa_p,
                "liczba": ilosc,
                "Cena": cena,  # Zakładam, że pełna nazwa to "Cena"
                "kategoria_id": kat_dict[wybrana_kat]
            }
            # Zmieniono na 'Produkty' (wielka litera)
            res = safe_execute(lambda: supabase.table("Produkty").insert(nowy_produkt).execute())
            if res:
                st.success("Produkt dodany!")
                st.rerun()
else:
    st.warning("Najpierw dodaj kategorię.")

# --- LISTA I USUWANIE ---
st.divider()
st.subheader("Lista produktów")
