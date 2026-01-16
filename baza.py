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
    st.error("❌ Brak konfiguracji Supabase. Sprawdź plik .streamlit/secrets.toml")
    st.stop()

# ================== FUNKCJE ==================

def pobierz_dane():
    produkty = supabase.table("produkty").select("*").order("nazwa").execute().data
    kategorie = supabase.table("kategorie").select("*").order("nazwa").execute().data
    return produkty, kategorie

def zmien_stan(id_produktu, nowy_stan):
    supabase.table("produkty").update({"liczba": nowy_stan}).eq("id", id_produktu).execute()
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
    produkty_w_kat = supabase.table("produkty").select("id").eq("kategoria_id", kategoria_id).execute().data
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

tab1, tab2, tab3 = st.tabs(["📋 Magazyn", "➕ Dodaj produkt", "📂 Kategorie"])

# ================== TAB 1 — MAGAZYN ==================

with tab1:
    # --- WYSZUKIWARKA ---
    search_col1, search_col2 = st.columns([2, 1])
    with search_col1:
        search_query = st.text_input("🔍 Szukaj produktu (nazwa lub kategoria)", "").lower()
    
    st.divider()

    # Filtrowanie produktów
    filtrowane_produkty = [
        p for p in produkty 
        if search_query in p['nazwa'].lower() or search_query in kat_id_na_nazwe.get(p['kategoria_id'], "").lower()
    ]

    if not filtrowane_produkty:
        st.info("Nie znaleziono produktów spełniających kryteria.")
    else:
        for p in filtrowane_produkty:
            st.markdown(f"### {p['nazwa']}")
            
            col_info, col_actions = st.columns([2, 2])

            with col_info:
                st.write(f"**Stan:** `{p['liczba']} szt.`")
                st.write(f"**Cena:** {p['cena']} zł")
                st.write(f"**Kategoria:** {kat_id_na_nazwe.get(p['kategoria_id'], '—')}")

            with col_actions:
                # Pole ilości
                ilosc_zmiany = st.number_input(
                    "Ilość", min_value=1, value=1, 
                    key=f"qty_{p['id']}", label_visibility="collapsed"
                )
                
                # Przyciski DODAJ / ODEJMIJ pod polem ilości
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("➕ Dodaj", key=f"plus_{p['id']}", use_container_width=True):
                        zmien_stan(p["id"], p["liczba"] + ilosc_zmiany)
                with btn_col2:
                    if st.button("➖ Odejmij", key=f"minus_{p['id']}", use_container_width=True):
                        zmien_stan(p["id"], max(0, p["liczba"] - ilosc_zmiany))
                
                # Przyciski pomocnicze (Wyzeruj / Usuń) pod spodem
                adm_col1, adm_col2 = st.columns(2)
                with adm_col1:
                    if st.button("🔄 Wyzeruj", key=f"zero_{p['id']}", use_container_width=True):
                        zmien_stan(p["id"], 0)
                with adm_col2:
                    if st.button("❌ Usuń produkt", key=f"del_{p['id']}", use_container_width=True):
                        usun_produkt(p["id"])

            st.divider()

# ================== TAB 2 — DODAJ PRODUKT ==================

with tab2:
    st.subheader("Dodaj nowy produkt")
    if not kategorie:
        st.warning("Najpierw dodaj kategorię.")
    else:
        with st.form("dodaj_prod"):
            n = st.text_input("Nazwa produktu")
            i = st.number_input("Ilość początkowa", min_value=1, value=1)
            c = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
            k = st.selectbox("Kategoria", list(kat_nazwa_na_id.keys()))
            if st.form_submit_button("Dodaj produkt"):
                dodaj_produkt(n, i, c, kat_nazwa_na_id[k])

# ================== TAB 3 — KATEGORIE ==================

with tab3:
    col_l, col_a = st.columns(2)
    with col_l:
        st.subheader("Lista kategorii")
        for kat in kategorie:
            with st.expander(f"📂 {kat['nazwa']}"):
                st.write(kat['opis'])
                if st.button(f"Usuń {kat['nazwa']}", key=f"dk_{kat['id']}"):
                    usun_kategorie(kat['id'])
    with col_a:
        st.subheader("Nowa kategoria")
        with st.form("dodaj_kat"):
            nk = st.text_input("Nazwa")
            ok = st.text_area("Opis")
            if st.form_submit_button("Zapisz kategorię"):
                dodaj_kategorie(nk, ok)
