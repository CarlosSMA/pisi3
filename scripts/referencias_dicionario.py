from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

REFERENCE_FILES = {
    "chikungunya": "dict_chikungunya.json",
    "dengue": "dict_dengue.json",
    "zika": "dict_zika.json",
}

CSV_ALIASES = {
    "num_notificacao": "NU_NOTIFIC",
    "tipo_notificacao": "TP_NOT",
    "co_cid": "ID_AGRAVO",
    "dt_notificacao": "DT_NOTIFIC",
    "ds_semana_notificacao": "SEM_NOT",
    "notificacao_ano": "NU_ANO",
    "co_uf_notificacao": "SG_UF_NOT",
    "co_municipio_notificacao": "ID_MUNICIP",
    "id_regional": "ID_REGIONA",
    "co_unidade_notificacao": "ID_UNIDADE",
    "dt_diagnostico_sintoma": "DT_SIN_PRI",
    "ds_semana_sintoma": "SEM_PRI",
    "dt_nascimento": "DT_NASC",
    "nu_idade": "NU_IDADE_N",
    "tp_sexo": "CS_SEXO",
    "tp_gestante": "CS_GESTANT",
    "tp_raca_cor": "CS_RACA",
    "tp_escolaridade": "CS_ESCOL_N",
    "co_uf_residencia": "SG_UF",
    "co_municipio_residencia": "ID_MN_RESI",
    "co_regional_residencia": "ID_RG_RESI",
    "co_distrito_residencia": "ID_DISTRIT",
    "co_bairro_residencia": "ID_BAIRRO",
    "no_bairro_residencia": "NM_BAIRRO",
    "co_logradouro_residencia": "ID_LOGRADO",
    "nome_logradouro_residencia": "NM_LOGRADO",
    "nu_cep_residencia": "NU_CEP",
    "tp_zona_residencia": "CS_ZONA",
    "co_pais_residencia": "ID_PAIS",
    "dt_investigacao": "DT_INVEST",
    "co_cbo_ocupacao": "ID_OCUPA_N",
}


@dataclass(frozen=True)
class ReferenceField:
    disease: str
    source_file: str
    source_code: str
    description: str
    source_type: str
    size: int | None
    allowed_values: str


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]", "", without_accents.lower())


def load_reference_fields(dict_dir: Path) -> list[ReferenceField]:
    fields: list[ReferenceField] = []
    for disease, filename in REFERENCE_FILES.items():
        source_file = dict_dir / filename
        payload: dict[str, Any] = json.loads(
            source_file.read_text(encoding="utf-8"))
        for field in payload["metadados"]["campos"]:
            fields.append(
                ReferenceField(
                    disease=disease,
                    source_file=filename,
                    source_code=str(field.get("codigo", "")),
                    description=str(field.get("descricao", "")),
                    source_type=str(field.get("tipo", "")),
                    size=field.get("tamanho"),
                    allowed_values=str(field.get("valores_permitidos", "")),
                )
            )
    return fields


def resolve_csv_name(source_code: str) -> str | None:
    normalized_code = normalize_name(source_code)
    for reference_code, csv_name in CSV_ALIASES.items():
        if normalize_name(reference_code) == normalized_code:
            return csv_name
    return None


def build_reference_mapping(
    fields: Iterable[ReferenceField],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    by_disease_and_csv: dict[tuple[str, str], list[ReferenceField]] = {}

    for field in fields:
        csv_name = resolve_csv_name(field.source_code)
        key = (field.disease, csv_name or "")
        by_disease_and_csv.setdefault(key, []).append(field)
        entry = asdict(field)
        entry["csv_name"] = csv_name
        entry["mapping_status"] = "mapeado" if csv_name else "sem_correspondencia"
        entries.append(entry)

    conflicts = [
        {
            "disease": disease,
            "csv_name": csv_name,
            "source_codes": [field.source_code for field in matching_fields],
        }
        for (disease, csv_name), matching_fields in sorted(
            by_disease_and_csv.items()
        )
        if csv_name and len(matching_fields) > 1
    ]
    return {
        "aliases_csv": CSV_ALIASES,
        "referencias": entries,
        "conflitos": conflicts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepara referências semânticas dos dicionários JSON."
    )
    parser.add_argument(
        "--dict-dir",
        type=Path,
        default=Path("data") / "dict",
        help="Pasta com os dicionários JSON de referência.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build") / "referencias_dicionario.json",
        help="Arquivo JSON de saída das referências.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fields = load_reference_fields(args.dict_dir)
    mapping = build_reference_mapping(fields)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Referências processadas: {len(mapping['referencias'])}")
    print(f"Conflitos identificados: {len(mapping['conflitos'])}")
    print(f"Mapeamento gerado em: {args.output}")


if __name__ == "__main__":
    main()
