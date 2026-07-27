import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64
import io

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

# --- Funzione per generare i dati del grafico (riutilizzabile) --- #
def generate_pie_chart_data():
    if st.session_state.expenses_df.empty or st.session_state.monthly_salary is None:
        return None, None, None

    # Filtra le spese con costo positivo per evitare errori nel grafico a torta
    valid_expenses = st.session_state.expenses_df[st.session_state.expenses_df['Costo Spesa'] > 0]
    if valid_expenses.empty:
        return None, None, None

    total_expenses = valid_expenses['Costo Spesa'].sum()
    chart_data = valid_expenses[['Nome Spesa', 'Costo Spesa']].copy()
    remaining_salary = st.session_state.monthly_salary - total_expenses

    if remaining_salary > 0:
        chart_data = pd.concat([
            chart_data,
            pd.DataFrame([{'Nome Spesa': 'Stipendio Rimanente', 'Costo Spesa': remaining_salary}])
        ], ignore_index=True)
    
    return chart_data, total_expenses, remaining_salary

# --- Funzione per il Grafico a Torta --- #
def display_pie_chart():
    chart_data, _, _ = generate_pie_chart_data()
    if chart_data is None:
        st.write("Nessuna spesa valida per il grafico o stipendio non impostato.")
        return

    fig1, ax1 = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax1.pie(chart_data['Costo Spesa'], 
                                      labels=chart_data['Nome Spesa'], 
                                      autopct='%1.1f%%', 
                                      startangle=90,
                                      pctdistance=0.85,
                                      wedgeprops=dict(width=0.3) # Renderizza come ciambella
                                      )
    
    # Rende le percentuali bianche per una migliore leggibilità su sfondi scuri
    for autotext in autotexts:
        autotext.set_color('white')

    ax1.axis('equal') # Assicura che la torta sia disegnata come un cerchio.
    plt.title('Percentuale Spese in Relazione allo Stipendio (con rimanenza)', fontsize=16)
    st.pyplot(fig1)

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
        st.dataframe(st.session_state.expenses_df.style.set_properties(**{'text-align': 'left'}).set_table_styles([dict(selector='th', props=[('text-align', 'left')])]))
        
        # Visualizza il grafico a torta
        display_pie_chart()

    else:
        st.write("Nessuna spesa registrata.")
        st.write(f"**Stipendio Rimanente:** €{st.session_state.monthly_salary:.2f}")

# --- Layout dell'Applicazione Streamlit --- #
st.title("Programma di Gestione delle Spese")

# --- 1. Gestione Stipendio Mensile --- #
st.header("1. Gestione Stipendio Mensile")
st.markdown("Inserisci il tuo stipendio mensile. Una volta confermato, non potrà essere modificato per la sessione corrente (fino al reset).")

salary_input_value = st.number_input(
    'Stipendio Mensile:', 
    min_value=0.0, 
    value=st.session_state.monthly_salary if st.session_state.monthly_salary is not None else 0.0,
    disabled=st.session_state.salary_set,
    format="%.2f"
)

if st.button('Imposta Stipendio', disabled=st.session_state.salary_set):
    if salary_input_value > 0 and st.session_state.monthly_salary is None:
        st.session_state.monthly_salary = salary_input_value
        st.session_state.salary_set = True
        st.success(f"Stipendio mensile impostato a: €{st.session_state.monthly_salary:.2f}")
        st.experimental_rerun() # Ricarica per aggiornare l'interfaccia
    elif st.session_state.monthly_salary is not None:
        st.warning(f"Lo stipendio mensile è già stato impostato a: €{st.session_state.monthly_salary:.2f}. Non può essere modificato.")
    else:
        st.error("Per favore, inserisci uno stipendio valido e maggiore di zero.")

# --- 2. Gestione Spese --- #
st.header("2. Gestione Spese")
st.markdown("Qui puoi inserire, modificare o rimuovere le tue spese. La tabella sottostante verrà aggiornata automaticamente.")

col1, col2 = st.columns(2)

with col1:
    expense_name = st.text_input('Nome Spesa:', placeholder='Es. Affitto, Cibo, Trasporti')
    expense_cost = st.number_input('Costo Spesa:', min_value=0.0, value=0.0, format="%.2f")

with col2:
    st.write(" ") # Spazio per allineare i pulsanti
    st.write(" ") 
    if st.button('Aggiungi Spesa', key='add_expense_btn'):
        if expense_name and expense_cost > 0:
            new_expense = pd.DataFrame([{'Nome Spesa': expense_name, 'Costo Spesa': expense_cost}])
            st.session_state.expenses_df = pd.concat([st.session_state.expenses_df, new_expense], ignore_index=True)
            st.success(f"Spesa '{expense_name}' aggiunta.")
            st.experimental_rerun()
        else:
            st.error("Per favore, inserisci un nome e un costo valido per la spesa.")

    if st.button('Modifica Spesa', key='modify_expense_btn'):
        if expense_name and expense_cost > 0 and expense_name in st.session_state.expenses_df['Nome Spesa'].values:
            st.session_state.expenses_df.loc[st.session_state.expenses_df['Nome Spesa'] == expense_name, 'Costo Spesa'] = expense_cost
            st.success(f"Spesa '{expense_name}' modificata.")
            st.experimental_rerun()
        else:
            st.error("Per favore, inserisci un nome di spesa esistente e un costo valido da modificare.")

    if st.button('Rimuovi Spesa', key='remove_expense_btn'):
        if expense_name and expense_name in st.session_state.expenses_df['Nome Spesa'].values:
            st.session_state.expenses_df = st.session_state.expenses_df[st.session_state.expenses_df['Nome Spesa'] != expense_name].reset_index(drop=True)
            st.success(f"Spesa '{expense_name}' rimossa.")
            st.experimental_rerun()
        else:
            st.error("Per favore, inserisci un nome di spesa esistente da rimuovere.")

# --- 3. Riepilogo e Grafico a Torta --- #
st.header("3. Riepilogo e Grafico a Torta")
st.markdown("Il riepilogo delle spese e il grafico a torta verranno aggiornati automaticamente dopo ogni modifica.")
display_summary()

# --- 4. Esporta Dati in CSV --- #
st.header("4. Esporta Dati in CSV")
st.markdown("Scarica un file CSV con il riepilogo delle tue spese e le relative percentuali.")

if not st.session_state.expenses_df.empty and st.session_state.monthly_salary is not None:
    summary_data = st.session_state.expenses_df.copy()
    total_expenses = summary_data['Costo Spesa'].sum()
    remaining_salary = st.session_state.monthly_salary - total_expenses

    # Calcola le percentuali relative alle spese totali e allo stipendio rimanente
    summary_data['Percentuale_su_Totale_Spese'] = (summary_data['Costo Spesa'] / total_expenses * 100).round(2) if total_expenses > 0 else 0
    
    summary_rows = []
    summary_rows.append({'Nome Spesa': 'Totale Spese', 'Costo Spesa': total_expenses, 'Percentuale_su_Totale_Spese': None})
    summary_rows.append({'Nome Spesa': 'Stipendio Rimanente', 'Costo Spesa': remaining_salary, 'Percentuale_su_Totale_Spese': (remaining_salary / st.session_state.monthly_salary * 100).round(2) if st.session_state.monthly_salary > 0 else 0})
    summary_rows.append({'Nome Spesa': 'Stipendio Mensile', 'Costo Spesa': st.session_state.monthly_salary, 'Percentuale_su_Totale_Spese': 100.0})
    
    summary_df_extra = pd.DataFrame(summary_rows)
    final_df = pd.concat([summary_data, summary_df_extra], ignore_index=True)

    csv_string = final_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Scarica CSV Spese",
        data=csv_string,
        file_name="resoconto_spese.csv",
        mime="text/csv"
    )
else:
    st.write("Nessuna spesa o stipendio non impostato per l'esportazione.")

# --- 5. Reset Mese --- #
st.header("5. Reset Mese")
st.markdown("Questo pulsante ti permette di azzerare tutte le spese e lo stipendio mensile per ricominciare da capo.")

if st.button('Reset Mese', type='secondary'):
    st.session_state.reset_pending = True

if st.session_state.reset_pending:
    st.warning("Sei sicuro di voler procedere?")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button('Sì, Azzera Tutto', type='primary'):
            st.session_state.monthly_salary = None
            st.session_state.expenses_df = pd.DataFrame(columns=['Nome Spesa', 'Costo Spesa'])
            st.session_state.salary_set = False
            st.session_state.reset_pending = False
            st.success("Mese azzerato! Inserisci il nuovo stipendio e le spese.")
            st.experimental_rerun()
    with col_cancel:
        if st.button('No, Annulla'):
            st.session_state.reset_pending = False
            st.info("Operazione di reset annullata.")
            st.experimental_rerun()
