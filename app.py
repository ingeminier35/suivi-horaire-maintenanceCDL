import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import time

# --- CONFIGURATION ---
fichier_db = 'heures_maintenance.csv'
MOT_DE_PASSE_ADMIN = "admin123"

st.set_page_config(page_title="Pointeuse Atelier", layout="wide")

# --- FONCTIONS UTILES ---
def charger_donnees():
    if not os.path.exists(fichier_db):
        df = pd.DataFrame(columns=['Date', 'Nom', 'Heures'])
        df.to_csv(fichier_db, index=False)
        return df
    try:
        return pd.read_csv(fichier_db)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=['Date', 'Nom', 'Heures'])

def sauvegarder_donnees(df):
    df.to_csv(fichier_db, index=False)

def get_start_of_week(date_ref):
    start = date_ref - timedelta(days=date_ref.weekday())
    return start

# --- INITIALISATION DE L'ÉTAT (Correction du bug de date ici) ---
if 'user' not in st.session_state:
    st.session_state.user = None

# On utilise le même nom de variable partout (date_reference)
if 'date_reference' not in st.session_state:
    st.session_state.date_reference = datetime.today()

if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False

# --- BARRE DU HAUT ---
col_logo, col_admin = st.columns([8, 1])
with col_admin:
    if st.button("🔒 ADMIN"):
        st.session_state.admin_mode = not st.session_state.admin_mode

# --- PARTIE ADMIN ---
if st.session_state.admin_mode:
    st.markdown("---")
    st.subheader("Espace Administrateur")
    mdp = st.text_input("Mot de passe", type="password")
    
    if mdp == MOT_DE_PASSE_ADMIN:
        st.success("Accès autorisé")
        df_complet = charger_donnees()
        st.write("Modifier n'importe quelle entrée :")
        df_edited = st.data_editor(df_complet, num_rows="dynamic", use_container_width=True)
        
        if st.button("Sauvegarder les modifications Admin"):
            sauvegarder_donnees(df_edited)
            st.success("Base de données mise à jour !")
            
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
        csv = convert_df(df_edited)
        st.download_button("📥 Télécharger Excel", csv, "releve_heures.csv", "text/csv")
    elif mdp:
        st.error("Mot de passe incorrect")
    st.markdown("---")

# --- PARTIE 1 : LOGIN ---
if st.session_state.user is None:
    col_vide1, col_login, col_vide2 = st.columns([1, 2, 1])
    with col_login:
        st.title("👋 Bonjour")
        st.write("Veuillez choisir votre profil.")
        liste_personnel = ["-- Choisir --", "Mélanie BOUVIER", "Christiant GEORGEAULT", "Aurélien LOUAPRE", "Ludovic VETTIER", "Ludovic BELINE", "Régis ANGER", "Clément MARTINEZ", "Richard LEBRUN", "Guillaume TREFOUEL"]
        choix = st.selectbox("Qui êtes-vous ?", liste_personnel)
        if st.button("VALIDER", use_container_width=True):
            if choix != "-- Choisir --":
                st.session_state.user = choix
                st.rerun()

# --- PARTIE 2 : TABLEAU SEMAINE ---
else:
    # En-tête avec bouton retour
    col_titre, col_btn = st.columns([6, 1])
    with col_titre:
        st.title(f"👤 {st.session_state.user}")
    with col_btn:
        if st.button("Déconnexion"):
            st.session_state.user = None
            st.rerun()

    st.markdown("---")

    # 1. Navigation & Calcul des dates
    lundi_actuel = get_start_of_week(st.session_state.date_reference)
    dimanche_actuel = lundi_actuel + timedelta(days=6)
    num_semaine = lundi_actuel.isocalendar()[1]

    # 2. Préparation des données
    df_global = charger_donnees()
    jours_semaine = []
    dates_semaine = []
    heures_existantes = []
    noms_jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    
    for i in range(7):
        jour_date = lundi_actuel + timedelta(days=i)
        str_date = jour_date.strftime('%Y-%m-%d')
        jours_semaine.append(noms_jours[i])
        dates_semaine.append(str_date)
        
        filtre = (df_global['Date'] == str_date) & (df_global['Nom'] == st.session_state.user)
        if not df_global[filtre].empty:
            heures_existantes.append(df_global[filtre].iloc[0]['Heures'])
        else:
            heures_existantes.append(0.0)

    df_semaine = pd.DataFrame({
        "Jour": jours_semaine,
        "Date": dates_semaine,
        "Heures": heures_existantes
    })

    # Calcul du total actuel
    total_heures_semaine = df_semaine['Heures'].sum()

    # 3. Affichage Navigation + Total
    col_prev, col_info, col_next, col_total = st.columns([1, 3, 1, 2])
    
    with col_prev:
        st.write("") # Espace pour aligner
        if st.button("◀ Préc."):
            st.session_state.date_reference -= timedelta(days=7)
            st.rerun()
            
    with col_info:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>Semaine {num_semaine}</h3>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; color: gray;'>{lundi_actuel.strftime('%d/%m')} au {dimanche_actuel.strftime('%d/%m')}</div>", unsafe_allow_html=True)
        
    with col_next:
        st.write("") 
        if st.button("Suiv. ▶"):
            st.session_state.date_reference += timedelta(days=7)
            st.rerun()

    with col_total:
        # Affichage du gros chiffre total
        st.metric(label="TOTAL SEMAINE", value=f"{total_heures_semaine} h")

    # 4. Tableau éditable
    config_colonnes = {
        "Date": st.column_config.TextColumn("Date", disabled=True),
        "Jour": st.column_config.TextColumn("Jour", disabled=True),
        "Heures": st.column_config.NumberColumn("Heures", min_value=0, max_value=24, step=0.5, format="%.1f h")
    }
    
    resultat_edit = st.data_editor(
        df_semaine, 
        column_config=config_colonnes, 
        use_container_width=True, 
        hide_index=True,
        key="editor_semaine"
    )

    # 5. Sauvegarde
    if st.button("💾 ENREGISTRER MA SEMAINE", type="primary", use_container_width=True):
        # Nettoyage des anciennes données de cette semaine
        for d in dates_semaine:
            df_global = df_global[~((df_global['Date'] == d) & (df_global['Nom'] == st.session_state.user))]
        
        # Ajout des nouvelles
        nouvelles_lignes = []
        for index, row in resultat_edit.iterrows():
            if row['Heures'] > 0:
                nouvelles_lignes.append({
                    'Date': row['Date'],
                    'Nom': st.session_state.user,
                    'Heures': row['Heures']
                })
        
        if nouvelles_lignes:
            df_nouveau = pd.DataFrame(nouvelles_lignes)
            df_global = pd.concat([df_global, df_nouveau], ignore_index=True)
        
        sauvegarder_donnees(df_global)
        st.success("✅ Semaine sauvegardée !")
        time.sleep(1)
        st.rerun()