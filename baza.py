import streamlit as st
from supabase import create_client, Client

# ================== KONFIGURACJA ==================

st.set_page_config(
    page_title="☁️ System magazynowy Chmurka",
    layout="wide"
)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.error("❌ Brak konfiguracji Supabase")
    st.stop()

# ================== FUNKCJE ==================

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

def usun_wszystkie_produkty():
    supabase.table("Produkty").delete().neq("id", 0).execute()
    st.success("🗑️ Wszystkie produkty zostały usunięte")
    st.rerun()

def dodaj_produkt(nazwa, ilosc, cena, kategoria_id):
    if not nazwa.strip():
        st.error("❌ Nazwa produktu nie może być pusta")
        return
    try:
        supabase.table("Produkty").insert({
            "nazwa": nazwa.strip(),
            "liczba": ilosc,
            "cena": cena,
            "kategoria_id": kategoria_id
        }).execute()
        st.success("✅ Produkt dodany")
        st.rerun()
    except Exception as e:
        st.error("❌ Nie udało się dodać produktu")
        st.code(str(e))

def dodaj_kategorie(nazwa, opis):
    if not nazwa.strip():
        st.error("❌ Nazwa kategorii nie może być pusta")
        return
    try:
        supabase.table("Kategorie").insert({
            "nazwa": nazwa.strip(),
            "opis": opis.strip()
        }).execute()
        st.success("✅ Kategoria dodana")
        st.rerun()
    except Exception as e:
        st.error("❌ Nie udało się dodać kategorii")
        st.code(str(e))

# ================== DANE ==================

produkty, kategorie = pobierz_dane()

kat_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie}
kat_nazwa_na_id = {k["nazwa"]: k["id"] for k in kategorie}

# ================== UI ==================

st.title("☁️ System magazynowy Chmurka")

tab1, tab2, tab3 = st.tabs([
    "📋 Magazyn",
    "➕ Dodaj produkt",
    "📂 Kategorie"
])

# ================== TAB 1 — MAGAZYN ==================

with tab1:
    st.subheader("Aktualny stan magazynu")

    if produkty:
        if st.button("🗑️ Wyczyść cały magazyn"):
            st.session_state["confirm_delete"] = True

        if st.session_state.get("confirm_delete"):
            st.warning("⚠️ Czy na pewno chcesz usunąć WSZYSTKIE produkty?")
            col1, col2 = st.columns(2)
            if col1.button("TAK, usuń wszystko"):
                usun_wszystkie_produkty()
            if col2.button("Anuluj"):
                st.session_state["confirm_delete"] = False

        st.divider()

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
    else:
        st.info("Magazyn jest pusty.")

# ================== TAB 2 — DODAJ PRODUKT ==================

with tab2:
    st.subheader("Dodaj nowy produkt")

    if not kategorie:
        st.warning("Najpierw dodaj kategorię.")
    else:
        with st.form("dodaj_produkt"):
            nazwa = st.text_input("Nazwa produktu")
            ilosc = st.number_input("Ilość", min_value=1, value=1)
            cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)

            kategoria = st.selectbox(
                "Kategoria",
                options=list(kat_nazwa_na_id.keys())
            )

            submitted = st.form_submit_button("➕ Dodaj produkt")

            if submitted:
                dodaj_produkt(
                    nazwa,
                    ilosc,
                    cena,
                    kat_nazwa_na_id[kategoria]
                )

# ================== TAB 3 — KATEGORIE ==================

with tab3:
    st.subheader("Kategorie")

    if kategorie:
        for k in kategorie:
            st.markdown(f"**{k['nazwa']}** — {k['opis']}")
    else:
        st.info("Brak kategorii.")

    st.divider()

    with st.form("dodaj_kategorie"):
        nazwa = st.text_input("Nazwa kategorii")
        opis = st.text_area("Opis")

        submitted = st.form_submit_button("➕ Dodaj kategorię")

        if submitted:
            dodaj_kategorie(nazwa, opis)
