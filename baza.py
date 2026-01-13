import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. Konfiguracja połączenia (Ustaw Secrets w Streamlit Cloud)
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd połączenia z bazą. Sprawdź Secrets!")
    st.stop()

st.set_page_config(page_title="WMS Magazyn", layout="wide")

# --- FUNKCJE BAZODANOWE ---
def pobierz_dane():
    # Pobieramy dane zgodnie ze schematem (relacja kategoria_id)
    prod = supabase.table("Produkty").select("id, nazwa, liczba, Cena, kategoria_id, Kategorie(nazwa)").execute()
    kat = supabase.table("Kategorie").select("id, nazwa").execute()
    return prod.data if prod.data else [], kat.data if kat.data else []

def aktualizuj_stan(id_produktu, nowa_liczba):
    if nowa_liczba > 0:
        supabase.table("Produkty").update({"liczba": nowa_liczba}).eq("id", id_produktu).execute()
    else:
        supabase.table("Produkty").delete().eq("id", id_produktu).execute()
    st.rerun()

# Pobranie danych na starcie
produkty_raw, kategorie_raw = pobierz_dane()
kat_dict = {k['nazwa']: k['id'] for k in kategorie_raw}
nazwy_istniejace = list(set([p['nazwa'] for p in produkty_raw]))

# --- INTERFEJS ---
st.title("📦 System Zarządzania Magazynem (WMS)")

tabs = st.tabs(["🏠 Stan i Wydawanie", "📈 Raporty", "➕ Przyjęcie Towaru"])

# --- TAB 1: STAN I USUWANIE KONKRETNEJ ILOŚCI ---
with tabs[0]:
    st.header("Aktualny Stan i Wydawanie Produktów")
    if produkty_raw:
        # Nagłówki
        h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1.5, 1.5])
        h1.write("**Nazwa**")
        h2.write("**Stan**")
        h3.write("**Cena**")
        h4.write("**Ile usunąć/wydać?**")
        h5.write("**Akcja**")
        
        for p in produkty_raw:
            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1.5, 1.5])
            with c1:
                st.write(f"**{p['nazwa']}**")
                st.caption(f"Kat: {p['Kategorie']['nazwa'] if p['Kategorie'] else 'Brak'}")
            with c2:
                # Kolorowanie niskiego stanu
                kolor = "red" if p['liczba'] < 5 else "green"
                st.markdown(f":{kolor}[{p['liczba']} szt.]")
            with c3:
                st.write(f"{p['Cena']} zł")
            with c4:
                # Pole do wpisania ilości do usunięcia
                ile_usunac = st.number_input(
                    "Ilość", 
                    min_value=1, 
                    max_value=int(p['liczba']), 
                    value=1, 
                    key=f"del_{p['id']}",
                    label_visibility="collapsed"
                )
            with c5:
                if st.button(f"Wydaj {ile_usunac}", key=f"btn_{p['id']}", type="primary"):
                    nowy_stan = p['liczba'] - ile_usunac
                    aktualizuj_stan(p['id'], nowy_stan)
                    st.toast(f"Wydano {ile_usunac} szt. produktu {p['nazwa']}")
    else:
        st.info("Magazyn jest pusty.")

# --- TAB 2: RAPORT I WARTOŚĆ ---
with tabs[1]:
    st.header("Analiza Magazynu")
    if produkty_raw:
        df = pd.DataFrame(produkty_raw)
        df['Wartość'] = df['liczba'] * df['Cena']
        
        m1, m2 = st.columns(2)
        m1.metric("Całkowita wartość", f"{df['Wartość'].sum():,.2f} zł")
        m2.metric("Liczba asortymentu", len(df))
        
        st.divider()
        st.subheader("Wartość magazynu wg kategorii")
        # Wyciągamy nazwy kategorii do wykresu
        df['kat_name'] = df['Kategorie'].apply(lambda x: x['nazwa'] if x else "Brak")
        fig = px.bar(df, x='kat_name', y='Wartość', color='nazwa', title="Wartość produktów w kategoriach")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Brak danych do analizy.")

# --- TAB 3: DODAWANIE Z PODPOWIEDZIAMI ---
with tabs[2]:
    st.header("Przyjęcie nowego towaru")
    
    # SYSTEM PODPOWIEDZI
    podpowiedz = st.selectbox(
        "Podpowiedź: Wybierz z bazy lub wpisz nową nazwę poniżej",
        options=[""] + nazwy_istniejace
    )
    
    with st.form("dodaj_form", clear_on_submit=True):
        nazwa = st.text_input("Nazwa produktu", value=podpowiedz)
        ilosc = st.number_input("Ilość przyjmowana", min_value=1, step=1)
        cena = st.number_input("Cena jednostkowa", min_value=0.0)
        
        if kategorie_raw:
            kat_wybor = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        submit = st.form_submit_button("Zapisz w bazie")
        
        if submit:
            if nazwa and kat_wybor:
                nowy_prod = {
                    "nazwa": nazwa,
                    "liczba": ilosc,
                    "Cena": cena,
                    "kategoria_id": kat_dict[kat_wybor]
                }
                supabase.table("Produkty").insert(nowy_prod).execute()
                st.success(f"Dodano produkt: {nazwa}")
                st.rerun()
