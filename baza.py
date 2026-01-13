import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Na Streamlit Cloud używamy st.secrets, lokalnie można użyć .env
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Zarządzanie Produktami", layout="wide")
st.title("📦 System Zarządzania Produktami")

# --- ZAKŁADKI ---
tab1, tab2 = st.tabs(["Kategorie", "Produkty"])

# --- TAB 1: KATEGORIE ---
with tab1:
    st.header("Zarządzaj Kategoriami")
    
    # Formularz dodawania
    with st.expander("Dodaj nową kategorię"):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        if st.button("Zapisz kategorię"):
            if nazwa_kat:
                res = supabase.table("Kategorie").insert({"nazwa": nazwa_kat, "opis": opis_kat}).execute()
                st.success("Dodano kategorię!")
                st.rerun()

    # Wyświetlanie i usuwanie
    st.subheader("Lista Kategorii")
    kategorie = supabase.table("Kategorie").select("*").execute().data
    if kategorie:
        for kat in kategorie:
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{kat['nazwa']}** - {kat['opis']}")
            if col2.button("Usuń", key=f"del_kat_{kat['id']}"):
                supabase.table("Kategorie").delete().eq("id", kat['id']).execute()
                st.warning(f"Usunięto kategorię: {kat['nazwa']}")
                st.rerun()
    else:
        st.info("Brak kategorii w bazie.")

# --- TAB 2: PRODUKTY ---
with tab2:
    st.header("Zarządzaj Produktami")

    # Formularz dodawania produktu
    with st.expander("Dodaj nowy produkt"):
        # Pobieramy kategorie do listy rozwijanej
        kategorie_opcje = {k['nazwa']: k['id'] for k in kategorie}
        
        nazwa_prod = st.text_input("Nazwa produktu")
        liczba = st.number_input("Ilość (liczba)", min_value=0, step=1)
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat = st.selectbox("Kategoria", options=list(kategorie_opcje.keys()))

        if st.button("Dodaj produkt"):
            if nazwa_prod and wybrana_kat:
                dane_produktu = {
                    "nazwa": nazwa_prod,
                    "liczba": liczba,
                    "Ce...": cena, # Nazwa kolumny z Twojego schematu (Cena)
                    "kategoria_id": kategorie_opcje[wybrana_kat]
                }
                supabase.table("Produkty").insert(dane_produktu).execute()
                st.success("Produkt dodany!")
                st.rerun()

    # Wyświetlanie i usuwanie produktów
    st.subheader("Lista Produktów")
    produkty = supabase.table("Produkty").select("*, Kategorie(nazwa)").execute().data
    
    if produkty:
        for prod in produkty:
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{prod['nazwa']}** (Ilość: {prod['liczba']})")
            col2.write(f"Kategoria: {prod['Kategorie']['nazwa'] if prod['Kategorie'] else 'Brak'}")
            if col3.button("Usuń", key=f"del_prod_{prod['id']}"):
                supabase.table("Produkty").delete().eq("id", prod['id']).execute()
                st.warning(f"Usunięto: {prod['nazwa']}")
                st.rerun()
    else:
        st.info("Brak produktów w bazie.")
