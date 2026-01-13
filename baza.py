import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Upewnij się, że dodałeś te dane w Streamlit Cloud: Settings -> Secrets
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji! Dodaj Secrets: SUPABASE_URL i SUPABASE_KEY.")
    st.stop()

st.set_page_config(page_title="Magazyn Supabase", layout="wide")

# --- FUNKCJE OBSŁUGI BAZY ---

def pobierz_dane():
    """Pobiera dane z tabel Produkty i Kategorie."""
    try:
        # Zgodnie ze schematem: id (int8), nazwa (Tekst), liczba (int8), Cena (Numeryczne), kategoria_id (int8)
        produkty = supabase.table("Produkty").select("*").execute()
        # Zgodnie ze schematem: id (int8), nazwa (Tekst), opis (Tekst)
        kategorie = supabase.table("Kategorie").select("*").execute()
        return produkty.data, kategorie.data
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return [], []

def aktualizuj_stan(id_produktu, nowa_liczba):
    """Zmienia ilość produktu lub usuwa go, gdy stan wynosi 0."""
    if nowa_liczba > 0:
        supabase.table("Produkty").update({"liczba": nowa_liczba}).eq("id", id_produktu).execute()
    else:
        supabase.table("Produkty").delete().eq("id", id_produktu).execute()
    st.rerun()

# --- LOGIKA APLIKACJI ---

produkty, kategorie = pobierz_dane()

# Słowniki pomocnicze
kat_id_na_nazwe = {k['id']: k['nazwa'] for k in kategorie}
kat_nazwa_na_id = {k['nazwa']: k['id'] for k in kategorie}
lista_nazw_produktow = list(set([p['nazwa'] for p in produkty]))

st.title("📦 System Magazynowy Supabase")

tab1, tab2, tab3 = st.tabs(["📋 Magazyn i Wydawanie", "➕ Dodaj Produkt", "📂 Kategorie"])

# --- TAB 1: STAN I USUWANIE ILOŚCI ---
with tab1:
    st.header("Aktualny stan magazynu")
    if produkty:
        # Nagłówki
        col_n, col_s, col_c, col_k, col_u, col_a = st.columns([2, 1, 1, 1.5, 1.5, 1])
        col_n.write("**Nazwa**")
        col_s.write("**Stan**")
        col_c.write("**Cena**")
        col_k.write("**Kategoria**")
        col_u.write("**Ile usunąć?**")
        col_a.write("**Akcja**")
        
        for p in produkty:
            c_n, c_s, c_c, c_k, c_u, c_a = st.columns([2, 1, 1, 1.5, 1.5, 1])
            c_n.write(p['nazwa'])
            c_s.write(f"{p['liczba']} szt.")
            # Zgodnie ze schematem kolumna nazywa się 'Ce...' (prawdopodobnie Cena/Cennik)
            # Jeśli w bazie masz inną nazwę, zmień klucz poniżej
            c_c.write(f"{p.get('Cena', p.get('Ce...', 0))} zł")
            c_k.write(kat_id_na_nazwe.get(p['kategoria_id'], "Brak"))
            
            # Pole do wpisania ilości do usunięcia
            ile_do_odjecia = c_u.number_input(
                "Ilość", min_value=1, max_value=int(p['liczba']), 
                value=1, key=f"del_{p['id']}", label_visibility="collapsed
