O serviço `backend/app/services/receita_digital.py` já existe com implementação completa. Corrigi um import faltante em `telemedicina_ws.py` (adicionei `router = APIRouter()`) que impedia a execução dos testes via conftest.

**Resumo da implementação:**

| Função | Localização | Descrição |
|--------|-------------|-----------|
| `gerar_hash_prescricao()` | `receita_digital.py:81` | Hash SHA-256 canônico (JSON ordenado, NFC, UTC) |
| `AssinadorReceitaDigital.assinar()` | `receita_digital.py:113` | Assinatura HMAC-SHA256 + metadados |
| `AssinadorReceitaDigital.verificar()` | `receita_digital.py:132` | Verifica integridade; detecta adulteração de dosagem/medicamento |
| `validar_documento_emitido()` | `receita_digital.py:163` | Validador de alto nível com chave via env/param |

**Testes:** 44/44 passando. Detecção de adulteração cobre: dosagem, nome, frequência, quantidade, CNS, CPF, CID-10, CIAP-2, observações, troca de medicamento, hash recalculado e chave incorreta.