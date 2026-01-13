import streamlit as st
from supabase import create_client, Client

# Połączenie z Supabase
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets!")
    st.stop()

st.title("📦 Inteligentny Magazyn")

# --- FUNKCJE POMOCNICZE ---
def pobierz_liste_produktow():
    # Pobieramy nazwy do podpowiedzi
    res = supabase.table("Produkty").select("nazwa").execute()
    return [p['nazwa'] for p in res.data] if res.data else []

def pobierz_kategorie():
    # Pobieramy kategorie (zgodnie ze schematem: tabela 'kategorie')
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return {k['nazwa']: k['id'] for k in res.data} if res.data else {}

# --- LOGIKA PODPOWIEDZI ---
istniejace = pobierz_liste_produktow()
kategorie_dict = pobierz_kategorie()

st.header("Dodaj nowy produkt")
szukaj = st.selectbox("Szukaj w bazie (podpowiedź):", [""] + istniejace)

if szukaj:
    st.info(f"Produkt '{szukaj}' jest już w bazie.")

# --- FORMULARZ (POPRAWIONY) ---
with st.form("dodaj_produkt_form", clear_on_submit=True):
    nazwa = st.text_input("Nazwa produktu", value=szukaj if szukaj else "")
    liczba = st.number_input("Ilość", min_value=1, step=1)
    # Kolumna 'Ce...' ze schematu to prawdopodobnie 'cena'
    cena = st.number_input("Cena", min_value=0.0, format="%.2f")
    kat_nazwa = st.selectbox("Kategoria", options=list(kategorie_dict.keys()))
    
    submit = st.form_submit_button("Zapisz produkt")
    
    if submit:
        if nazwa and kat_nazwa:
            # ROZWIĄZANIE BŁĘDU: Nie definiujemy 'id' w tym słowniku.
            # Baza danych sama przypisze kolejny wolny numer.
            nowy_rekord = {
                "nazwa": nazwa,
                "liczba": liczba,
                "cena": cena,
                "kategoria_id": kategorie_dict[kat_nazwa]
            }
            
            try:
                supabase.table("Produkty").insert(nowy_rekord).execute()
                st.success(f"Dodano pomyślnie: {nazwa}")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd bazy danych: {e}")
        else:
            st.warning("Uzupełnij nazwę produktu!")
