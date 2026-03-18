import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Salon de Coiffure Dame",
    page_icon="💇‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "salon.db"

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Lato:wght@300;400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lato', sans-serif;
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #8B3A62 !important;
}

.stApp {
    background: linear-gradient(135deg, #FFF8F3 0%, #FDE8F0 100%);
}

.metric-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(139,58,98,0.10);
    border-left: 5px solid #C06490;
    margin-bottom: 10px;
}

.metric-card h2 {
    color: #8B3A62 !important;
    font-size: 2rem !important;
    margin: 0;
}

.metric-card p {
    color: #9B7B8B;
    margin: 0;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #8B3A62 0%, #5C1A3C 100%) !important;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

[data-testid="stSidebar"] .stRadio label {
    color: white !important;
}

.stButton > button {
    background: linear-gradient(135deg, #C06490, #8B3A62) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(139,58,98,0.3) !important;
}

.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
}

div[data-testid="stExpander"] {
    background: white;
    border-radius: 12px;
    border: 1px solid #F0D0E0;
    padding: 5px;
}

.success-box {
    background: #E8F8F0;
    border: 1px solid #27AE60;
    border-radius: 10px;
    padding: 12px;
    color: #1E8449;
    margin: 10px 0;
}

.warning-box {
    background: #FEF9E7;
    border: 1px solid #F39C12;
    border-radius: 10px;
    padding: 12px;
    color: #9A7D0A;
    margin: 10px 0;
}

.stSelectbox > div, .stTextInput > div > input, .stNumberInput > div > input {
    border-radius: 10px !important;
    border-color: #E8C0D0 !important;
}

.header-banner {
    background: linear-gradient(135deg, #8B3A62, #C06490, #E8A0BC);
    color: white;
    padding: 20px 30px;
    border-radius: 20px;
    margin-bottom: 30px;
    text-align: center;
    box-shadow: 0 8px 30px rgba(139,58,98,0.25);
}

.header-banner h1 {
    color: white !important;
    font-size: 2.2rem !important;
    margin: 0 !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.header-banner p {
    color: #FFE0EE;
    margin-top: 5px;
    font-size: 1rem;
}

.rdv-card {
    background: white;
    border-radius: 14px;
    padding: 15px 20px;
    margin: 8px 0;
    box-shadow: 0 2px 12px rgba(139,58,98,0.08);
    border-left: 4px solid #C06490;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.stock-alert {
    background: #FFF0F0;
    border: 1px solid #E74C3C;
    border-radius: 10px;
    padding: 10px 15px;
    color: #C0392B;
}
</style>
""", unsafe_allow_html=True)

# ─── DATABASE ─────────────────────────────────────────────────────────────────
def get_db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT,
        telephone TEXT,
        email TEXT,
        notes TEXT,
        date_creation TEXT DEFAULT CURRENT_DATE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        categorie TEXT,
        prix REAL NOT NULL,
        duree_min INTEGER DEFAULT 30,
        description TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS rendez_vous (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        service_id INTEGER,
        date_rdv TEXT NOT NULL,
        heure_rdv TEXT NOT NULL,
        statut TEXT DEFAULT 'Confirmé',
        notes TEXT,
        prix_applique REAL,
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(service_id) REFERENCES services(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS recettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_recette TEXT NOT NULL,
        rdv_id INTEGER,
        montant REAL NOT NULL,
        mode_paiement TEXT DEFAULT 'Espèces',
        description TEXT,
        FOREIGN KEY(rdv_id) REFERENCES rendez_vous(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        categorie TEXT,
        quantite REAL DEFAULT 0,
        unite TEXT DEFAULT 'unité',
        prix_achat REAL DEFAULT 0,
        prix_vente REAL DEFAULT 0,
        seuil_alerte INTEGER DEFAULT 5,
        fournisseur TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS mouvements_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER,
        type_mouvement TEXT,
        quantite REAL,
        date_mouvement TEXT DEFAULT CURRENT_DATE,
        notes TEXT,
        FOREIGN KEY(produit_id) REFERENCES produits(id)
    )""")

    # Seed services by default
    c.execute("SELECT COUNT(*) FROM services")
    if c.fetchone()[0] == 0:
        services_defaut = [
            ("Coupe femme", "Coupe", 1200, 45, "Coupe + brushing"),
            ("Coupe + Brushing", "Coupe", 1800, 60, "Coupe cheveux + brushing professionnel"),
            ("Brushing", "Brushing", 800, 30, "Brushing simple"),
            ("Coloration complète", "Couleur", 4500, 120, "Coloration racines + longueurs"),
            ("Mèches", "Couleur", 5500, 150, "Mèches balayage"),
            ("Henné", "Couleur", 2500, 90, "Application henné naturel"),
            ("Lissage brésilien", "Traitement", 8000, 180, "Lissage kératine"),
            ("Permanente", "Traitement", 5000, 120, "Permanente classique"),
            ("Soin nourrissant", "Soin", 1500, 45, "Masque + soin profond"),
            ("Manucure", "Ongles", 1000, 45, "Soin + vernis"),
            ("Pédicure", "Ongles", 1200, 60, "Soin complet pieds"),
            ("Epilation visage", "Epilation", 500, 20, "Sourcils + lèvres + menton"),
            ("Epilation jambes", "Epilation", 1500, 45, "Jambes complètes"),
            ("Mariage - Coiffure", "Mariage", 15000, 180, "Coiffure mariée complète"),
            ("Tresses", "Coiffure", 3000, 120, "Tresses africaines"),
        ]
        c.executemany("INSERT INTO services(nom,categorie,prix,duree_min,description) VALUES(?,?,?,?,?)", services_defaut)

    conn.commit()
    conn.close()

init_db()

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def fmt_dzd(val):
    return f"{val:,.0f} DA"

def run_query(sql, params=()):
    conn = get_db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = get_db()
    conn.execute(sql, params)
    conn.commit()
    conn.close()

def executemany(sql, data):
    conn = get_db()
    conn.executemany(sql, data)
    conn.commit()
    conn.close()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💇‍♀️ Salon Elite")
    st.markdown("---")
    page = st.radio("Navigation", [
        "🏠 Tableau de bord",
        "📅 Rendez-vous",
        "👩 Clients",
        "✂️ Services & Prix",
        "📦 Stock",
        "💰 Recettes",
        "📊 Rapports",
    ])
    st.markdown("---")
    st.markdown(f"<small>📆 {datetime.now().strftime('%d/%m/%Y')}</small>", unsafe_allow_html=True)
    st.markdown(f"<small>🕐 {datetime.now().strftime('%H:%M')}</small>", unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
  <h1>💇‍♀️ Salon de Coiffure Dame</h1>
  <p>Gestion professionnelle de votre salon — Prix en Dinars Algériens</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TABLEAU DE BORD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Tableau de bord":
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()
    year_start  = date.today().replace(month=1, day=1).isoformat()

    rec_jour  = run_query("SELECT COALESCE(SUM(montant),0) as t FROM recettes WHERE date_recette=?", (today,))
    rec_mois  = run_query("SELECT COALESCE(SUM(montant),0) as t FROM recettes WHERE date_recette>=?", (month_start,))
    rec_annee = run_query("SELECT COALESCE(SUM(montant),0) as t FROM recettes WHERE date_recette>=?", (year_start,))
    rdv_jour  = run_query("SELECT COUNT(*) as n FROM rendez_vous WHERE date_rdv=?", (today,))
    nb_clients= run_query("SELECT COUNT(*) as n FROM clients")
    stocks_alerte = run_query("SELECT COUNT(*) as n FROM produits WHERE quantite <= seuil_alerte")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card"><p>💰 Recette du jour</p><h2>{fmt_dzd(rec_jour['t'].iloc[0])}</h2></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card"><p>📅 Recette du mois</p><h2>{fmt_dzd(rec_mois['t'].iloc[0])}</h2></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card"><p>📆 Recette annuelle</p><h2>{fmt_dzd(rec_annee['t'].iloc[0])}</h2></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card"><p>📋 RDV aujourd'hui</p><h2>{rdv_jour['n'].iloc[0]}</h2></div>""", unsafe_allow_html=True)

    st.markdown("")
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("📈 Recettes — 30 derniers jours")
        df30 = run_query("""
            SELECT date_recette as Date, COALESCE(SUM(montant),0) as Montant
            FROM recettes
            WHERE date_recette >= date('now','-30 days')
            GROUP BY date_recette ORDER BY date_recette
        """)
        if not df30.empty:
            fig = px.area(df30, x="Date", y="Montant", color_discrete_sequence=["#C06490"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              yaxis_title="DA", xaxis_title="", margin=dict(t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune recette enregistrée encore.")

    with col_r:
        st.subheader("🥧 Recettes par service")
        df_svc = run_query("""
            SELECT s.categorie as Categorie, SUM(r.prix_applique) as Total
            FROM rendez_vous r JOIN services s ON r.service_id=s.id
            WHERE r.statut='Terminé'
            GROUP BY s.categorie ORDER BY Total DESC
        """)
        if not df_svc.empty:
            fig2 = px.pie(df_svc, names="Categorie", values="Total",
                          color_discrete_sequence=px.colors.sequential.RdPu)
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10,b=10))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucune donnée encore.")

    st.subheader("📋 Rendez-vous d'aujourd'hui")
    rdv_auj = run_query("""
        SELECT rv.heure_rdv as Heure, c.nom||' '||COALESCE(c.prenom,'') as Client,
               s.nom as Service, rv.prix_applique as Prix, rv.statut as Statut
        FROM rendez_vous rv
        JOIN clients c ON rv.client_id=c.id
        JOIN services s ON rv.service_id=s.id
        WHERE rv.date_rdv=? ORDER BY rv.heure_rdv
    """, (today,))
    if rdv_auj.empty:
        st.info("Aucun rendez-vous aujourd'hui.")
    else:
        for _, row in rdv_auj.iterrows():
            color = "#27AE60" if row['Statut']=="Terminé" else "#F39C12" if row['Statut']=="En cours" else "#3498DB"
            st.markdown(f"""
            <div class="rdv-card">
                <div>
                    <strong>⏰ {row['Heure']}</strong> — {row['Client']}
                    <br><span style="color:#9B7B8B">{row['Service']}</span>
                </div>
                <div style="text-align:right">
                    <strong style="color:#8B3A62">{fmt_dzd(row['Prix'])}</strong><br>
                    <span style="color:{color}; font-size:0.85rem">● {row['Statut']}</span>
                </div>
            </div>""", unsafe_allow_html=True)

    if stocks_alerte['n'].iloc[0] > 0:
        st.markdown(f"""<div class="stock-alert">⚠️ <strong>{stocks_alerte['n'].iloc[0]} produit(s)</strong> en stock bas — Vérifiez le stock !</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RENDEZ-VOUS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Rendez-vous":
    st.subheader("📅 Gestion des Rendez-vous")

    tab1, tab2, tab3 = st.tabs(["➕ Nouveau RDV", "📋 Liste RDV", "✏️ Modifier / Annuler"])

    with tab1:
        clients_df = run_query("SELECT id, nom||' '||COALESCE(prenom,'') as label FROM clients ORDER BY nom")
        services_df = run_query("SELECT id, nom, prix, duree_min FROM services ORDER BY categorie, nom")

        if clients_df.empty:
            st.warning("⚠️ Aucun client. Ajoutez d'abord un client dans l'onglet Clients.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                client_options = dict(zip(clients_df['label'], clients_df['id']))
                client_sel = st.selectbox("👩 Cliente", list(client_options.keys()))
                date_rdv = st.date_input("📅 Date", min_value=date.today())
                heure_rdv = st.time_input("⏰ Heure", value=datetime.strptime("09:00", "%H:%M").time())
                statut_rdv = st.selectbox("📌 Statut", ["Confirmé", "En attente", "En cours", "Terminé", "Annulé"])

            with col2:
                svc_options = {f"{r['nom']} — {fmt_dzd(r['prix'])} (~{r['duree_min']} min)": (r['id'], r['prix']) for _, r in services_df.iterrows()}
                svc_sel = st.selectbox("✂️ Service", list(svc_options.keys()))
                svc_id, svc_prix = svc_options[svc_sel]
                prix_app = st.number_input("💰 Prix appliqué (DA)", min_value=0.0, value=float(svc_prix), step=50.0)
                notes_rdv = st.text_area("📝 Notes", height=80)

            if st.button("✅ Enregistrer le rendez-vous", use_container_width=True):
                client_id = client_options[client_sel]
                execute("""INSERT INTO rendez_vous(client_id,service_id,date_rdv,heure_rdv,statut,notes,prix_applique)
                           VALUES(?,?,?,?,?,?,?)""",
                        (client_id, svc_id, date_rdv.isoformat(), heure_rdv.strftime("%H:%M"), statut_rdv, notes_rdv, prix_app))
                if statut_rdv == "Terminé":
                    execute("INSERT INTO recettes(date_recette,montant,mode_paiement,description) VALUES(?,?,?,?)",
                            (date_rdv.isoformat(), prix_app, "Espèces", f"RDV - {svc_sel[:40]}"))
                st.success("✅ Rendez-vous enregistré !")
                st.rerun()

    with tab2:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtre_date = st.date_input("Filtrer par date", value=date.today())
        with col_f2:
            filtre_statut = st.selectbox("Statut", ["Tous", "Confirmé", "En attente", "En cours", "Terminé", "Annulé"])

        sql_rdv = """
            SELECT rv.id, rv.heure_rdv as Heure, c.nom||' '||COALESCE(c.prenom,'') as Cliente,
                   c.telephone as Tel, s.nom as Service, rv.prix_applique as Prix,
                   rv.statut as Statut, rv.notes as Notes
            FROM rendez_vous rv
            JOIN clients c ON rv.client_id=c.id
            JOIN services s ON rv.service_id=s.id
            WHERE rv.date_rdv=?
        """
        params = [filtre_date.isoformat()]
        if filtre_statut != "Tous":
            sql_rdv += " AND rv.statut=?"
            params.append(filtre_statut)
        sql_rdv += " ORDER BY rv.heure_rdv"

        df_rdv = run_query(sql_rdv, tuple(params))
        if df_rdv.empty:
            st.info("Aucun rendez-vous pour cette date.")
        else:
            df_display = df_rdv.drop(columns=['id','Notes']).copy()
            df_display['Prix'] = df_display['Prix'].apply(fmt_dzd)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            total_jour = df_rdv[df_rdv['Statut']=='Terminé']['Prix'].sum()
            st.markdown(f"**Total encaissé :** `{fmt_dzd(total_jour)}`")

    with tab3:
        rdv_list = run_query("""
            SELECT rv.id, rv.date_rdv||' '||rv.heure_rdv||' — '||c.nom||' — '||s.nom as label,
                   rv.statut, rv.prix_applique
            FROM rendez_vous rv
            JOIN clients c ON rv.client_id=c.id
            JOIN services s ON rv.service_id=s.id
            ORDER BY rv.date_rdv DESC, rv.heure_rdv DESC LIMIT 50
        """)
        if rdv_list.empty:
            st.info("Aucun rendez-vous.")
        else:
            options = dict(zip(rdv_list['label'], rdv_list['id']))
            sel = st.selectbox("Sélectionner un RDV", list(options.keys()))
            rdv_id = options[sel]
            rdv_row = rdv_list[rdv_list['id']==rdv_id].iloc[0]

            new_statut = st.selectbox("Nouveau statut", ["Confirmé","En attente","En cours","Terminé","Annulé"],
                                       index=["Confirmé","En attente","En cours","Terminé","Annulé"].index(rdv_row['statut']))
            new_prix = st.number_input("Prix (DA)", value=float(rdv_row['prix_applique']), step=50.0)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Mettre à jour", use_container_width=True):
                    execute("UPDATE rendez_vous SET statut=?, prix_applique=? WHERE id=?",
                            (new_statut, new_prix, rdv_id))
                    if new_statut == "Terminé":
                        exist = run_query("SELECT id FROM recettes WHERE rdv_id=?", (rdv_id,))
                        if exist.empty:
                            rv_info = run_query("SELECT date_rdv FROM rendez_vous WHERE id=?", (rdv_id,))
                            execute("INSERT INTO recettes(date_recette,rdv_id,montant,mode_paiement) VALUES(?,?,?,?)",
                                    (rv_info['date_rdv'].iloc[0], rdv_id, new_prix, "Espèces"))
                    st.success("Mis à jour !")
                    st.rerun()
            with col_btn2:
                if st.button("🗑️ Supprimer", use_container_width=True):
                    execute("DELETE FROM rendez_vous WHERE id=?", (rdv_id,))
                    st.success("Supprimé.")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CLIENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👩 Clients":
    st.subheader("👩 Gestion des Clients")
    tab1, tab2 = st.tabs(["➕ Ajouter / Modifier", "📋 Liste clients"])

    with tab1:
        clients_df = run_query("SELECT id, nom||' '||COALESCE(prenom,'') as label FROM clients ORDER BY nom")
        mode = st.radio("Mode", ["Nouveau client", "Modifier existant"], horizontal=True)

        if mode == "Modifier existant" and not clients_df.empty:
            options = dict(zip(clients_df['label'], clients_df['id']))
            sel = st.selectbox("Choisir client", list(options.keys()))
            cid = options[sel]
            row = run_query("SELECT * FROM clients WHERE id=?", (cid,)).iloc[0]
        else:
            row = None; cid = None

        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom *", value=row['nom'] if row is not None else "")
            prenom = st.text_input("Prénom", value=row['prenom'] if row is not None and row['prenom'] else "")
            telephone = st.text_input("📞 Téléphone", value=row['telephone'] if row is not None and row['telephone'] else "")
        with col2:
            email = st.text_input("📧 Email", value=row['email'] if row is not None and row['email'] else "")
            notes = st.text_area("📝 Notes", value=row['notes'] if row is not None and row['notes'] else "", height=100)

        if st.button("✅ Enregistrer", use_container_width=True):
            if not nom:
                st.error("Le nom est obligatoire !")
            elif mode == "Nouveau client":
                execute("INSERT INTO clients(nom,prenom,telephone,email,notes) VALUES(?,?,?,?,?)",
                        (nom, prenom, telephone, email, notes))
                st.success("✅ Client ajouté !")
                st.rerun()
            else:
                execute("UPDATE clients SET nom=?,prenom=?,telephone=?,email=?,notes=? WHERE id=?",
                        (nom, prenom, telephone, email, notes, cid))
                st.success("✅ Client mis à jour !")
                st.rerun()

    with tab2:
        search = st.text_input("🔍 Rechercher", placeholder="Nom, téléphone...")
        if search:
            df_cl = run_query(f"""SELECT c.id, c.nom, c.prenom, c.telephone, c.email, c.date_creation,
                COUNT(rv.id) as nb_rdv, COALESCE(SUM(rv.prix_applique),0) as total_depense
                FROM clients c LEFT JOIN rendez_vous rv ON c.id=rv.client_id
                WHERE c.nom LIKE ? OR c.telephone LIKE ?
                GROUP BY c.id ORDER BY c.nom""",
                (f"%{search}%", f"%{search}%"))
        else:
            df_cl = run_query("""SELECT c.id, c.nom, c.prenom, c.telephone, c.email, c.date_creation,
                COUNT(rv.id) as nb_rdv, COALESCE(SUM(rv.prix_applique),0) as total_depense
                FROM clients c LEFT JOIN rendez_vous rv ON c.id=rv.client_id
                GROUP BY c.id ORDER BY c.nom""")
        if not df_cl.empty:
            df_cl['total_depense'] = df_cl['total_depense'].apply(fmt_dzd)
            st.dataframe(df_cl.drop(columns=['id']), use_container_width=True, hide_index=True)
            st.caption(f"Total : {len(df_cl)} cliente(s)")
        else:
            st.info("Aucune cliente trouvée.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SERVICES & PRIX
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✂️ Services & Prix":
    st.subheader("✂️ Services & Tarifs")
    tab1, tab2 = st.tabs(["➕ Ajouter / Modifier", "📋 Grille tarifaire"])

    with tab1:
        svc_df = run_query("SELECT id, nom FROM services ORDER BY categorie,nom")
        mode = st.radio("Mode", ["Nouveau service", "Modifier existant"], horizontal=True)

        row = None; sid = None
        if mode == "Modifier existant" and not svc_df.empty:
            opts = dict(zip(svc_df['nom'], svc_df['id']))
            sel = st.selectbox("Service", list(opts.keys()))
            sid = opts[sel]
            row = run_query("SELECT * FROM services WHERE id=?", (sid,)).iloc[0]

        cats = ["Coupe","Brushing","Couleur","Traitement","Soin","Ongles","Epilation","Mariage","Coiffure","Autre"]
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom du service *", value=row['nom'] if row is not None else "")
            cat_idx = cats.index(row['categorie']) if row is not None and row['categorie'] in cats else 0
            cat = st.selectbox("Catégorie", cats, index=cat_idx)
            prix = st.number_input("💰 Prix (DA)", min_value=0.0, value=float(row['prix']) if row is not None else 1000.0, step=50.0)
        with col2:
            duree = st.number_input("⏱ Durée (min)", min_value=5, value=int(row['duree_min']) if row is not None else 30, step=5)
            desc = st.text_area("Description", value=row['description'] if row is not None and row['description'] else "", height=80)

        if st.button("✅ Enregistrer le service", use_container_width=True):
            if not nom:
                st.error("Le nom est obligatoire !")
            elif mode == "Nouveau service":
                execute("INSERT INTO services(nom,categorie,prix,duree_min,description) VALUES(?,?,?,?,?)",
                        (nom, cat, prix, duree, desc))
                st.success("✅ Service ajouté !")
                st.rerun()
            else:
                execute("UPDATE services SET nom=?,categorie=?,prix=?,duree_min=?,description=? WHERE id=?",
                        (nom, cat, prix, duree, desc, sid))
                st.success("✅ Service mis à jour !")
                st.rerun()

    with tab2:
        df_svc = run_query("SELECT categorie as Catégorie, nom as Service, prix as Prix, duree_min as Durée_min, description as Description FROM services ORDER BY categorie, prix")
        if not df_svc.empty:
            df_svc['Prix'] = df_svc['Prix'].apply(fmt_dzd)
            cats = df_svc['Catégorie'].unique()
            for cat in cats:
                st.markdown(f"#### 🏷️ {cat}")
                sub = df_svc[df_svc['Catégorie']==cat].drop(columns=['Catégorie'])
                st.dataframe(sub, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun service enregistré.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: STOCK
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📦 Stock":
    st.subheader("📦 Gestion du Stock")
    tab1, tab2, tab3 = st.tabs(["➕ Produit", "📥 Mouvement", "📋 État du stock"])

    with tab1:
        prod_df = run_query("SELECT id, nom FROM produits ORDER BY nom")
        mode = st.radio("Mode", ["Nouveau produit", "Modifier existant"], horizontal=True)
        row = None; pid = None
        if mode == "Modifier existant" and not prod_df.empty:
            opts = dict(zip(prod_df['nom'], prod_df['id']))
            sel = st.selectbox("Produit", list(opts.keys()))
            pid = opts[sel]
            row = run_query("SELECT * FROM produits WHERE id=?", (pid,)).iloc[0]

        cats_p = ["Shampooing","Après-shampooing","Coloration","Soin","Outil","Accessoire","Produit chimique","Autre"]
        col1, col2 = st.columns(2)
        with col1:
            nom_p = st.text_input("Nom produit *", value=row['nom'] if row is not None else "")
            cat_p_idx = cats_p.index(row['categorie']) if row is not None and row['categorie'] in cats_p else 0
            cat_p = st.selectbox("Catégorie", cats_p, index=cat_p_idx)
            unite = st.text_input("Unité", value=row['unite'] if row is not None else "unité")
            qte_init = st.number_input("Quantité initiale", min_value=0.0, value=float(row['quantite']) if row is not None else 0.0)
        with col2:
            prix_achat = st.number_input("Prix achat (DA)", min_value=0.0, value=float(row['prix_achat']) if row is not None else 0.0, step=50.0)
            prix_vente = st.number_input("Prix vente (DA)", min_value=0.0, value=float(row['prix_vente']) if row is not None else 0.0, step=50.0)
            seuil = st.number_input("⚠️ Seuil alerte", min_value=0, value=int(row['seuil_alerte']) if row is not None else 5)
            fournisseur = st.text_input("Fournisseur", value=row['fournisseur'] if row is not None and row['fournisseur'] else "")

        if st.button("✅ Enregistrer produit", use_container_width=True):
            if not nom_p:
                st.error("Le nom est obligatoire !")
            elif mode == "Nouveau produit":
                execute("INSERT INTO produits(nom,categorie,quantite,unite,prix_achat,prix_vente,seuil_alerte,fournisseur) VALUES(?,?,?,?,?,?,?,?)",
                        (nom_p, cat_p, qte_init, unite, prix_achat, prix_vente, seuil, fournisseur))
                st.success("✅ Produit ajouté !")
                st.rerun()
            else:
                execute("UPDATE produits SET nom=?,categorie=?,quantite=?,unite=?,prix_achat=?,prix_vente=?,seuil_alerte=?,fournisseur=? WHERE id=?",
                        (nom_p, cat_p, qte_init, unite, prix_achat, prix_vente, seuil, fournisseur, pid))
                st.success("✅ Produit mis à jour !")
                st.rerun()

    with tab2:
        prod_df2 = run_query("SELECT id, nom, quantite, unite FROM produits ORDER BY nom")
        if prod_df2.empty:
            st.info("Aucun produit. Ajoutez d'abord des produits.")
        else:
            opts2 = {f"{r['nom']} (Stock: {r['quantite']} {r['unite']})": r['id'] for _, r in prod_df2.iterrows()}
            sel2 = st.selectbox("Produit", list(opts2.keys()))
            pid2 = opts2[sel2]
            col1, col2 = st.columns(2)
            with col1:
                type_mouv = st.selectbox("Type", ["Entrée (réception)", "Sortie (utilisation)", "Sortie (vente)", "Ajustement"])
            with col2:
                qte_mouv = st.number_input("Quantité", min_value=0.0, step=1.0)
            notes_mouv = st.text_input("Notes")

            if st.button("✅ Enregistrer mouvement", use_container_width=True):
                if qte_mouv <= 0:
                    st.error("Quantité doit être > 0")
                else:
                    execute("INSERT INTO mouvements_stock(produit_id,type_mouvement,quantite,notes) VALUES(?,?,?,?)",
                            (pid2, type_mouv, qte_mouv, notes_mouv))
                    if "Entrée" in type_mouv:
                        execute("UPDATE produits SET quantite=quantite+? WHERE id=?", (qte_mouv, pid2))
                    elif "Sortie" in type_mouv:
                        execute("UPDATE produits SET quantite=MAX(0,quantite-?) WHERE id=?", (qte_mouv, pid2))
                    else:
                        execute("UPDATE produits SET quantite=? WHERE id=?", (qte_mouv, pid2))
                    st.success("✅ Mouvement enregistré !")
                    st.rerun()

    with tab3:
        df_stock = run_query("SELECT nom as Produit, categorie as Catégorie, quantite as Quantité, unite as Unité, prix_achat as Prix_Achat, prix_vente as Prix_Vente, seuil_alerte as Seuil, fournisseur as Fournisseur FROM produits ORDER BY categorie, nom")
        if df_stock.empty:
            st.info("Aucun produit.")
        else:
            alertes = df_stock[df_stock['Quantité'] <= df_stock['Seuil']]
            if not alertes.empty:
                st.markdown(f"""<div class="stock-alert">⚠️ <strong>{len(alertes)} produit(s) en stock bas !</strong></div>""", unsafe_allow_html=True)
                st.dataframe(alertes[['Produit','Quantité','Seuil','Unité']], use_container_width=True, hide_index=True)

            df_stock['Prix_Achat'] = df_stock['Prix_Achat'].apply(fmt_dzd)
            df_stock['Prix_Vente'] = df_stock['Prix_Vente'].apply(fmt_dzd)
            st.dataframe(df_stock, use_container_width=True, hide_index=True)

            hist = run_query("""
                SELECT m.date_mouvement as Date, p.nom as Produit, m.type_mouvement as Type,
                       m.quantite as Quantité, m.notes as Notes
                FROM mouvements_stock m JOIN produits p ON m.produit_id=p.id
                ORDER BY m.id DESC LIMIT 30
            """)
            if not hist.empty:
                with st.expander("📜 Historique des mouvements (30 derniers)"):
                    st.dataframe(hist, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RECETTES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Recettes":
    st.subheader("💰 Gestion des Recettes")
    tab1, tab2 = st.tabs(["➕ Enregistrer recette", "📋 Historique"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            date_rec = st.date_input("Date", value=date.today())
            montant = st.number_input("💰 Montant (DA)", min_value=0.0, step=50.0)
        with col2:
            mode_paiement = st.selectbox("Mode de paiement", ["Espèces","CCP","Carte","Virement","Autre"])
            desc_rec = st.text_input("Description / Prestation")

        if st.button("✅ Enregistrer la recette", use_container_width=True):
            if montant <= 0:
                st.error("Montant doit être > 0")
            else:
                execute("INSERT INTO recettes(date_recette,montant,mode_paiement,description) VALUES(?,?,?,?)",
                        (date_rec.isoformat(), montant, mode_paiement, desc_rec))
                st.success(f"✅ Recette de {fmt_dzd(montant)} enregistrée !")
                st.rerun()

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            date_debut = st.date_input("Du", value=date.today().replace(day=1))
        with col2:
            date_fin = st.date_input("Au", value=date.today())

        df_rec = run_query("""
            SELECT date_recette as Date, montant as Montant, mode_paiement as Paiement, description as Description
            FROM recettes WHERE date_recette BETWEEN ? AND ?
            ORDER BY date_recette DESC
        """, (date_debut.isoformat(), date_fin.isoformat()))

        if not df_rec.empty:
            total = df_rec['Montant'].sum()
            st.markdown(f"**Total période : `{fmt_dzd(total)}`** sur {len(df_rec)} opération(s)")
            df_rec['Montant'] = df_rec['Montant'].apply(fmt_dzd)
            st.dataframe(df_rec, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune recette sur cette période.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RAPPORTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Rapports":
    st.subheader("📊 Rapports & Statistiques")

    rapport_type = st.selectbox("Type de rapport", ["Journalier", "Mensuel", "Annuel", "Services populaires", "Clientes fidèles"])

    if rapport_type == "Journalier":
        d = st.date_input("Choisir le jour", value=date.today())
        df = run_query("""
            SELECT r.montant, r.mode_paiement, r.description
            FROM recettes r WHERE r.date_recette=?
        """, (d.isoformat(),))
        total = df['montant'].sum() if not df.empty else 0
        nb_rdv = run_query("SELECT COUNT(*) as n FROM rendez_vous WHERE date_rdv=?", (d.isoformat(),))['n'].iloc[0]
        c1,c2,c3 = st.columns(3)
        c1.metric("💰 Recette", fmt_dzd(total))
        c2.metric("📋 RDV", nb_rdv)
        c3.metric("💳 Moyenne/RDV", fmt_dzd(total/nb_rdv) if nb_rdv>0 else "—")
        if not df.empty:
            fig = px.pie(df, names='mode_paiement', values='montant', title="Par mode de paiement",
                         color_discrete_sequence=px.colors.sequential.RdPu)
            st.plotly_chart(fig, use_container_width=True)

    elif rapport_type == "Mensuel":
        col1, col2 = st.columns(2)
        with col1: mois = st.selectbox("Mois", list(range(1,13)), index=date.today().month-1, format_func=lambda m: ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"][m-1])
        with col2: annee = st.number_input("Année", min_value=2020, max_value=2030, value=date.today().year)
        debut = f"{annee}-{mois:02d}-01"
        import calendar
        fin = f"{annee}-{mois:02d}-{calendar.monthrange(annee,mois)[1]}"
        df_m = run_query("SELECT date_recette as Jour, SUM(montant) as Total FROM recettes WHERE date_recette BETWEEN ? AND ? GROUP BY date_recette ORDER BY date_recette", (debut, fin))
        total_m = df_m['Total'].sum() if not df_m.empty else 0
        nb_rdv_m = run_query("SELECT COUNT(*) as n FROM rendez_vous WHERE date_rdv BETWEEN ? AND ?", (debut, fin))['n'].iloc[0]
        c1,c2 = st.columns(2)
        c1.metric("💰 Recette du mois", fmt_dzd(total_m))
        c2.metric("📋 Total RDV", nb_rdv_m)
        if not df_m.empty:
            fig = px.bar(df_m, x='Jour', y='Total', color_discrete_sequence=["#C06490"], title="Recettes journalières")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    elif rapport_type == "Annuel":
        annee = st.number_input("Année", min_value=2020, max_value=2030, value=date.today().year)
        df_a = run_query("""
            SELECT strftime('%m',date_recette) as Mois, SUM(montant) as Total
            FROM recettes WHERE strftime('%Y',date_recette)=? GROUP BY Mois ORDER BY Mois
        """, (str(annee),))
        mois_labels = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
        total_a = df_a['Total'].sum() if not df_a.empty else 0
        st.metric("💰 Recette annuelle", fmt_dzd(total_a))
        if not df_a.empty:
            df_a['Mois'] = df_a['Mois'].apply(lambda x: mois_labels[int(x)-1])
            fig = px.bar(df_a, x='Mois', y='Total', color_discrete_sequence=["#8B3A62"], title=f"Recettes {annee}")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    elif rapport_type == "Services populaires":
        df_svc = run_query("""
            SELECT s.nom as Service, s.categorie as Catégorie,
                   COUNT(rv.id) as Nb_RDV, SUM(rv.prix_applique) as Recette_Total
            FROM rendez_vous rv JOIN services s ON rv.service_id=s.id
            WHERE rv.statut='Terminé'
            GROUP BY s.id ORDER BY Nb_RDV DESC LIMIT 15
        """)
        if not df_svc.empty:
            fig = px.bar(df_svc, x='Service', y='Nb_RDV', color='Catégorie',
                         title="Services les plus demandés",
                         color_discrete_sequence=px.colors.sequential.RdPu)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            df_svc['Recette_Total'] = df_svc['Recette_Total'].apply(fmt_dzd)
            st.dataframe(df_svc, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée.")

    elif rapport_type == "Clientes fidèles":
        df_top = run_query("""
            SELECT c.nom||' '||COALESCE(c.prenom,'') as Cliente, c.telephone as Tel,
                   COUNT(rv.id) as Nb_Visites, SUM(rv.prix_applique) as Total_Depense
            FROM clients c JOIN rendez_vous rv ON c.id=rv.client_id
            WHERE rv.statut='Terminé'
            GROUP BY c.id ORDER BY Nb_Visites DESC LIMIT 15
        """)
        if not df_top.empty:
            fig = px.bar(df_top, x='Cliente', y='Nb_Visites', title="Clientes les plus fidèles",
                         color_discrete_sequence=["#C06490"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            df_top['Total_Depense'] = df_top['Total_Depense'].apply(fmt_dzd)
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée.")
