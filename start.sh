#!/usr/bin/env bash
set -e

# Ativar ambiente virtual
source /home/jpversiani/Projeto_dados_tabnet_Sus/.venv/bin/activate

# Diretório base
cd /home/jpversiani/Projeto_dados_tabnet_Sus/backend

echo "========================================================"
echo " Iniciando e-SUS APS Open Source (PEC)"
echo " Acesse a interface web em:  http://localhost:8000"
echo " Documentação da API:        http://localhost:8000/docs"
echo "========================================================"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
