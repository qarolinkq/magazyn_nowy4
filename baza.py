import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Połączenie z Supabase
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets! Sprawdź ustawienia na Streamlit Cloud.")
    st.stop()

st.set_page_config(page_title="System WMS Pro", layout="wide")

# --- STYLE CSS DLA PROGÓW ALARMOWYCH ---
st.markdown("""
    <style>
    .low-stock { background-color: #ffcccc; border-radius: 5px; padding: 5px; color: black; }
    .normal-stock { background-color: #e6ffed; border-radius: 5px; padding: 5px; color: black; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE BAZODANOWE ---
def pobierz_dane():
    # Pobieramy produkty z joinem do kategorii
    prod = supabase.table("Produkty").select("id, nazwa, liczba, cena, kategoria_id, kategorie(nazwa)").execute()
    kat = supabase.table("kategorie").select("id, nazwa").execute()
    return prod.data if prod.data else [], kat.data if kat.data else []

def aktualizuj_stan(id_prod, nowa_liczba):
    if nowa_liczba >= 0:
        supabase.table("Produkty").update({"liczba": nowa_liczba}).eq("id", id_prod).execute()
        st.rerun()

# Pobranie danych
produkty, kategorie = pobierz_dane()
kat_dict = {k['nazwa']: k['id'] for k in kategorie}
nazwy_produktow = [p['nazwa'] for p in produkty]

# --- MENU BOCZNE (NAV) ---
st.sidebar.title("🎮 Panel Sterowania")
opcja = st.sidebar.radio("Wybierz moduł:", ["Magazyn i Edycja", "Dodaj Nowy Towar", "Statystyki"])

# --- MODUŁ 1: MAGAZYN I EDYCJA (KLUCZ WMS) ---
if opcja == "Magazyn i Edycja":
    st.header("📊 Stan Magazynowy i Operacje")
    
    if nie produkty:
        st.info("Magazyn jest pusty.")
    else:
        # Nagłówki tabeli
        cols = st.columns([2, 1, 1, 2, 2, 1])
        cols[0].write("**Produkt**")
        cols[1].write("**Ilość**")
        cols[2].write("**Cena**")
        cols[3].write("**Kategoria**")
        cols[4].write("**Szybka Zmiana**")
        cols[5].write("**Akcja**")
        st.divider()

        for p in produkty:
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 2, 2, 1])
            
            # Progi alarmowe (wizualizacja)
            is_low = p['liczba'] < 5
            style = "low-stock" if is_low else "normal-stock"
            alert = "⚠️ MAŁO!" if is_low else "✅ OK"
            
            c1.markdown(f"<div class='{style}'><b>{p['nazwa']}</b><br><small>{alert}</small></div>", unsafe_allow_html=True)
            c2.write(f"{p['liczba']} szt.")
            c3.write(f"{p['cena']} zł")
            c4.write(p['kategorie']['nazwa'] if p.get('kategorie') else "Brak")
            
            # Przyciski +/- (Szybkie wydanie/przyjęcie)
            with c5:
                col_m, col_p = st.columns(2)
                if col_m.button("➖", key=f"minus_{p['id']}"):
                    aktualizuj_stan(p['id'], p['liczba'] - 1)
                if col_p.button("➕", key=f"plus_{p['id']}"):
                    aktualizuj_stan(p['id'], p['liczba'] + 1)
            
            if c6.button("🗑️", key=f"del_{p['id']}"):
                supabase.table("Produkty").delete().eq("id", p['id']).execute()
                st.rerun()

# --- MODUŁ 2: DODAWANIE Z PODPOWIEDZIAMI ---
elif opcja == "Dodaj Nowy Towar":
    st.header("➕ Przyjęcie nowego towaru")
    
    # Inteligentna podpowiedź
    szukaj = st.selectbox("Podpowiedź (istniejące):", [""] + list(set(nazwy_produktow)))
    
    with st.form("form_wms"):
        nazwa = st.text_input("Nazwa produktu", value=szukaj)
        ilosc = st.number_input("Ilość początkowa", min_value=1)
        cena = st.number_input("Cena jednostkowa", min_value=0.0, format="%.2f")
        kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        if st.form_submit_button("Zatwierdź przyjęcie"):
            if nazwa and kat:
                # Automatyczne ID (naprawa błędu 23505)
                supabase.table("Produkty").insert({
                    "nazwa": nazwa, "liczba": ilosc, "cena": cena, "kategoria_id": kat_dict[kat]
                }).execute()
                st.success("Towar przyjęty do bazy!")
                st.rerun()

# --- MODUŁ 3: STATYSTYKI ---
elif opcja == "Statystyki":
    st.header("📈 Analityka Magazynowa")
    if produkty:
        df = pd.DataFrame(produkty)
        total_value = (df['liczba'] * df['cena']).sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Łączna wartość magazynu", f"{total_value:,.2f} zł")
        c2.metric("Liczba asortymentu (SKU)", len(df))
        
        st.subheader("Wartość towaru per kategoria")
        # Wykres uproszczony
        df['wartosc'] = df['liczba'] * df['cena']
        st.bar_chart(df, x="nazwa", y="wartosc")
