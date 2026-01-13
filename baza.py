import streamlit as st
from supabase import create_client, Client

# 1. Konfiguracja połączenia z Supabase
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets! Sprawdź ustawienia na Streamlit Cloud.")
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
            safe_execute(lambda: supabase.table("kategorie").insert({"nazwa": nowa_kat_nazwa}).execute())
            st.success(f"Dodano kategorię: {nowa_kat_nazwa}")
            st.rerun()

st.divider()

# --- SEKCJA 2: PRODUKTY ---
st.header("2. Zarządzanie Produktami")

# Pobieramy aktualne kategorie do listy rozwijanej
kat_res = safe_execute(lambda: supabase.table("kategorie").select("*").execute())
kategorie_lista = kat_res.data if kat_res else []

# POPRAWKA: Dodano brakujący dwukropek po if
if kategorie_lista:
    kat_dict = {k['nazwa']: k['id'] for k in kategorie_lista}
    
    with st.form("form_produkt", clear_on_submit=True):
        st.subheader("Dodaj nowy produkt")
        nazwa_p = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Liczba sztuk", min_value=0, step=1)
        # Zmieniamy na 'cena' (małymi) lub 'Ce...' zależnie od bazy
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        submit = st.form_submit_button("Dodaj produkt do magazynu")
        
        if submit:
            if nazwa_p:
                # NIE dodajemy 'id' - baza wygeneruje je sama
                dane_produktu = {
                    "nazwa": nazwa_p,
                    "liczba": ilosc,
                    "cena": cena, 
                    "kategoria_id": kat_dict[wybrana_kat]
                }
                res = safe_execute(lambda: supabase.table("Produkty").insert(dane_produktu).execute())
                if res:
                    st.success(f"Pomyślnie dodano produkt: {nazwa_p}")
                    st.rerun()
            else:
                st.warning("Proszę podać nazwę produktu.")
else:
    st.info("Baza kategorii jest pusta. Dodaj kategorię powyżej.")

st.divider()

# --- SEKCJA 3: LISTA PRODUKTÓW I USUWANIE ---
st.header("3. Aktualny Stan Magazynu")

# Pobieramy produkty
prod_res = safe_execute(lambda: supabase.table("Produkty").select("id, nazwa, liczba, cena").execute())

if prod_res and prod_res.data:
    for p in prod_res.data:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{p['nazwa']}**")
        with col2:
            st.write(f"{p['liczba']} szt. | {p['cena']} zł")
        with col3:
            if st.button("Usuń", key=f"btn_del_{p['id']}"):
                safe_execute(lambda: supabase.table("Produkty").delete().eq("id", p['id']).execute())
                st.rerun()
else:
    st.write("Brak produktów w bazie.")
