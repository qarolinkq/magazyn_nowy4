iimport streamlit as st
from supabase import create_client, Client

# 1. Połączenie z Supabase
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets w Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title="Magazyn Pro", layout="wide")
st.title("📦 Inteligentne Zarządzanie Magazynem")

# --- FUNKCJE POMOCNICZE ---
def pobierz_dane():
    # Pobieranie produktów wraz z joinem do tabeli kategorie
    prod = supabase.table("Produkty").select("id, nazwa, liczba, cena, kategoria_id, kategorie(nazwa)").execute()
    kat = supabase.table("kategorie").select("id, nazwa").execute()
    return prod.data if prod.data else [], kat.data if kat.data else []

def usun_produkt(id_produktu):
    supabase.table("Produkty").delete().eq("id", id_produktu).execute()
    st.success("Produkt został usunięty.")
    st.rerun()

# Pobieranie danych na starcie
produkty, kategorie = pobierz_dane()
kat_dict = {k['nazwa']: k['id'] for k in kategorie}
nazwy_produktow = [p['nazwa'] for p in produkty]

# --- SEKCJA 1: DODAWANIE I PODPOWIEDZI ---
st.header("➕ Dodaj nowy towar")
col_search, col_form = st.columns([1, 2])

with col_search:
    st.subheader("🔍 Podpowiedzi")
    szukaj = st.selectbox(
        "Zacznij wpisywać nazwę:",
        options=[""] + list(set(nazwy_produktow)),
        help="Jeśli produkt istnieje w bazie, wybierz go, aby przyspieszyć wpisywanie."
    )
    if szukaj:
        st.info(f"Produkt '{szukaj}' jest już w bazie.")

with col_form:
    with st.form("form_dodawania", clear_on_submit=True):
        nazwa = st.text_input("Nazwa produktu", value=szukaj if szukaj else "")
        liczba = st.number_input("Ilość (liczba)", min_value=1, step=1)
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        submit = st.form_submit_button("Zapisz w magazynie")
        
        if submit:
            if nazwa and wybrana_kat:
                # Nie wysyłamy 'id', aby uniknąć błędu duplicate key
                nowy_produkt = {
                    "nazwa": nazwa,
                    "liczba": liczba,
                    "cena": cena,
                    "kategoria_id": kat_dict[wybrana_kat]
                }
                res = supabase.table("Produkty").insert(nowy_produkt).execute()
                if res:
                    st.success(f"Dodano: {nazwa}")
                    st.rerun()
            else:
                st.error("Wypełnij wszystkie pola!")

st.divider()

# --- SEKCJA 2: AKTUALNY STAN MAGAZYNOWY ---
st.header("📊 Aktualny stan magazynowy")

if produkty:
    # Przygotowanie tabeli do wyświetlenia
    tabela_danych = []
    for p in produkty:
        tabela_danych.append({
            "ID": p['id'],
            "Nazwa": p['nazwa'],
            "Ilość": p['liczba'],
            "Cena": f"{p['cena']} zł",
            "Kategoria": p['kategorie']['nazwa'] if p.get('kategorie') else "Brak"
        })
    
    st.table(tabela_danych)

    # --- SEKCJA 3: USUWANIE PRODUKTÓW ---
    st.subheader("🗑️ Usuń produkt z bazy")
    col_del1, col_del2 = st.columns([3, 1])
    
    with col_del1:
        produkt_do_usunicia = st.selectbox(
            "Wybierz produkt do trwałego usunięcia:",
            options=produkty,
            format_func=lambda x: f"{x['nazwa']} (ID: {x['id']})"
        )
    
    with col_del2:
        st.write("##") # Margines
        if st.button("USUŃ DEFINITYWNIE", type="primary"):
            usun_produkt(produkt_do_usunicia['id'])
else:
    st.info("Magazyn jest obecnie pusty.")
                    aktualizuj_stan(p['
