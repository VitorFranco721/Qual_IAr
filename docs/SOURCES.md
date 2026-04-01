# Fontes de dados e plano de extração

Este documento lista as fontes oficiais utilizadas no projeto
**Brasília Air Quality**. Para cada fonte, mostramos agência responsável,
acesso, formato, cobertura e limitações.

| ID | Órgão | URL | Formato | Cobertura | Observações |
|---|---|---|---|---|---|
| `arcgis_stations` | **IBRAM** (Instituto Brasília Ambiental) | `https://onda.ibram.df.gov.br/server/rest/services/Hosted/Estações_de_monitoramento_da_qualidade_do_ar_estabelecidas_por_licenciamento_ambiental/FeatureServer/0` | ArcGIS FeatureLayer | 9 estações no DF | Camada com nomes codificados das estações (ex.: `cras_fercal`, `rodoviaria`, `zoo`) e indicadores de poluentes monitorados. Pode exigir autenticação para algumas consultas diretas da API REST. |
| `monitorar` | **Ministério do Meio Ambiente e Mudança do Clima (MMA)** | `https://monitorar.mma.gov.br` | Aplicação web / API | Dados em tempo real de estações automáticas na Fercal | A API não é oficialmente documentada. O projeto prevê fallback quando a coleta automática não for possível. |
| `manual_reports` | **IBRAM / empresas licenciadas** | Relatórios PDF anuais | PDF | Estações manuais no DF e Fercal | Sem API pública para consulta estruturada. Pode exigir extração manual de tabelas. |

## Uso responsável e ética

* **Respeito a limites de acesso:** os conectores devem evitar excesso de
  requisições e seguir boas práticas de coleta.
* **Licenciamento:** sempre que a licença estiver disponível, ela deve ser
  preservada no campo `license`.
* **Restrições de termos de uso:** se a fonte proibir automação, o projeto deve
  registrar essa limitação e usar estratégia alternativa.