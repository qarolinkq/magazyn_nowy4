import streamlit as st
from supabase import create_client, Client

# 1. Konfiguracja połączenia z Supabase
try:
    # Dane pobierane z Settings -> Secrets w Streamlit Cloud
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets! Sprawdź czy dodałeś SUPABASE_URL i SUPABASE_KEY.")
    st.stop()

st.set_page_config(page_title="Magazyn Supabase", layout="centered")
st.title("📦 System Zarządzania Magazynem")

# --- FUNKCJA POMOCNICZA DO OBSŁUGI BŁĘDÓW ---
def safe_execute(query_func):
    try:
        return query_func()
    except Exception as e:
        st.error(f"Wystąpił błąd bazy danych: {e}")
        return None

# --- SEKCJA 1: KATEGORIE ---
st.header("1. Zarządzanie Kategoriami")

with st.expander("Dodaj nową kategorię"):
    nowa_kat_nazwa = st.text_input("Nazwa kategorii (np. Elektronika)")
    if st.button("Zapisz kategorię"):
        if nowa_kat_nazwa:
            # Używamy 'kategorie' (mała litera zgodnie z błędem PGRST205)
            safe_execute(lambda: supabase.table("kategorie").insert({"nazwa": nowa_kat_nazwa}).execute())
            st.success(f"Dodano kategorię: {nowa_kat_nazwa}")
            st.rerun()

st.divider()

# --- SEKCJA 2: PRODUKTY ---
st.header("2. Zarządzanie Produktami")

# Pobieramy aktualne kategorie do listy rozwijanej
kat_res = safe_execute(lambda: supabase.table("kategorie").select("*").execute())
kategorie_lista = kat_res.data if kat_res else []

if kategorie
