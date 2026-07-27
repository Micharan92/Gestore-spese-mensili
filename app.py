import streamlit

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Funzioni di Inizializzazione dello Stato --- #
def init_session_state():
    if 'monthly_salary' not in st.session_state:
        st.session_state.monthly_salary = None
    if 'expenses_df' not in st.session_state:
        st.session_state.expenses_df = pd.DataFrame(columns=['Nome Spesa', 'Costo Spesa'])
    if 'salary_set' not in st.session_state:
        st.session_state.salary_set = False
    if 'reset_pending' not in st.session_state:
        st.session_state.reset_pending = False

init_session_state()

# --- Funzione per rimuovere una spesa specifica --- #
def remove_expense(index):
    if index in st.session_state.expenses_df.index:
        st.session_state.expenses_df = st.session_state.expenses_df.drop(index=index).reset_index(drop=True)
        st.rerun()

# --- Funzione per generare i dati del grafico (robusta) --- #
def generate_pie_chart_data():
    if st.session_state.monthly_salary is None:
        return None, None, None
    
    # Crea una copia per lavorare in sicurezza
    df = st.session_state.expenses_df.copy()
    
    # Forza la colonna Costo Spesa a essere numerica, mettendo 0 dove ci sono errori
    df['Costo Spesa'] = pd.to_numeric(df['Costo Spesa'], errors='coerce').fillna(0)
    
    # Filtra solo spese positive
    valid_expenses = df[df['Costo Spesa'] > 0].copy()
    
    total_expenses = valid_expenses['Costo Spesa'].sum()
    chart_data = valid_expenses[['Nome Spesa', 'Costo Spesa']].copy()
    remaining_salary = st.session_state.monthly_salary - total_expenses

    if remaining_salary > 0:
        remaining_df = pd.DataFrame([{'Nome Spesa': 'Stipendio Rimanente', 'Costo Spesa': remaining_salary}])
        chart_data = pd.concat([chart_data, remaining_df], ignore_index=True)
    
    # Rimuove eventuali righe nulle residue e verifica che ci siano dati
    chart_data = chart_data.dropna()
    if chart_data.empty or chart_data['Costo Spesa'].sum() <= 0:
        return None, total_expenses, remaining_salary

    return chart_data, total_expenses, remaining_salary

# --- Funzione per il Grafico a Torta (blindata) --- #
def display_pie_chart():
    chart_data, _, _ = generate_pie_chart_data()
    
    if chart_data is None or chart_data.empty:
        st.write("Dati insufficienti per generare il grafico.")
        return

    try:
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax1.pie(
            chart_data['Costo Spesa'], 
            labels=chart_data['Nome Spesa'], 
            autopct='%1.1f%%', 
            startangle=90,
            pctdistance=0.85,
            wedgeprops=dict(width=0.3)
        )
        
        for autotext in autotexts:
            autotext.set_color('black') # Cambiato in black per leggibilità standard
            
        ax1.axis('equal')
        plt.title('Distribuzione Spese vs Stipendio', fontsize=16)
        st.pyplot(fig1)
    except Exception as e:
        st.error(f"Errore nella visualizzazione del grafico: {e}")

# --- Funzione per il Riepilogo --- #
def display_summary():
    if st.session_state.monthly_salary is None:
        st.write("Per favore, imposta prima lo stipendio mensile.")
        return

    st.write(f"**Stipendio Mensile:** €{st.session_state.monthly_salary:.2f}")

    if not st.session_state.expenses_df.empty:
        total_expenses = st.session_state.expenses_df['Costo Spesa'].sum()
        remaining_salary = st.session_state.monthly_salary - total_expenses

        st.write(f"**Totale Spese:** €{total_expenses:.2f}")
        st.write(f"**Stipendio Rimanente:** €{remaining_salary:.2f}")
        
        st.markdown("#### Dettaglio Spese:")
        for idx, row in st.session_state.expenses_df.iterrows():
            col_name, col_cost, col_remove = st.columns([3, 1.5, 0.5])
            col_name.write(f"• {row['Nome Spesa']}")
            col_cost.write(f"€{row['Costo Spesa']:.2f}")
            if col_remove.button("-", key=f"remove_expense_{idx}"):
                remove_expense(idx)
                break
        
        display_pie_chart()
    else:
        st.write("Nessuna spesa registrata.")
        st.write(f"**Stipendio Rimanente:** €{st.session_state.monthly_salary:.2f}")

# --- Layout dell'Applicazione --- #
st.title("Programma di Gestione delle Spese")

# --- 1. Gestione Stipendio --- #
st.header("1. Gestione Stipendio Mensile")

with st.form("salary_form"):
    salary_input_value = st.number_input(
        'Stipendio Mensile:', 
        min_value=0.0, 
        value=st.session_state.monthly_salary if st.session_state.monthly_salary is not None else 0.0,
        disabled=st.session_state.salary_set,
        format="%.2f"
    )
    submitted_salary = st.form_submit_button('Imposta Stipendio', disabled=st.session_state.salary_set)

    if submitted_salary:
        if salary_input_value > 0:
            st.session_state.monthly_salary = salary_input_value
            st.session_state.salary_set = True
            st.success(f"Stipendio mensile impostato a: €{st.session_state.monthly_salary:.2f}")
            st.rerun()
        else:
            st.error("Inserisci uno stipendio valido superiore a zero.")

# --- 2. Gestione Spese --- #
st.header("2. Gestione Spese")
col1, col2 = st.columns(2)

with col1:
    with st.form("expense_form", clear_on_submit=True):
        expense_name = st.text_input('Nome Spesa:', placeholder='Es. Affitto')
        expense_cost = st.number_input('Costo Spesa:', min_value=0.0, value=0.0, format="%.2f")
        submitted_expense = st.form_submit_button('Aggiungi Spesa')

        if submitted_expense:
            if expense_name and expense_cost > 0:
                new_row = pd.DataFrame([{'Nome Spesa': expense_name, 'Costo Spesa': expense_cost}])
                st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, new_row], ignore_index=True)
                st.rerun()
            else:
                st.error("Inserisci nome e costo validi.")

with col2:
    st.markdown("<br>", unsafe_allow_html=True) # Spazio per allineare

# --- 3. Riepilogo --- #
st.header("3. Riepilogo e Grafico")
display_summary()

# --- 4. Esporta --- #
st.header("4. Esporta Dati")
if not st.session_state.expenses_df.empty and st.session_state.monthly_salary is not None:
    csv = st.session_state.expenses_df.to_csv(index=False).encode('utf-8')
    st.download_button("Scarica CSV Spese", csv, "spese.csv", "text/csv")

# --- 5. Reset --- #
st.header("5. Reset Mese")
if st.button('Reset Mese'):
    st.session_state.reset_pending = True

if st.session_state.reset_pending:
    st.warning("Sei sicuro di voler azzerare tutto?")
    if st.button('Sì, conferma'):
        st.session_state.monthly_salary = None
        st.session_state.expenses_df = pd.DataFrame(columns=['Nome Spesa', 'Costo Spesa'])
        st.session_state.salary_set = False
        st.session_state.reset_pending = False
        st.rerun()
