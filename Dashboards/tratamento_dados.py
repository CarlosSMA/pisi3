import argparse
import unicodedata
from pathlib import Path

import pandas as pd

SYMPTOMS = {
    "FEBRE": "Febre", "MIALGIA": "Mialgia", "CEFALEIA": "Cefaleia", "EXANTEMA": "Exantema",
    "VOMITO": "Vômito", "NAUSEA": "Náusea", "DOR_COSTAS": "Dor nas costas", "CONJUNTVIT": "Conjuntivite",
    "ARTRITE": "Artrite", "ARTRALGIA": "Artralgia", "PETEQUIA_N": "Petéquias", "LEUCOPENIA": "Leucopenia",
    "LACO": "Prova do laço", "DOR_RETRO": "Dor retro-orbital",
}
EXAMS = {
    "RESUL_NS1": "NS1", "RESUL_PCR_": "RT-PCR", "RESUL_SORO": "Sorologia IgM (dengue)",
    "RESUL_VI_N": "Isolamento viral", "RES_CHIKS1": "Sorologia IgM chik. (S1)",
    "RES_CHIKS2": "Sorologia IgM chik. (S2)", "RESUL_PRNT": "PRNT",
}
RESULT_LABELS = {"1": "Reagente / positivo", "2": "Não reagente / negativo", "3": "Inconclusivo", "4": "Não realizado"}
CRITERIA_LABELS = {"1": "Laboratorial", "2": "Clínico-epidemiológico", "3": "Em investigação"}
SEROTYPE_LABELS = {"1": "DENV-1", "2": "DENV-2", "3": "DENV-3", "4": "DENV-4"}
# Classificações específicas de cada ficha do SINAN.
CLASSIFICATION_LABELS = {
    "Dengue": {"5": "Descartado", "8": "Inconclusivo", "10": "Dengue", "11": "Dengue com sinais de alarme",
               "12": "Dengue grave", "13": "Chikungunya"},
    "Chikungunya": {"5": "Descartado", "8": "Inconclusivo", "10": "Dengue", "11": "Dengue com sinais de alarme",
                    "12": "Dengue grave", "13": "Chikungunya"},
    "Zika": {"1": "Zika confirmado", "2": "Descartado", "8": "Inconclusivo"},
}
STATUS_BY_LABEL = {"Descartado": "Descartado", "Inconclusivo": "Inconclusivo"}
INTERVALS = {
    "dias_sintoma_notificacao": "Sintomas → notificação",
    "dias_notificacao_investigacao": "Notificação → investigação",
    "dias_notificacao_encerramento": "Notificação → encerramento",
    "dias_sintoma_encerramento": "Sintomas → encerramento",
}
VALORES_NAO_INFORMADOS = {'Não informado', 'Não Informado', 'Não informada', 'Não Informada', 'Nan', ''}



def codigo(series):
    return series.astype('string').str.strip().str.replace(r'\.0+$', '', regex=True).replace('', pd.NA)


def coluna(frame, name):
    return frame[name] if name in frame else pd.Series(pd.NA, index=frame.index, dtype='string')


def substituir_nao_informado_pela_moda(frame, columns):
    result = frame.copy()
    for column in columns:
        if column not in result:
            continue
        values = result[column]
        known = values.notna() & ~values.astype('string').isin(VALORES_NAO_INFORMADOS)
        if known.any():
            mode = values[known].mode()
            if not mode.empty:
                result.loc[~known, column] = mode.iat[0]
    return result


def converter_datas(series):
    text = series.astype('string').str.strip()
    iso = text.str.match(r'^\d{4}-\d{2}-\d{2}', na=False)
    serial = pd.to_numeric(text, errors='coerce').where(text.str.fullmatch(r'\d{5}(\.0+)?', na=False))
    return (pd.to_datetime(text.where(iso), format='ISO8601', errors='coerce')
            .fillna(pd.to_datetime(text.where(~iso), format='%d/%m/%Y', errors='coerce'))
            .fillna(pd.to_datetime(serial, unit='D', origin='1899-12-30', errors='coerce')))


def semana_epidemiologica(datas):
    inicio = datas - pd.to_timedelta(((datas.dt.dayofweek + 1) % 7).fillna(0), unit='D')
    ano = (inicio + pd.Timedelta(days=3)).dt.year.astype('Int64')
    janeiro = pd.to_datetime(ano.astype('string') + '-01-04', errors='coerce')
    primeira = janeiro - pd.to_timedelta(((janeiro.dt.dayofweek + 1) % 7).fillna(0), unit='D')
    semana = ((inicio - primeira).dt.days // 7 + 1).astype('Int64')
    return ano, semana, inicio


def normalizar_nome(value):
    if pd.isna(value):
        return pd.NA
    text = ''.join(c for c in unicodedata.normalize('NFKD', str(value)) if not unicodedata.combining(c))
    return ' '.join(text.upper().split()) or pd.NA


def normalizar_bairro(value):
    aliases = {'POCO': 'POCO DA PANELA', 'BAIRRO DO RECIFE': 'RECIFE', 'SAN MARTIM': 'SAN MARTIN',
           'PAU-FERRO': 'PAU FERRO', 'FUNDÆO': 'FUNDAO', 'HIPADROMO': 'HIPODROMO',
           'CAMPO GRANE': 'CAMPO GRANDE', 'CORREGO JENIPAPO': 'CORREGO DO JENIPAPO',
           "ALTO JOS' DO PINHO": 'ALTO JOSE DO PINHO', 'ALTO JOS\x90 DO PINHO': 'ALTO JOSE DO PINHO'}
    name = normalizar_nome(value)
    return aliases.get(name, name) if pd.notna(name) else pd.NA


def resposta(frame, field):
    raw = codigo(coluna(frame, field))
    status = raw.map({'1': 'Sim', '2': 'Não', '9': 'Ignorado'}).fillna('Não informado')
    if field not in frame:
        status[:] = 'Não disponível'
    return raw.map({'1': True, '2': False}).astype('boolean'), status


# Nomes de referência: https://recifeemdia.recife.pe.gov.br/regionaisSecon
BAIRROS_RECIFE = set("""AFLITOS;AFOGADOS;AGUA FRIA;ALTO DO MANDU;ALTO JOSE BONIFACIO;ALTO JOSE DO PINHO;ALTO SANTA TEREZINHA;APIPUCOS
AREIAS;ARRUDA;BARRO;BEBERIBE;BOA VIAGEM;BOA VISTA;BOMBA DO HEMETERIO;BONGI;BRASILIA TEIMOSA;BREJO DA GUABIRABA
BREJO DE BEBERIBE;CABANGA;CACOTE;CAJUEIRO;CAMPINA DO BARRETO;CAMPO GRANDE;CASA AMARELA;CASA FORTE;CAXANGA
CIDADE UNIVERSITARIA;COELHOS;COHAB;COQUEIRAL;CORDEIRO;CORREGO DO JENIPAPO;CURADO;DERBY;DOIS IRMAOS;DOIS UNIDOS
ENCRUZILHADA;ENGENHO DO MEIO;ESPINHEIRO;ESTANCIA;FUNDAO;GRACAS;GUABIRABA;HIPODROMO;IBURA;ILHA DO LEITE
ILHA DO RETIRO;ILHA JOANA BEZERRA;IMBIRIBEIRA;IPSEP;IPUTINGA;JAQUEIRA;JARDIM SAO PAULO;JIQUIA;JORDAO;LINHA DO TIRO
MACAXEIRA;MADALENA;MANGABEIRA;MANGUEIRA;MONTEIRO;MORRO DA CONCEICAO;MUSTARDINHA;NOVA DESCOBERTA;PAISSANDU
PARNAMIRIM;PASSARINHO;PAU FERRO;PEIXINHOS;PINA;POCO DA PANELA;PONTO DE PARADA;PORTO DA MADEIRA;PRADO;RECIFE
ROSARINHO;SAN MARTIN;SANCHO;SANTANA;SANTO AMARO;SANTO ANTONIO;SAO JOSE;SITIO DOS PINTOS;SOLEDADE;TAMARINEIRA
TEJIPIO;TORRE;TORREAO;TORROES;TOTO;VARZEA;VASCO DA GAMA;ZUMBI""".replace("\n", ";").split(";"))


def carregar_dados_tratados(pasta=None, incluir_incompletos=False, limite_sintomas=365):
    pasta = Path(pasta) if pasta else Path(__file__).resolve().parent.parent / 'data'
    frames = []
    for path in sorted(pasta.glob('*.csv')):
        disease = next((v for k, v in [('dengue', 'Dengue'), ('chik', 'Chikungunya'), ('zika', 'Zika')]
                        if k in path.name.lower()), None)
        if disease is None:
            continue
        raw = pd.read_csv(path, sep=';', dtype='string', on_bad_lines='error')
        raw.columns = raw.columns.str.strip().str.upper()
        out = raw.copy()
        out['arquivo_origem'] = path.name
        out['registro_origem'] = range(1, len(raw) + 1)
        out['doenca'] = disease
        out['registro_incompleto'] = raw.notna().sum(axis=1).le(1)
        dates = {'dt_notificacao': 'DT_NOTIFIC', 'dt_sintomas': 'DT_SIN_PRI',
                 'dt_investigacao': 'DT_INVEST', 'dt_encerramento': 'DT_ENCERRA', 'dt_nascimento': 'DT_NASC'}
        for target, field in dates.items():
            out[target] = converter_datas(coluna(raw, field))
            out[target + '_invalida'] = coluna(raw, field).notna() & out[target].isna()
        onset, notified = out.dt_sintomas, out.dt_notificacao
        atraso = (notified - onset).dt.days
        # O limite serve para revisão, sem alterar a data original.
        out['sintomas_suspeitos'] = (atraso.lt(0) | atraso.gt(limite_sintomas) | onset.lt(out.dt_nascimento)).fillna(False)
        out['dt_sintomas_analise'] = onset.mask(out.sintomas_suspeitos)
        out['ano'] = notified.dt.year.astype('Int64')
        ano_original = pd.to_numeric(codigo(coluna(raw, 'NU_ANO')), errors='coerce')
        out['ano_divergente'] = (ano_original.notna() & notified.notna() & ano_original.ne(out.ano)).fillna(False)
        for suffix, field, date_field in [('notificacao', 'SEM_NOT', 'dt_notificacao'),
                                          ('sintomas', 'SEM_PRI', 'dt_sintomas_analise')]:
            year, week, start = semana_epidemiologica(out[date_field])
            original = codigo(coluna(raw, field))
            expected = year * 100 + week
            numeric = pd.to_numeric(original, errors='coerce')
            out['semana_' + suffix + '_divergente'] = (numeric.notna() & expected.notna() & numeric.ne(expected)).fillna(False)
            out['ano_epi_' + suffix] = year
            out['semana_' + suffix] = week
            out['inicio_semana_' + suffix] = start
        out['semana'] = out.semana_notificacao
        out['semana_epidemiologica'] = out.semana_sintomas
        intervals = {'dias_sintoma_notificacao': ('dt_sintomas_analise', 'dt_notificacao'),
                     'dias_notificacao_investigacao': ('dt_notificacao', 'dt_investigacao'),
                     'dias_notificacao_encerramento': ('dt_notificacao', 'dt_encerramento'),
                     'dias_sintoma_encerramento': ('dt_sintomas_analise', 'dt_encerramento')}
        for target, (begin, end) in intervals.items():
            days = (out[end] - out[begin]).dt.days
            out[target + '_negativo'] = days.lt(0)
            out[target] = days.where(days.ge(0))
            out[target + '_acima_120'] = days.gt(120)
        out['tempo_encerramento'] = out.dias_notificacao_encerramento
        classification = codigo(coluna(raw, 'CLASSI_FIN'))
        labels = classification.map(CLASSIFICATION_LABELS[disease])
        out['classificacao'] = labels.fillna('Não informado')
        confirmed_codes = {'Dengue': ['10', '11', '12'], 'Chikungunya': ['13'], 'Zika': ['1']}
        out['confirmado'] = classification.isin(confirmed_codes[disease])
        out['situacao'] = labels.map(STATUS_BY_LABEL).fillna('Em investigação / sem classificação')
        out.loc[out.confirmado, 'situacao'] = 'Confirmado'
        other = classification.isin(['10', '11', '12', '13']) & ~out.confirmado & (disease != 'Zika')
        out.loc[other, 'situacao'] = 'Outro agravo confirmado'
        out['classificacao_desconhecida'] = classification.notna() & labels.isna()
        out['criterio'] = codigo(coluna(raw, 'CRITERIO')).map(CRITERIA_LABELS).fillna('Não informado')
        out['sorotipo'] = codigo(coluna(raw, 'SOROTIPO')).map(SEROTYPE_LABELS)
        for target, field in [('municipio', 'ID_MN_RESI'), ('mun_notificacao', 'ID_MUNICIP'), ('mun_hospital', 'MUNICIPIO')]:
            out[target] = codigo(coluna(raw, field)).replace({'261160': 'Recife'}).fillna('Não informado')
        out['mun_residencia'] = out.municipio
        out['unidade_saude'] = codigo(coluna(raw, 'ID_UNIDADE')).fillna('Não informada')
        bairro = coluna(raw, 'NM_BAIRRO').map(normalizar_bairro)
        out['bairro_suspeito'] = ~bairro.isin(BAIRROS_RECIFE) | out.municipio.ne('Recife')
        out['bairro'] = bairro.mask(out.bairro_suspeito).fillna('Não informado')
        out['bairro_normalizado'] = bairro
        age_code = pd.to_numeric(codigo(coluna(raw, 'NU_IDADE_N')), errors='coerce')
        unit, amount = age_code // 1000, age_code % 1000
        age = amount * unit.map({1: 1 / 8760, 2: 1 / 365, 3: 1 / 12, 4: 1})
        out['idade_suspeita'] = (age_code.notna() & (~unit.isin([1, 2, 3, 4]) | ~age.between(0, 120)))
        out['idade'] = age.mask(out.idade_suspeita)
        out['faixa_etaria'] = pd.cut(out.idade, [-1, 4, 14, 24, 44, 64, 120],
                                    labels=['0–4', '5–14', '15–24', '25–44', '45–64', '65+']).astype('object').fillna('Não informado')
        out['sexo'] = codigo(coluna(raw, 'CS_SEXO')).map({'F': 'Feminino', 'M': 'Masculino', 'I': 'Ignorado'}).fillna('Não informado')
        out['raca'] = codigo(coluna(raw, 'CS_RACA')).map({'1': 'Branca', '2': 'Preta', '3': 'Amarela', '4': 'Parda', '5': 'Indígena', '9': 'Ignorado'}).fillna('Não informado')
        for field, label in SYMPTOMS.items():
            out['sintoma_' + label], out['informacao_' + field] = resposta(raw, field)
        for field, label in EXAMS.items():
            out['exame_' + label] = codigo(coluna(raw, field)).map(RESULT_LABELS).fillna('Não informado' if field in raw else 'Não disponível')
        for target, field in {'hospitalizado': 'HOSPITALIZ', 'hipertensao': 'HIPERTENSA', 'diabetes': 'DIABETES',
                              'renal': 'RENAL', 'hematologia': 'HEMATOLOG', 'hepatopatia': 'HEPATOPAT', 'autoimune': 'AUTO_IMUNE'}.items():
            out[target], out[target + '_informacao'] = resposta(raw, field)
        out['sinais_alarme'] = classification.eq('11').where(classification.isin(['10', '11', '12']))
        out['caso_grave'] = classification.eq('12').where(classification.isin(['10', '11', '12']))
        evolution = codigo(coluna(raw, 'EVOLUCAO'))
        out['obito'] = evolution.eq('2').where(evolution.isin(['1', '2', '3']))
        out['caso_encerrado'] = out.dt_encerramento.notna()
        out['casos'] = 1
        frames.append(out.copy())
    if not frames:
        raise FileNotFoundError(f'Nenhum CSV de arboviroses em {pasta}')
    result = pd.concat(frames, ignore_index=True)
    keys = pd.DataFrame({c: codigo(coluna(result, c)) for c in ['NU_NOTIFIC', 'ID_MUNICIP', 'NU_ANO', 'ID_AGRAVO']})
    result['possivel_duplicidade'] = keys.notna().all(axis=1) & keys.duplicated(keep=False)
    if not incluir_incompletos:
        result = result.loc[~result.registro_incompleto].copy()
    return result


def resumo_auditoria(frame):
    flags = ['registro_incompleto', 'possivel_duplicidade', 'sintomas_suspeitos', 'idade_suspeita',
             'bairro_suspeito', 'ano_divergente', 'semana_notificacao_divergente', 'semana_sintomas_divergente',
             'classificacao_desconhecida']
    flags += [c for c in frame if c.endswith(('_invalida', '_negativo', '_acima_120'))]
    return frame.groupby('arquivo_origem')[flags].sum().astype(int)


def resumo_intervalos(frame):
    rows = []
    for (arquivo, doenca), group in frame.groupby(['arquivo_origem', 'doenca']):
        for column, label in INTERVALS.items():
            values = group[column].dropna()
            q1, q3 = values.quantile([.25, .75])
            rows.append({'arquivo': arquivo, 'doenca': doenca, 'intervalo': label,
                         'validos': len(values), 'ausentes_ou_suspeitos': int(group[column].isna().sum()),
                         'mediana': values.median(), 'p95': values.quantile(.95),
                         'maximo': values.max(), 'acima_120': int(values.gt(120).sum()),
                         'outliers_iqr_superiores': int(values.gt(q3 + 1.5 * (q3 - q1)).sum())})
    return pd.DataFrame(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auditoria', type=Path, help='Pasta para salvar o resumo e os registros sinalizados.')
    args = parser.parse_args()
    dados = carregar_dados_tratados(incluir_incompletos=True)
    resumo = resumo_auditoria(dados)
    print(resumo.to_string())
    if args.auditoria:
        args.auditoria.mkdir(parents=True, exist_ok=True)
        resumo.to_csv(args.auditoria / 'resumo.csv', sep=';')
        flags = resumo.columns.tolist()
        columns = ['arquivo_origem', 'registro_origem'] + flags
        dados.loc[dados[flags].any(axis=1), columns].to_csv(args.auditoria / 'registros_sinalizados.csv', sep=';', index=False)
        resumo_intervalos(dados.loc[~dados.registro_incompleto]).to_csv(
            args.auditoria / 'intervalos.csv', sep=';', index=False)
