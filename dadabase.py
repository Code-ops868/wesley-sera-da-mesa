import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO
# ==========================================
st.set_page_config(page_title="Igreja Emmanuel Evangelica Wesleyana Serra da Mesa", layout="wide")
DB_NAME = "igreja.db"

# ==========================================
# INICIALIZAÇÃO DO BANCO
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS membros (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, estado_civil TEXT, idade INTEGER,
        faixa_etaria TEXT, residencia TEXT, batizado TEXT, anos_igreja INTEGER, data_cadastro TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ajuda_pastoral (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, descricao TEXT, data_pedido TEXT, status TEXT DEFAULT 'Pendente')''')
    c.execute('''CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, categoria TEXT, valor REAL, data TEXT, observacao TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# SENHAS
# ==========================================
SENHA_PASTOR = "sermerev9"
SENHA_FINANCEIRO = "finserme"

# ==========================================
# FUNÇÕES DO BANCO
# ==========================================
def salvar_membro(dados):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO membros (nome, estado_civil, idade, faixa_etaria, residencia, batizado, anos_igreja, data_cadastro)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', dados)
    conn.commit()
    conn.close()

def salvar_ajuda(nome, descricao):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute('''INSERT INTO ajuda_pastoral (nome, descricao, data_pedido, status)
                 VALUES (?, ?, ?, 'Pendente')''', (nome, descricao, data))
    conn.commit()
    conn.close()

def atualizar_status_ajuda(ajuda_id, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE ajuda_pastoral SET status = ? WHERE id = ?", (status, ajuda_id))
    conn.commit()
    conn.close()

def salvar_movimentacao(tipo, categoria, valor, data, observacao):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO financeiro (tipo, categoria, valor, data, observacao)
                 VALUES (?, ?, ?, ?, ?)''', (tipo, categoria, valor, data, observacao))
    conn.commit()
    conn.close()

def carregar_membros():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM membros ORDER BY data_cadastro DESC", conn)
    conn.close()
    return df

def carregar_ajudas():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM ajuda_pastoral ORDER BY data_pedido DESC", conn)
    conn.close()
    return df

def carregar_financeiro():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM financeiro ORDER BY data DESC", conn)
    conn.close()
    return df

# FUNÇÕES DE DELEÇÃO
def deletar_membro(id_membro):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM membros WHERE id = ?", (id_membro,))
    conn.commit()
    conn.close()

def deletar_ajuda(id_ajuda):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM ajuda_pastoral WHERE id = ?", (id_ajuda,))
    conn.commit()
    conn.close()

def deletar_movimentacao(id_mov):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM financeiro WHERE id = ?", (id_mov,))
    conn.commit()
    conn.close()

def limpar_tabela(tabela):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"DELETE FROM {tabela}")
    conn.commit()
    conn.close()

# ==========================================
# FUNÇÃO AUXILIAR
# ==========================================
def definir_faixa_etaria(idade):
    if idade < 13: return "Crianças"
    elif idade < 18: return "Jovens"
    elif idade < 60: return "Pais/Mães"
    else: return "Idosos"

# ==========================================
# MENU LATERAL
# ==========================================
st.sidebar.title("Menu")
opcao = st.sidebar.radio("Ir para", ["Cadastro de Membro", "Ajuda Pastoral", "Relatórios", "Financeiro", "Admin (Limpar)"])

# ==========================================
# 1. CADASTRO DE MEMBRO
# ==========================================
if opcao == "Cadastro de Membro":
    st.title('Igreja E. E. WESLEYANA DE NAMPULA - SERRA DA MESA')
    st.header("Cadastro de Membro")
    with st.form("form_cadastro"):
        nome = st.text_input("Nome *")
        estado_civil = st.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Viúvo(a)", "Divorciado(a)"])
        idade = st.number_input("Idade *", min_value=0, max_value=120)
        residencia = st.text_input("Residência *")
        batizado = st.selectbox("Batizado?", ["Sim", "Não"])
        anos_igreja = st.number_input("Anos na igreja", min_value=0)
        if st.form_submit_button("Cadastrar"):
            if nome and residencia:
                faixa = definir_faixa_etaria(idade)
                data = datetime.now().strftime("%d/%m/%Y %H:%M")
                salvar_membro((nome, estado_civil, idade, faixa, residencia, batizado, anos_igreja, data))
                st.success(f"{nome} cadastrado!")
                st.balloons()
            else:
                st.error("Preencha os campos obrigatórios")

    # === DELETAR MEMBRO ===
    st.markdown("---")
    st.subheader("Remover Membro")
    membros = carregar_membros()
    if not membros.empty:
        membro_selecionado = st.selectbox("Selecione o membro para excluir", options=membros['nome'], key="del_membro")
        if st.button("Excluir Membro", type="secondary"):
            id_del = membros[membros['nome'] == membro_selecionado].iloc[0]['id']
            deletar_membro(id_del)
            st.success(f"{membro_selecionado} removido!")
            st.rerun()
    else:
        st.info("Nenhum membro cadastrado.")

# ==========================================
# 2. AJUDA PASTORAL
# ==========================================
elif opcao == "Ajuda Pastoral":
    st.header("Ajuda Pastoral")
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    tab1, tab2 = st.tabs(["Enviar Pedido", "Histórico (Pastor)"])

    with tab1:
        with st.form("form_ajuda"):
            nome_ajuda = st.text_input("Seu nome *")
            descricao = st.text_area("Descreva sua necessidade *", height=120)
            if st.form_submit_button("Enviar"):
                if nome_ajuda and descricao:
                    salvar_ajuda(nome_ajuda, descricao)
                    st.success("Pedido enviado!")
                    st.balloons()
                else:
                    st.error("Preencha todos os campos")

    with tab2:
        if not st.session_state.autenticado:
            st.warning("Acesso restrito ao pastor")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                if senha == SENHA_PASTOR:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Senha incorreta")
        else:
            if st.button("Sair"):
                st.session_state.autenticado = False
                st.rerun()

            ajudas = carregar_ajudas()
            if not ajudas.empty:
                for _, row in ajudas.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([2, 4, 2, 1.5, 1.5])
                    with c1: st.write(f"**{row['nome']}**")
                    with c2: st.caption(row['descricao'])
                    with c3: st.caption(f"_{row['data_pedido']}_")
                    with c4:
                        if row['status'] == "Pendente":
                            if st.button("Atendido", key=f"at_{row['id']}"):
                                atualizar_status_ajuda(row['id'], "Atendido")
                                st.rerun()
                        else:
                            st.success("Atendido")
                    with c5:
                        if st.button("Excluir", key=f"del_ajuda_{row['id']}", type="secondary"):
                            deletar_ajuda(row['id'])
                            st.success("Pedido excluído!")
                            st.rerun()
                st.markdown("---")
                st.dataframe(ajudas[['nome', 'descricao', 'data_pedido', 'status']], use_container_width=True)
            else:
                st.info("Nenhum pedido.")

# ==========================================
# 3. RELATÓRIOS
# ==========================================
elif opcao == "Relatórios":
    st.header("Relatórios")
    membros = carregar_membros()
    if membros.empty:
        st.info("Nenhum membro.")
    else:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.subheader("Membros")
            st.dataframe(membros.drop(columns=['id']), use_container_width=True)
        with col2:
            st.subheader("Faixa Etária")
            cont = membros['faixa_etaria'].value_counts().reset_index()
            cont.columns = ['Faixa', 'Total']
            fig = px.pie(cont, values='Total', names='Faixa', hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. FINANCEIRO
# ==========================================
elif opcao == "Financeiro":
    st.header("Controle Financeiro")
    if 'acesso_financeiro' not in st.session_state:
        st.session_state.acesso_financeiro = False

    if not st.session_state.acesso_financeiro:
        st.warning("Acesso restrito")
        senha = st.text_input("Senha financeira", type="password")
        if st.button("Acessar"):
            if senha == SENHA_FINANCEIRO:
                st.session_state.acesso_financeiro = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    else:
        if st.button("Sair"):
            st.session_state.acesso_financeiro = False
            st.rerun()

        tab1, tab2 = st.tabs(["Lançar", "Relatórios"])

        with tab1:
            with st.form("form_financeiro"):
                tipo = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True)
                if tipo == "Entrada":
                    categoria = st.selectbox("Categoria", ["Dízimo", "Oferta", "Doação"])
                else:
                    categoria = st.text_input("Descrição da Saída")
                valor = st.number_input("Valor (MZN)", min_value=0.01, format="%.2f")
                data = st.date_input("Data", value=datetime.today())
                obs = st.text_area("Observação", height=80)
                if st.form_submit_button("Lançar"):
                    data_str = data.strftime("%d/%m/%Y")
                    salvar_movimentacao(tipo, categoria, valor, data_str, obs)
                    st.success("Lançamento realizado!")
                    st.balloons()

        with tab2:
            df = carregar_financeiro()
            if df.empty:
                st.info("Nenhuma movimentação.")
            else:
                df['data_dt'] = pd.to_datetime(df['data'], format="%d/%m/%Y", errors='coerce')
                df['mês'] = df['data_dt'].dt.strftime('%Y-%m')

                entradas = df[df['tipo'] == 'Entrada']['valor'].sum()
                saidas = df[df['tipo'] == 'Saída']['valor'].sum()
                saldo = entradas - saidas
                c1, c2, c3 = st.columns(3)
                c1.metric("Entradas", f"MZN {entradas:,.2f}")
                c2.metric("Saídas", f"MZN {saidas:,.2f}")
                c3.metric("Saldo", f"MZN {saldo:,.2f}")

                st.subheader("Movimentações")
                disp = df.copy()
                disp['valor'] = disp['valor'].apply(lambda x: f"MZN {x:,.2f}")
                st.dataframe(disp[['tipo', 'categoria', 'valor', 'data', 'observacao']], use_container_width=True)

                # === DELETAR MOVIMENTAÇÃO ===
                st.markdown("---")
                st.subheader("Remover Movimentação")
                mov_selecionada = st.selectbox("Selecione para excluir", options=disp.apply(lambda x: f"{x['data']} - {x['tipo']} - {x['categoria']} - MZN {x['valor']}", axis=1))
                if st.button("Excluir Movimentação", type="secondary"):
                    idx = disp[disp.apply(lambda x: f"{x['data']} - {x['tipo']} - {x['categoria']} - MZN {x['valor']}", axis=1) == mov_selecionada].index[0]
                    id_del = df.iloc[idx]['id']
                    deletar_movimentacao(id_del)
                    st.success("Movimentação removida!")
                    st.rerun()

                # === GRÁFICO DE BARRAS (CORRIGIDO) ===
                st.subheader("Entradas × Saídas por Mês")
                mensal = df.groupby(['mês', 'tipo'])['valor'].sum().unstack(fill_value=0)
                for col in ['Entrada', 'Saída']:
                    if col not in mensal.columns:
                        mensal[col] = 0
                mensal = mensal.reset_index()
                if len(mensal) > 0:
                    fig_bar = px.bar(mensal, x='mês', y=['Entrada', 'Saída'], barmode='group',
                                     color_discrete_map={'Entrada': '#2E8B57', 'Saída': '#DC143C'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Sem dados mensais.")

                # === GRÁFICO DE PIZZA ===
                st.subheader("Distribuição das Entradas")
                entradas_cat = df[df['tipo'] == 'Entrada'].groupby('categoria')['valor'].sum()
                if not entradas_cat.empty:
                    fig_pie = px.pie(values=entradas_cat.values, names=entradas_cat.index, hole=0.4)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Nenhuma entrada.")

# ==========================================
# 5. ADMIN - LIMPAR HISTÓRICO
# ==========================================
else:  # Admin
    st.header("Admin - Limpeza de Dados")
    st.warning("**CUIDADO**: Esta seção permite apagar dados permanentemente.")

    senha_admin = st.text_input("Senha de Administrador", type="password")
    if senha_admin == "adminrev9":  # Mude para st.secrets em produção
        st.success("Acesso admin liberado")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Limpar Membros", type="secondary"):
                if st.checkbox("Confirmo que desejo apagar todos os membros"):
                    limpar_tabela("membros")
                    st.success("Todos os membros foram apagados!")
                    st.rerun()
        with col2:
            if st.button("Limpar Pedidos", type="secondary"):
                if st.checkbox("Confirmo que desejo apagar todos os pedidos"):
                    limpar_tabela("ajuda_pastoral")
                    st.success("Todos os pedidos foram apagados!")
                    st.rerun()
        with col3:
            if st.button("Limpar Financeiro", type="secondary"):
                if st.checkbox("Confirmo que desejo apagar todo o financeiro"):
                    limpar_tabela("financeiro")
                    st.success("Todo o financeiro foi apagado!")
                    st.rerun()

        st.markdown("---")
        st.info("Use com responsabilidade. Não há recuperação de dados.")
    else:
        st.info("Digite a senha de administrador para acessar.")