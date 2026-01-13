import streamlit as st

# --- 1. Zarządzanie Stanem Sesji ---

# Używamy słownika: { "Nazwa": ilość_sztuk }
if 'magazyn' not in st.session_state:
    st.session_state['magazyn'] = {} 

def dodaj_prezent():
    nazwa = st.session_state.temp_nazwa.strip()
    ile_dodac = st.session_state.temp_ilosc
    if nazwa:
        if nazwa in st.session_state.magazyn:
            st.session_state.magazyn[nazwa] += ile_dodac
        else:
            st.session_state.magazyn[nazwa] = ile_dodac
        # Resetowanie pól formularza
        st.session_state.temp_nazwa = ""
        st.session_state.temp_ilosc = 1

def usun_konkretna_ilosc(nazwa, ile_odjac):
    if nazwa in st.session_state.magazyn:
        st.session_state.magazyn[nazwa] -= ile_odjac
        # Jeśli ilość spadnie do zera, usuwamy produkt z widoku
        if st.session_state.magazyn[nazwa] <= 0:
            del st.session_state.magazyn[nazwa]

# --- 2. Układ Aplikacji ---

def main():
    st.set_page_config(page_title="Magazyn Mikołaja", layout="wide")
    st.title("📦 Magazyn Prezentów z Wyborem Ilości")
    
    # --- GÓRA: Panel dodawania ---
    col_mik, col_form = st.columns([1, 2])
    
    with col_mik:
        st.markdown("# 🎅")
        total = sum(st.session_state.magazyn.values())
        st.metric("Suma prezentów w worku", total)
        st.write("**Hoł, hoł! Zarządzaj zapasami mądrze!**")
        
    with col_form:
        st.subheader("➕ Przyjęcie nowej dostawy")
        c1, c2 = st.columns([3, 1])
        with c1:
            st.text_input("Nazwa przedmiotu", key="temp_nazwa")
        with c2:
            st.number_input("Ile sztuk?", min_value=1, value=1, key="temp_ilosc")
        st.button("Dodaj do magazynu", on_click=dodaj_prezent, use_container_width=True)

    st.markdown("---")

    # --- DÓŁ: Lista i inteligentne usuwanie ---
    st.header("🗒️ Stan Magazynu i Wydawanie")

    if st.session_state.magazyn:
        # Nagłówki
        h1, h2, h3, h4 = st.columns([0.4, 0.2, 0.2, 0.2])
        h1.write("**Nazwa produktu**")
        h2.write("**Obecny stan**")
        h3.write("**Ile chcesz usunąć?**")
        h4.write("**Potwierdź**")
        
        # Przechodzimy przez produkty (używamy list(), aby móc usuwać klucze w pętli)
        for nazwa, stan in list(st.session_state.magazyn.items()):
            c_nazwa, c_stan, c_ile, c_akcja = st.columns([0.4, 0.2, 0.2, 0.2])
            
            with c_nazwa:
                st.write(f"🎁 **{nazwa}**")
            
            with c_stan:
                st.write(f"{stan} szt.")
            
            with c_ile:
                # To pole pozwala Ci zdecydować, jaką ilość usunąć
                ile_do_usuniecia = st.number_input(
                    "Ilość", 
                    min_value=1, 
                    max_value=stan, # Nie pozwoli usunąć więcej niż masz
                    value=1, 
                    key=f"input_{nazwa}",
                    label_visibility="collapsed"
                )
            
            with c_akcja:
                st.button(
                    "Zdejmij ze stanu", 
                    key=f"btn_{nazwa}", 
                    on_click=usun_konkretna_ilosc, 
                    args=(nazwa, ile_do_usuniecia),
                    type="primary"
                )
    else:
        st.info("Magazyn jest pusty. Mikołaj czeka na dostawę!")

if __name__ == "__main__":
    main()
