import streamlit as st
from supabase import create_client, Client

# ================== KONFIGURACJA ==================
st.set_page_config(page_title="☁️ System Chmurka PRO", layout="wide")

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("❌ Błąd połączenia z Supabase")
        return None

supabase = init_connection()
if not supabase: st.stop()

# ================== FUNKCJE ==================
def pobierz_dane():
    produkty = supabase.table("produkty").select("*").order("nazwa").execute().data
    kategorie = supabase.table("kategorie").select("*").order("nazwa").execute().data
    return produkty, kategorie

def zmien_stan(id_produktu, nowy_stan):
    supabase.table("produkty").update({"liczba": max(0, nowy_stan)}).eq("id", id_produktu).execute()
    st.rerun()

# ================== DANE ==================
produkty, kategorie = pobierz_dane()
kat_id_na_nazwe = {k["id"]: k["nazwa"] for k in kategorie}
kat_nazwa_na_id = {k["nazwa"]: k["id"] for k in kategorie}

# ================== UI ==================
st.title("☁️ System magazynowy Chmurka PRO")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Magazyn", "📊 Statystyki", "➕ Dodaj produkt", "📂 Kategorie"])

# ================== TAB 1 — MAGAZYN ==================
with tab1:
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Szukaj produktu...", "").lower()
    with col_filter:
        pokaż_tylko_braki = st.toggle("⚠️ Pokaż tylko braki (poniżej minimum)")

    st.divider()

    # --- LOGIKA FILTROWANIA ---
    filtrowane = [
        p for p in produkty 
        if (search_query in p['nazwa'].lower() or search_query in kat_id_na_nazwe.get(p['kategoria_id'], "").lower())
        and (not pokaż_tylko_braki or p['liczba'] <= p.get('minimum', 0))
    ]

    if not filtrowane:
        st.info("Brak produktów spełniających kryteria.")
    else:
        for p in filtrowane:
            # Określenie czy stan jest krytyczny
            min_stan = p.get('minimum', 0)
            is_low = p['liczba'] <= min_stan
            
            with st.container():
                c1, c2 = st.columns([2, 1])
                
                with c1:
                    # Kolorowanie nagłówka jeśli mało towaru
                    title_color = "red" if is_low else "black"
                    st.markdown(f"<h3 style='color: {title_color};'>{p['nazwa']} {'⚠️' if is_low else ''}</h3>", unsafe_allow_html=True)
                    
                    st.write(f"**Stan:** `{p['liczba']} szt.` (Minimum: {min_stan})")
                    st.write(f"**Cena:** {p['cena']} zł | **Suma:** {round(p['liczba'] * p['cena'], 2)} zł")
                    
                    if is_low:
                        st.error(f"Niski stan! Brakuje co najmniej {max(0, min_stan - p['liczba'] + 1)} sztuk do poziomu bezpiecznego.")

                with c2:
                    val = st.number_input("Ilość", min_value=1, value=1, key=f"v_{p['id']}")
                    
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("➕ Dodaj", key=f"a_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], p["liczba"] + val)
                    with b2:
                        if st.button("➖ Odejmij", key=f"s_{p['id']}", use_container_width=True):
                            zmien_stan(p["id"], p["liczba"] - val)
                    
                    if st.button("🗑️ Usuń", key=f"d_{p['id']}", use_container_width=True, type="secondary"):
                        supabase.table("produkty").delete().eq("id", p['id']).execute()
                        st.rerun()
                st.divider()

# ================== TAB 3 — DODAJ PRODUKT ==================
with tab3:
    st.subheader("Nowa pozycja w magazynie")
    with st.form("new_product", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            nazwa = st.text_input("Nazwa produktu*")
            ilosc = st.number_input("Ilość początkowa", min_value=0, value=10)
            cena = st.number_input("Cena (zł)", min_value=0.0, step=0.01)
        with col_b:
            # NOWE POLE: PROG OSTRZEGAWCZY
            minimum = st.number_input("Próg ostrzegawczy (minimum)", min_value=0, value=5, help="Poniżej tej ilości system podświetli produkt na czerwono.")
            kat_sel = st.selectbox("Kategoria", list(kat_nazwa_na_id.keys()))
        
        if st.form_submit_button("✅ Zapisz produkt"):
            if nazwa:
                supabase.table("produkty").insert({
                    "nazwa": nazwa, "liczba": ilosc, "cena": cena, 
                    "kategoria_id": kat_nazwa_na_id[kat_sel], "minimum": minimum
                }).execute()
                st.success("Produkt dodany!")
                st.rerun()

# ================== STATYSTYKI I KATEGORIE (Uproszczone dla czytelności) ==================
with tab2:
    st.header("Analityka zapasów")
    braki = [p for p in produkty if p['liczba'] <= p.get('minimum', 0)]
    st.metric("Produkty wymagające zamówienia", len(braki), delta=len(braki), delta_color="inverse")
    
    if braki:
        st.warning("Poniższe produkty są na wyczerpaniu:")
        st.write(", ".join([p['nazwa'] for p in braki]))

with tab4:
    # (Tutaj pozostaje Twój poprzedni kod do kategorii)
    st.info("Zarządzaj kategoriami jak wcześniej.")
