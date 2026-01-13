import streamlit as st
from supabase import create_client, Client

# 1. Połączenie z Supabase (skonfiguruj Secrets w panelu Streamlit Cloud)
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd połączenia. Upewnij się, że dodałeś Secrets w Streamlit!")
    st.stop()

st.set_page_config(page_title="Magazyn AI", layout="centered")
st.title("📦 Inteligentny System Magazynowy")

# --- FUNKCJE POMOCNICZE ---
def pobierz_liste_produktow():
    # Pobiera tylko nazwy dla systemu podpowiedzi
    res = supabase.table("Produkty").select("nazwa").execute()
    return [p['nazwa'] for p in res.data] if res.data else []

def pobierz_kategorie():
    # Pobiera kategorie do listy rozwijanej
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return {k['nazwa']: k['id'] for k in res.data} if res.data else {}

# --- LOGIKA APLIKACJI ---

# Pobieramy dane do podpowiedzi
istniejace_nazwy = pobierz_liste_produktow()
kategorie_dict = pobierz_kategorie()

st.header("Dodaj nowy produkt")

# System podpowiedzi (Searchbox)
szukaj = st.selectbox(
    "Podpowiedź: sprawdź czy produkt już istnieje",
    options=[""] + istniejace_nazwy,
    help="Zacznij wpisywać, aby przeszukać bazę"
)

if szukaj:
    st.info(f"Produkt '{szukaj}' znajduje się już w Twoim magazynie.")

# Formularz dodawania
with st.form("form_dodawania", clear_on_submit=True):
    # Pola zgodne ze schematem
    nowa_nazwa = st.text_input("Nazwa produktu", value=szukaj if szukaj else "")
    liczba = st.number_input("Liczba (ilość)", min_value=1, step=1)
    # Kolumna 'Ce...' na schemacie to prawdopodobnie 'Cena'
    cena = st.number_input("Cena", min_value=0.0, format="%.2f")
    
    if kategorie_dict:
        wybrana_kat = st.selectbox("Wybierz kategorię", options=list(kategorie_dict.keys()))
    else:
        st.warning("Najpierw dodaj kategorie w bazie danych!")
        wybrana_kat = None

    submit = st.form_submit_button("Zapisz w magazynie")

    if submit:
        if nowa_nazwa and wybrana_kat:
            dane_produktu = {
                "nazwa": nowa_nazwa,
                "liczba": liczba,
                "cena": cena,
                "kategoria_id": kategorie_dict[wybrana_kat]
            }
            
            # Wstawianie do tabeli Produkty
            try:
                supabase.table("Produkty").insert(dane_produktu).execute()
                st.success(f"Pomyślnie dodano: {nowa_nazwa}")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd zapisu: {e}")
        else:
            st.warning("Wypełnij wszystkie pola!")

# --- PODGLĄD MAGAZYNU ---
st.divider()
st.subheader("Aktualny stan magazynu")
prod_res = supabase.table("Produkty").select("nazwa, liczba, cena, kategorie(nazwa)").execute()

if prod_res.data:
    for p in prod_res.data:
        kat_nazwa = p['kategorie']['nazwa'] if p.get('kategorie') else "Brak"
        st.write(f"🔹 **{p['nazwa']}** | Ilość: {p['liczba']} | Cena: {p['cena']} zł | ({kat_nazwa})")
else:
    st.info("Magazyn jest pusty.")
