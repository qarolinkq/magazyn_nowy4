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
    produkty = supabase.table("produkty").select("*").execute().data
    kategorie = supabase.table("kategorie").select("*").execute().data
    return produkty, kategorie

def zmien_stan(id_produktu, nowy_stan):
    if nowy_stan > 0:
        supabase.table("produkty").update(
            {"liczba": nowy_stan}
        ).eq("id", id_produktu).execute()
    else:
        supabase.table("produkty").delete().eq("id", id_produktu).execute()
    st.rerun()

def usun_produkt(id_produktu):
    supabase.table("produkty").delete().eq("id", id_produktu).execute()
    st.success("🗑️ Produkt usunięty")
    st.rerun()

def dodaj_produkt(nazwa, ilosc, cena, kategoria_id):
    if not nazwa.strip():
        st.error("❌ Nazwa produktu nie może być pusta")
        return
    supabase.table("produkty").insert({
        "nazwa": nazwa.strip(),
        "liczba": ilosc,
        "cena": cena,
        "kategoria_id": kategoria_id
    }).execute()
    st.success("✅ Produkt dodany")
    st.rerun()

def dodaj_kategorie(nazwa, opis):
    if not nazwa.strip():
        st.error("❌ Nazwa kategorii nie może być pusta")
        return
    supabase.table("kategorie").insert({
        "nazwa": nazwa.strip(),
        "opis": opis.strip()
    }).execute()
    st.success("✅ Kategoria dodana")
    st.rerun()

def usun_kategorie(kategoria_id):
    produkty_w_kat = (
        supabase.table("produkty")
        .select("id")
        .eq("kategoria_id", kategoria_id)
        .execute()
        .data
    )
    if produkty_w_kat:
        st.error("❌ Nie można usunąć kategorii — są do niej przypisane produkty")
        return
    supabase.table("kategorie").delete().eq("id", kategoria_id).execute()
    st.success("🗑️ Kategoria usunięta")
    st.rerun()

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
    st.subheader("Stan magazynu")

    if not produkty:
        st.info("Magazyn jest pusty.")
    else:
        for p in produkty:
            st.markdown(f"### {p['nazwa']}")
            st.caption(
                f"Stan: {p['liczba']} szt. | "
                f"Cena: {p['cena']} zł | "
                f"Kategoria: {kat_id_na_nazwe.get(p['kategoria_id'], '—')}"
            )

            # ===== JEDEN PROFESJONALNY PASEK =====
            col_qty, col_minus, col_plus, col_zero, col_del = st.columns(
                [2, 1, 1, 2, 2]
            )

            with col_qty:
                ilosc = st.number_input(
                    "Ilość",
                    min_value=1,
                    value=1,
                    key=f"qty_{p['id']}"
                )

            with col_minus:
                if st.button("➖", key=f"minus_{p['id']}"):
                    zmien_stan(p["id"], max(0, p["liczba"] - ilosc))
                st.caption("Usuń")

            with col_plus:
                if st.button("➕", key=f"plus_{p['id']}"):
                    zmien_stan(p["id"], p["liczba"] + ilosc)
                st.caption("Dodaj")

            with col_zero:
                if st.button("🗑️ Wyzeruj stan", key=f"zero_{p['id']}"):
                    zmien_stan(p["id"], 0)

            with col_del:
                if st.button("❌ Usuń produkt", key=f"del_{p['id']}"):
                    usun_produkt(p["id"])

            st.divider()

# ================== TAB 2 — DODAJ PRODUKT ==================

with tab2:
    st.subheader("Dodaj nowy produkt")

    if not kategorie:
        st.warning("Najpierw dodaj kategorię.")
    else:
        with st.form("dodaj_produkt"):
            nazwa = st.text_input("Nazwa produktu")
            ilosc = st.number_input("Ilość początkowa", min_value=1, value=1)
            cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
            kategoria = st.selectbox("Kategoria", kat_nazwa_na_id.keys())

            submit = st.form_submit_button("➕ Dodaj produkt")

            if submit:
                dodaj_produkt(nazwa, ilosc, cena, kat_nazwa_na_id[kategoria])

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
        opis = st.text_area("Opis kategorii")
        submit = st.form_submit_button("Dodaj kategorię")
        if submit:
            dodaj_kategorie(nazwa, opis)

    st.divider()

    if kategorie:
        kat = st.selectbox("Usuń kategorię", kat_nazwa_na_id.keys())
        if st.button("Usuń kategorię"):
            usun_kategorie(kat_nazwa_na_id[kat])
