# PISI3

Aplicação Dash para análise de registros epidemiológicos de Chikungunya, Dengue e Zika.

## Instalação

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Executar a aplicação

Com o ambiente virtual ativado:

```bash
python main.py
```

A aplicação Dash será disponibilizada em `http://127.0.0.1:8050/`.

## Dicionário de dados

Os arquivos CSV originais estão em `data/`. A documentação gerada está em `docs/`:

- `docs/chikungunya.md`: esquema dos arquivos de Chikungunya;
- `docs/dengue.md`: esquema dos arquivos de Dengue;
- `docs/zika.md`: esquema dos arquivos de Zika;
- `docs/diferencas_estrutura.md`: comparação estrutural dos 12 CSVs;
- `docs/inconsistencias_dados.md`: inconsistências e recomendações de qualidade;
- `docs/dicionario_dados.docx`: versão Word para compartilhamento.

Os arquivos de referência semântica usados no mapeamento estão em `data/dict/`.

## Regenerar artefatos

Execute os comandos a partir da raiz do projeto:

```bash
python scripts/gerar_dicionario.py
python scripts/referencias_dicionario.py
python scripts/gerar_word.py
```

Os dois primeiros comandos geram arquivos intermediários em `build/`. O último comando recompõe `docs/dicionario_dados.docx` a partir dos documentos Markdown de `docs/`.

## Observações

- Os CSVs são lidos com separador `;` e encoding UTF-8 com BOM.
- Códigos e identificadores devem ser tratados como texto para preservar zeros à esquerda.
- Os documentos descrevem os arquivos originais e não substituem uma etapa autorizada de limpeza ou normalização dos dados.
