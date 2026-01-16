import streamlit as st
from supabase import create_client, Client

# ================== KONFIGURACJA ==================

st.set_page_config(
    page_title="📦 System Magazynowy",
    layout="wide"
)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.error("❌ Brak konfiguracji Supabase (SUPABASE_URL, SUPABASE_KEY)")
    st.stop()

# ================== FUNKCJE BAZY ==================

def pobierz_dane():
    try:
        produkty = supabase.table("Produkty").select("*").execute().data
        kategorie = supabase.table("Kategorie").select("*").execute().data
        return produkty, kategorie
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return [], []

def aktualizuj_stan(id_produktu, nowa_ilosc):
    if nowa_ilosc > 0:
        supabase.table("Produkty").update(
            {"liczba": nowa_ilosc}
        ).eq("id", id_produktu).execute()
    else:
        supabase.table("Produkty").delete().eq("id", id_produktu).execute()
    st.rerun()

def dodaj_produkt(nazwa, ilosc, cena, kategoria_id):
    supabase.table("Produkty").insert({
        "nazwa": nazwa,
        "liczba": ilosc,
        "cena": cena,
        "kategoria_id": kategoria_id
    }).execute()
    st.success("✅ Produkt dodany")
    st.rerun()

def dodaj_kategorie(nazwa, opis):
    supabase.table("Kategorie").insert({
        "nazwa": nazwa,
        "opis": opis
    }).execute()
    st.success("✅ Kategoria dodana")
    st.rerun()

# ================== DANE ==================

produkty, kategorie = pobierz_dane()

kat_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie}
kat_nazwa_na_id = {k["nazwa"]: k["id"] for k in kategorie}

# ================== UI ==================

st.title("📦 System Magazynowy (Supabase)")

tab1, tab2, tab3 = st.tabs([
    "📋 Magazyn",
    "➕ Dodaj produkt",
    "📂 Kategorie"
])

# ================== TAB 1 ==================

with tab1:
    st.subheader("Aktualny stan magazynu")

    if not produkty:
        st.info("Brak produktów w magazynie.")
    else:
        h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 1.5, 1.5, 1])
        h1.write("**Nazwa**")
        h2.write("**Stan**")
        h3.write("**Cena**")
        h4.write("**Kategoria**")
        h5.write("**Ile wydać**")
        h6.write("**Akcja**")

        for p in produkty:
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 1.5, 1.5, 1])

            c1.write(p["nazwa"])
            c2.write(f"{p['liczba']} szt.")
            c3.write(f"{p['cena']} zł")
            c4.write(kat_id_na_nazwe.get(p["kategoria_id"], "—"))

            ile = c5.number_input(
                "Ilość",
                min_value=1,
                max_value=int(p["liczba"]),
                value=1,
                key=f"del_{p['id']}",
                label_visibility="collapsed"
            )

            if c6.button("➖", key=f"btn_{p['id']}"):
                aktualizuj_stan(p["id"], p["liczba"] - ile)

# ================== TAB 2 ==================

with tab2:
    st.subheader("Dodaj nowy produkt")

    with st.form("dodaj_produkt"):
        nazwa = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Ilość", min_value=1, value=1)
        cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)

        kategoria = st.selectbox(
            "Kategoria",
            options=list(kat_nazwa_na_id.keys())
        )

        submitted = st.form_submit_button("➕ Dodaj")

        if submitted:
            dodaj_produkt(
                nazwa,
                ilosc,
                cena,
                kat_nazwa_na_id[kategoria]
            )

# ================== TAB 3 ==================

with tab3:
    st.subheader("Kategorie")

    for k in kategorie:
        st.markdown(f"**{k['nazwa']}** — {k['opis']}")

    st.divider()

    with st.form("dodaj_kategorie"):
        nazwa = st.text_input("Nazwa kategorii")
        opis = st.text_area("Opis")
        submitted = st.form_submit_button("➕ Dodaj kategorię")

        if submitted:
            dodaj_kategorie(nazwa, opis)

