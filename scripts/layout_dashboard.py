"""
Layout e conteúdo das 3 páginas do dashboard (usado pelo fundo em PNG e pelo workbook do Tableau).
Posições em pixels de um painel fixo de 1400 x 900.
"""
import unicodedata

W, H = 1400, 900

AZUL_1, AZUL_2 = "#12294f", "#1f4f8f"
AMARELO = "#f2b632"
TILE_CORES = ["#f2b632", "#f5c85f", "#f6d27d"]
TEXTO = "#1c2a48"

KPIS = [(60, 110, 300, 135), (382, 110, 300, 135), (704, 110, 300, 135), (1026, 110, 314, 135)]
PRINCIPAL = (60, 270, 650, 590)
LATERAL = (735, 270, 605, 330)
TILES = [(735, 625, 188, 235), (943, 625, 188, 235), (1152, 625, 188, 235)]
DONUT = dict(centro=(1275, 177), raio=40)


def area_kpi(i):
    x, y, w, h = KPIS[i]
    return (x + 10, y + 35, (w - 120 if i == 3 else w - 20), h - 45)


def area_principal(legenda=False):
    x, y, w, h = PRINCIPAL
    return (x + 20, y + 50, w - 40, h - (100 if legenda else 65))


def area_lateral(legenda=False):
    x, y, w, h = LATERAL
    return (x + 20, y + 50, w - 40, h - (95 if legenda else 65))


# Paleta padrão do Tableau (ordem alfabética dos valores) -> usada nas legendas desenhadas no fundo
T10 = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1"]
LEG_FONTES = list(zip(["Hidráulica", "Solar", "Térmica", "Eólica"], T10))
LEG_ANOS = list(zip([str(a) for a in range(2020, 2027)], T10))
LEG_SUBS = list(zip(["Nordeste", "Norte", "Sudeste/CO", "Sul"], T10))


def area_tile(i):
    x, y, w, h = TILES[i]
    return (x + 10, y + 130, w - 20, 80)


PAGINAS = ["Preço", "Matriz", "Reservatórios"]
ABAS = {
    "Preço": (955, 36, 100, 34),
    "Matriz": (1065, 36, 110, 34),
    "Reservatórios": (1185, 36, 155, 34),
}

TITULO = "Energia no Brasil"

CONTEUDO = {
    "Preço": dict(
        subtitulo="Custo da energia (CMO) · dados do ONS, jan/2020 até hoje",
        kpis=[("CMO MÉDIO NO ANO · SE/CO", "c_preco_ano"), ("VARIAÇÃO VS. ANO ANTERIOR", "c_preco_var"),
              ("HORAS COM CMO ≥ R$ 500/MWh", "c_horas_500"), ("HORAS COM CMO ZERO", "c_horas_zero")],
        donut="pct_horas_zero",
        principal=("CMO MÉDIO MENSAL · SUDESTE/CENTRO-OESTE (R$/MWh)", "CMO mensal"),
        lateral=("CMO MÉDIO POR HORA DO DIA · ANO ATUAL (R$/MWh)", "CMO por hora"),
        tiles=[("PICO DO ANO", "c_pico"), ("PERÍODO SECO", "c_seco"), ("PERÍODO ÚMIDO", "c_umido")],
        icones=["▲", "☀", "☂"],
    ),
    "Matriz": dict(
        subtitulo="De onde vem a energia do Brasil · geração por fonte",
        kpis=[("RENOVÁVEIS NO ANO", "m_renov"), ("SOLAR NO ANO", "m_solar"),
              ("TÉRMICAS NO ANO", "m_termica"), ("EÓLICA + SOLAR NO ANO", "m_eol_sol")],
        donut="pct_eol_sol",
        principal=("GERAÇÃO POR FONTE (TWh POR ANO)", "Geracao por ano"),
        lateral=("PERFIL MÉDIO POR HORA DO DIA · ANO ATUAL (GW)", "Perfil horario"),
        leg_principal=LEG_FONTES, leg_lateral=LEG_FONTES,
        tiles=[("SOLAR VS. 2020", "m_solar_x"), ("PICO SOLAR (GW)", "m_pico_solar"), ("HIDRELÉTRICAS", "m_hidro")],
        icones=["☀", "▲", "≈"],
    ),
    "Reservatórios": dict(
        subtitulo="Chuva, reservatórios e o preço da energia",
        kpis=[("RESERVATÓRIOS SE/CO · ÚLTIMO DIA", "c_ear_hoje"), ("CHUVA NO ANO · % DA MÉDIA (SE/CO)", "c_ena_ano"),
              ("CMO COM RESERVATÓRIO < 40%", "c_cmo_ear40"), ("RESERVATÓRIO MÉDIO NO ANO", "c_ear_ano")],
        donut="pct_ear_ano",
        principal=("RESERVATÓRIO x PREÇO · CADA PONTO É UM MÊS (SE/CO)", "EAR x CMO"),
        lateral=("RESERVATÓRIOS POR SUBSISTEMA (% DA CAPACIDADE)", "EAR subsistemas"),
        leg_principal=LEG_ANOS, leg_lateral=LEG_SUBS,
        tiles=[("CMO C/ RESERV. > 60%", "c_cmo_ear60"), ("TÉRMICAS C/ RESERV. < 40%", "c_term_ear40"),
               ("TÉRMICAS C/ RESERV. > 60%", "c_term_ear60")],
        icones=["≈", "▲", "▼"],
    ),
}


def slug(pagina):
    s = unicodedata.normalize("NFKD", pagina).encode("ascii", "ignore").decode().lower()
    return s.replace(" ", "_")
