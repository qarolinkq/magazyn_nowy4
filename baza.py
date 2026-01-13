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
        # Zmieniono 'Kategorie' na 'kategorie'
        safe_execute(lambda: supabase.table("kategorie").insert({"nazwa": nazwa_kat}).execute())
        st.success(f"Dodano kategorię: {nazwa_kat}")
        st.rerun()

# --- PRODUKTY ---
st.divider()
st.header("2. Produkty")

# Pobieranie kategorii (Zmieniono na małe litery)
kat_data = safe_execute(lambda: supabase.table("kategorie").select("*").execute())
kategorie = kat_data.data if kat_data else []

if kategorie:
    kat_dict = {k['nazwa']: k['id'] for k in kategorie}
    
    with st.form("produkt_form"):
        nazwa_p = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Liczba", step=1, value=0)
        cena = st.number_input("Cena", format="%.2f", value=0.0)
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        submit = st.form_submit_button("Dodaj Produkt")
        
        if submit:
            nowy_produkt = {
                "nazwa": nazwa_p,
                "liczba": ilosc,
                "cena": cena, # Jeśli w bazie kolumna nazywa się inaczej, np. "Ce...", zmień to tutaj
                "kategoria_id": kat_dict[wybrana_kat]
            }
            # Zmieniono 'Produkty' na 'produkty'
            res = safe_execute(lambda: supabase.table("produkty").insert(nowy_produkt).execute())
            if res:
                st.success("Produkt dodany!")
                st.rerun()
else:
    st.warning("Najpierw dodaj kategorię w sekcji powyżej.")

# --- LISTA I USUWANIE ---
st.divider()
st.subheader("Lista produktów w bazie")
# Zmieniono na małe litery
prod_data = safe_execute(lambda: supabase.table("produkty").select("id, nazwa").execute())

if prod_data and prod_data.data:
    for p in prod_data.data:
        col1, col2 = st.columns([4, 1])
        col1.write(f"ID: {p['id']} | **{p['nazwa']}**")
        if col2.button("Usuń", key=f"del_{p['id']}"):
            safe_execute(lambda: supabase.table("produkty").delete().eq("id", p['id']).execute())
            st.rerun()
