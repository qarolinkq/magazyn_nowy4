import streamlit as st
from supabase import create_client, Client

# ================== KONFIGURACJA ==================
st.set_page_config(
    page_title="☁️ System magazynowy Chmurka",
    layout="wide"
)

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Błąd połączenia: {e}")
        return None

supabase = init_connection()
if not supabase:
    st.stop()

# ================== FUNKCJE ==================

def pobierz_dane():
    produkty = supabase.table("produkty").select("*").order("nazwa").execute().data
    kategorie = supabase.table("kategorie").select("*").order("nazwa").execute().data
    return produkty, kategorie

def zmien_stan(id_produktu, nowy_stan):
    supabase.table("produkty").update(
        {"liczba": max(0, nowy_stan)}
    ).eq("id", id_produktu).execute()
    st.rerun()

def usun_produkt(id_produktu):
    supabase.table("produkty").delete().eq("id", id_produktu).execute()
    st.rerun()

# ================== DANE ==================

produkty, kategorie = pobierz_dane()
kat_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie}
kat_nazwa_na_id = {k["nazwa"]: k["id"] for k in kategorie}

# ================== UI ==================

st.title("☁️ System magazynowy Chmurka")

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Magazyn",
    "📊 Statystyki",
    "➕ Dodaj produkt",
    "📂 Kategorie"
])

# ================== TAB 1 — MAGAZYN ==================
with tab1:
    st.subheader("Filtrowanie i sortowanie")

    f1, f2, f3 = st.columns(3)

    with f1:
        search_query = st.text_input(
            "🔍 Szukaj (produkt / kategoria)", ""
        ).lower()

    with f2:
        filtr_kategoria = st.selectbox(
            "📂 Kategoria",
            ["Wszystkie"] + list(kat_nazwa_na_id.keys())
        )

    with f3:
        sortowanie = st.selectbox(
            "↕️ Sortuj według",
            [
                "Nazwa (A–Z)",
                "Nazwa (Z–A)",
                "Ilość (rosnąco)",
                "Ilość (malejąco)",
                "Wartość (rosnąco)",
                "Wartość (malejąco)"
            ]
        )

    st.divider()

    # ---------- FILTROWANIE ----------
    filtrowane = []

    for p in produkty:
        nazwa = p["nazwa"].lower()
        kat = kat_id_na_nazwe.get(p["kategoria_id"], "").lower()
        wartosc = p["liczba"] * p["cena"]

        if search_query and search_query not in nazwa and search_query not in kat:
            continue

        if filtr_kategoria != "Wszystkie":
            if kat_id_na_nazwe.get(p["kategoria_id"]) != filtr_kategoria:
                continue

        p["_wartosc"] = wartosc
        filtrowane.append(p)

    # ---------- SORTOWANIE ----------
    if sortowanie == "Nazwa (A–Z)":
        filtrowane.sort(key=lambda x: x["nazwa"])
    elif sortowanie == "Nazwa (Z–A)":
        filtrowane.sort(key=lambda x: x["nazwa"], reverse=True)
    elif sortowanie == "Ilość (rosnąco)":
        filtrowane.sort(key=lambda x: x["liczba"])
    elif sortowanie == "Ilość (malejąco)":
        filtrowane.sort(key=lambda x: x["liczba"], reverse=True)
    elif sortowanie == "Wartość (rosnąco)":
        filtrowane.sort(key=lambda x: x["_wartosc"])
    elif sortowanie == "Wartość (malejąco)":
        filtrowane.sort(key=lambda x: x["_wartosc"], reverse=True)

    # ---------- WYŚWIETLANIE ----------
    if not filtrowane:
        st.info("Brak produktów spełniających kryteria.")
    else:
        for p in filtrowane:
            with st.container():
                col_info, col_actions = st.columns([2, 1])

                with col_info:
                    st.subheader(p["nazwa"])
                    st.write(
                        f"**Stan:** `{p['liczba']} szt.` | "
                        f"**Cena:** {p['cena']} zł | "
                        f"**Wartość:** {p['_wartosc']:.2f} zł"
                    )
                    st.caption(
                        f"Kategoria: {kat_id_na_nazwe.get(p['kategoria_id'], 'Brak')}"
                    )

                with col_actions:
                    ilosc = st.number_input(
                        "Ile sztuk?",
                        min_value=1,
                        value=1,
                        key=f"qty_{p['id']}"
                    )

                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("➕ Dodaj", key=f"add_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], p["liczba"] + ilosc)
                    with b2:
                        if st.button("➖ Odejmij", key=f"sub_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], p["liczba"] - ilosc)

                    with st.expander("Opcje usuwania"):
                        if st.button("🔄 Wyzeruj stan", key=f"reset_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], 0)
                        if st.button("🗑️ Usuń produkt", key=f"del_{p['id']}", use_container_width=True):
                            usun_produkt(p["id"])

                st.divider()

# ================== TAB 2 — STATYSTYKI ==================
with tab2:
    total_val = sum(p["liczba"] * p["cena"] for p in produkty)
    total_qty = sum(p["liczba"] for p in produkty)

    c1, c2 = st.columns(2)
    c1.metric("Łączna wartość magazynu", f"{total_val:,.2f} zł")
    c2.metric("Suma wszystkich sztuk", f"{total_qty} szt.")

    if produkty:
        wykres = {}
        for p in produkty:
            kat = kat_id_na_nazwe.get(p["kategoria_id"], "Nieprzypisane")
            wykres[kat] = wykres.get(kat, 0) + (p["liczba"] * p["cena"])
        st.bar_chart(wykres)

# ================== TAB 3 — DODAJ PRODUKT ==================
with tab3:
    st.subheader("Dodawanie nowego produktu")
    if not kategorie:
        st.error("Najpierw dodaj kategorię.")
    else:
        with st.form("form_dodaj_prod", clear_on_submit=True):
            nazwa = st.text_input("Nazwa produktu")
            ilosc = st.number_input("Ilość", min_value=0, value=0)
            cena = st.number_input("Cena za sztukę", min_value=0.0, step=0.01)
            kat = st.selectbox("Kategoria", kat_nazwa_na_id.keys())

            if st.form_submit_button("Dodaj produkt"):
                if nazwa:
                    supabase.table("produkty").insert({
                        "nazwa": nazwa,
                        "liczba": ilosc,
                        "cena": cena,
                        "kategoria_id": kat_nazwa_na_id[kat]
                    }).execute()
                    st.success("Dodano!")
                    st.rerun()
                else:
                    st.warning("Podaj nazwę!")

# ================== TAB 4 — KATEGORIE ==================
with tab4:
    col_l, col_r = st.columns(2)

    with col_r:
        with st.form("form_kat", clear_on_submit=True):
            n = st.text_input("Nazwa nowej kategorii")
            o = st.text_area("Opis")
            if st.form_submit_button("Utwórz kategorię") and n:
                supabase.table("kategorie").insert({
                    "nazwa": n,
                    "opis": o
                }).execute()
                st.rerun()

    with col_l:
        for k in kategorie:
            with st.expander(f"📂 {k['nazwa']}"):
                st.write(k["opis"])
                if st.button("Usuń kategorię", key=f"del_kat_{k['id']}"):
                    if any(p["kategoria_id"] == k["id"] for p in produkty):
                        st.error("Kategoria nie jest pusta!")
                    else:
                        supabase.table("kategorie").delete().eq("id", k["id"]).execute()
                        st.rerun()
