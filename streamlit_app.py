import streamlit as st
import boto3
import pandas as pd
from io import BytesIO
import os

# Configurações AWS via Streamlit Secrets
AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY"]
AWS_SECRET_KEY = st.secrets["AWS_SECRET_KEY"]
AWS_BUCKET_NAME = st.secrets["AWS_BUCKET_NAME"]
AWS_REGION = "us-east-1"

# Inicializa cliente S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Nome do arquivo no S3
S3_FILE_KEY = "controle/controle_diarias_servicos.xlsx"

# Função para carregar arquivo do S3
def carregar_arquivo():
    try:
        buffer = BytesIO()
        s3.download_fileobj(AWS_BUCKET_NAME, S3_FILE_KEY, buffer)
        buffer.seek(0)
        with pd.ExcelFile(buffer) as xls:
            df_funcionarios = pd.read_excel(xls, sheet_name="Diárias Funcionários")
        return df_funcionarios
    except Exception:
        return pd.DataFrame(columns=["Nome", "Dia", "Combustível (R$)", "Valor do Dia (R$)", "Descrição"])

# Função para salvar arquivo no S3
def salvar_no_s3(df_funcionarios):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_funcionarios.to_excel(writer, sheet_name="Diárias Funcionários", index=False)
    buffer.seek(0)
    s3.upload_fileobj(buffer, AWS_BUCKET_NAME, S3_FILE_KEY)

# Carregar dados existentes
df_funcionarios = carregar_arquivo()

# Layout Streamlit
st.title("📋 Controle de Diárias e Serviços")

aba = st.sidebar.radio("Escolha a seção", ["Diárias Funcionários"])

if aba == "Diárias Funcionários":
    st.header("Adicionar Diária")
    with st.form("form_funcionario"):
        nomes_opcoes = ["Selecione", "Batista", "Sonia"]
        nome = st.selectbox("Nome", nomes_opcoes)
        dia = st.date_input("Dia")
        combustivel = st.number_input("Combustível (R$)", min_value=0.0, step=10.0)
        valor_dia = st.number_input("Valor do Dia (R$)", min_value=0.0, step=10.0)
        observacao = st.text_area("Descrição")
        submitted = st.form_submit_button("Salvar")

        if submitted:
            novo = {"Nome": nome, "Dia": dia, "Combustível (R$)": combustivel, "Valor do Dia (R$)": valor_dia, "Descrição": observacao}
            df_funcionarios = pd.concat([df_funcionarios, pd.DataFrame([novo])], ignore_index=True)
            salvar_no_s3(df_funcionarios)
            st.success("✅ Diária salva!")

    st.subheader("Registros Atuais")

    if "Dia" in df_funcionarios.columns:
        df_funcionarios["Dia"] = pd.to_datetime(df_funcionarios["Dia"]).dt.strftime("%d/%m/%Y")

    st.dataframe(df_funcionarios)

# Botão para download direto
if st.button("⬇️ Baixar Planilha"):
    buffer = BytesIO()
    s3.download_fileobj(AWS_BUCKET_NAME, S3_FILE_KEY, buffer)
    buffer.seek(0)
    st.download_button(
        label="Clique para baixar",
        data=buffer,
        file_name="controle_diarias_servicos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
