"""
Gera o XML das planilhas, painéis e navegação do dashboard do Tableau (3 páginas, 2 fontes de dados).
Usado por scripts/montar_twbx.py, que injeta este XML no pacote base criado no Tableau Public
(o pacote base guarda as conexões com os Excel da camada gold e as extrações .hyper).
"""
import sys
import uuid
from pathlib import Path
from xml.sax.saxutils import quoteattr

sys.path.insert(0, str(Path(__file__).parent))
import layout_dashboard as L  # noqa: E402

# Nomes internos das fontes de dados (substituídos pelos reais em montar_twbx.py)
DS = {"energia": "federated.energia", "matriz": "federated.matriz"}
CAPTION = {"energia": "Energia horária (gold)", "matriz": "Matriz por fonte (gold)"}
SIMPLE_ID = True

COLUNAS = {
    "energia": {
        "data_hora": "datetime", "data": "date", "ano": "integer", "mes": "integer", "nome_mes": "string",
        "inicio_mes": "date", "periodo_hidrologico": "string", "hora": "integer", "subsistema_id": "string",
        "subsistema": "string", "cmo": "real", "ger_hidraulica": "real", "ger_termica": "real",
        "ger_eolica": "real", "ger_solar": "real", "ger_total": "real", "ger_renovavel": "real",
        "carga": "real", "intercambio": "real", "ear_pct": "real", "ena_pct_mlt": "real",
        "faixa_reservatorio": "string", "hora_cmo_zero": "integer", "hora_cmo_acima_500": "integer",
    },
    "matriz": {
        "ano": "integer", "mes": "integer", "hora": "integer", "fonte": "string",
        "geracao_mwmed": "real", "energia_twh": "real", "horas": "integer",
    },
}


# ---------------------------------------------------------------- campos calculados
def milhar(expr):
    return (f"IF ({expr}) >= 1000 THEN STR(INT(({expr})/1000)) + '.' + RIGHT('000' + STR(INT({expr}) % 1000), 3) "
            f"ELSE STR(INT({expr})) END")


def dec(expr, casas=1):
    return f"REPLACE(STR(ROUND({expr}, {casas})), '.', ',')"


def reais(expr):
    return f"'R$ ' + {milhar(f'ROUND({expr}, 0)')}"


ATUAL = "[ano] = { FIXED : MAX([ano]) }"
ANTERIOR = "[ano] = { FIXED : MAX([ano]) } - 1"
SE = "[subsistema_id] = 'SE'"


def cmo_se(cond=""):
    return f"AVG(IF {SE}{' AND ' + cond if cond else ''} THEN [cmo] END)"


def share(fontes, cond=ATUAL):
    lista = " OR ".join(f"[fonte] = '{f}'" for f in fontes)
    return (f"SUM(IF {cond} AND ({lista}) THEN [energia_twh] END) / SUM(IF {cond} THEN [energia_twh] END) * 100")


# nome -> (fonte de dados, legenda, fórmula, tipo, papel)
CALCULOS = {
    # ---------- Preço (energia)
    "c_preco_ano": ("energia", "CMO médio no ano (texto)", reais(cmo_se(ATUAL)) + " + '/MWh'", "string", "dimension"),
    "c_preco_var": ("energia", "Variação vs ano anterior (texto)",
                    f"IF {cmo_se(ATUAL)} >= {cmo_se(ANTERIOR)} THEN '+' ELSE '' END + "
                    + dec(f"({cmo_se(ATUAL)} / {cmo_se(ANTERIOR)} - 1) * 100") + " + '%'", "string", "dimension"),
    "c_horas_500": ("energia", "Horas CMO >= 500 (texto)",
                    milhar(f"SUM(IF {SE} AND {ATUAL} THEN [hora_cmo_acima_500] ELSE 0 END)"), "string", "dimension"),
    "c_horas_zero": ("energia", "% horas CMO zero (texto)",
                     dec(f"AVG(IF {SE} AND {ATUAL} THEN [hora_cmo_zero] END) * 100") + " + '%'", "string", "dimension"),
    "c_pico": ("energia", "Pico do ano (texto)", reais(f"MAX(IF {SE} AND {ATUAL} THEN [cmo] END)"), "string", "dimension"),
    "c_seco": ("energia", "CMO período seco (texto)", reais(cmo_se(f"{ATUAL} AND [periodo_hidrologico] = 'Seco'")), "string", "dimension"),
    "c_umido": ("energia", "CMO período úmido (texto)", reais(cmo_se(f"{ATUAL} AND [periodo_hidrologico] = 'Úmido'")), "string", "dimension"),
    "c_cmo_se_mensal": ("energia", "CMO SE/CO (R$/MWh)", f"ROUND({cmo_se()}, 0)", "real", "measure"),
    "c_cmo_se_hora": ("energia", "CMO SE/CO no ano (R$/MWh)", f"ROUND({cmo_se(ATUAL)}, 0)", "real", "measure"),
    # ---------- Reservatórios (energia)
    "c_ear_hoje": ("energia", "Reservatório último dia (texto)",
                   dec(f"AVG(IF {SE} AND [data] = {{ FIXED : MAX([data]) }} THEN [ear_pct] END)") + " + '%'", "string", "dimension"),
    "c_ena_ano": ("energia", "Chuva no ano (texto)", dec(f"AVG(IF {SE} AND {ATUAL} THEN [ena_pct_mlt] END)") + " + '%'", "string", "dimension"),
    "c_cmo_ear40": ("energia", "CMO com reservatório < 40% (texto)", reais(cmo_se("[ear_pct] < 40")), "string", "dimension"),
    "c_cmo_ear60": ("energia", "CMO com reservatório > 60% (texto)", reais(cmo_se("[ear_pct] > 60")), "string", "dimension"),
    "c_ear_ano": ("energia", "Reservatório médio no ano (texto)", dec(f"AVG(IF {SE} AND {ATUAL} THEN [ear_pct] END)") + " + '%'", "string", "dimension"),
    "c_term_ear40": ("energia", "Térmicas com reservatório < 40% (texto)",
                     dec("SUM(IF [ear_pct] < 40 THEN [ger_termica] END) / SUM(IF [ear_pct] < 40 THEN [ger_total] END) * 100") + " + '%'",
                     "string", "dimension"),
    "c_term_ear60": ("energia", "Térmicas com reservatório > 60% (texto)",
                     dec("SUM(IF [ear_pct] > 60 THEN [ger_termica] END) / SUM(IF [ear_pct] > 60 THEN [ger_total] END) * 100") + " + '%'",
                     "string", "dimension"),
    "c_ear_se": ("energia", "Reservatório SE/CO (%)", f"ROUND(AVG(IF {SE} THEN [ear_pct] END), 1)", "real", "measure"),
    "c_ear_media": ("energia", "Reservatório (%)", "ROUND(AVG([ear_pct]), 1)", "real", "measure"),
    # ---------- Matriz
    "m_renov": ("matriz", "Renováveis no ano (texto)", dec(share(["1. Hidráulica", "2. Solar", "4. Eólica"])) + " + '%'", "string", "dimension"),
    "m_solar": ("matriz", "Solar no ano (texto)", dec(share(["2. Solar"])) + " + '%'", "string", "dimension"),
    "m_termica": ("matriz", "Térmicas no ano (texto)", dec(share(["3. Térmica"])) + " + '%'", "string", "dimension"),
    "m_eol_sol": ("matriz", "Eólica + solar no ano (texto)", dec(share(["2. Solar", "4. Eólica"])) + " + '%'", "string", "dimension"),
    "m_hidro": ("matriz", "Hidrelétricas no ano (texto)", dec(share(["1. Hidráulica"])) + " + '%'", "string", "dimension"),
    "m_solar_x": ("matriz", "Solar vs 2020 (texto)",
                  "STR(ROUND(AVG(IF " + ATUAL + " AND [fonte] = '2. Solar' THEN [geracao_mwmed] END) / "
                  "AVG(IF [ano] = 2020 AND [fonte] = '2. Solar' THEN [geracao_mwmed] END), 0)) + 'x maior'", "string", "dimension"),
    "m_pico_solar": ("matriz", "Pico solar (texto)",
                     dec(f"MAX(IF {ATUAL} AND [fonte] = '2. Solar' THEN [geracao_mwmed] END) / 1000") + " + ' GW'", "string", "dimension"),
    "m_twh": ("matriz", "Geração (TWh)", "ROUND(SUM([energia_twh]), 1)", "real", "measure"),
    "m_gw_ano": ("matriz", "Geração média no ano (GW)", f"ROUND(AVG(IF {ATUAL} THEN [geracao_mwmed] END) / 1000, 1)", "real", "measure"),
}


def uuid_de(texto):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "energia-" + texto)).upper()


def sid(texto, recuo=6):
    return f"\n{' ' * recuo}<simple-id uuid='{{{uuid_de(texto)}}}' />" if SIMPLE_ID else ""


def coluna_calc(n, recuo):
    _, cap, f, t, papel = CALCULOS[n]
    esp = " " * recuo
    tipo = "quantitative" if papel == "measure" else "nominal"
    return (f"{esp}<column caption={quoteattr(cap)} datatype='{t}' name='[{n}]' role='{papel}' type='{tipo}'>\n"
            f"{esp}  <calculation class='tableau' formula={quoteattr(f)} />\n{esp}</column>")


def colunas_calculadas(ds, recuo=6):
    return "\n".join(coluna_calc(n, recuo) for n, v in CALCULOS.items() if v[0] == ds)


# ---------------------------------------------------------------- planilhas
def ref(ds, inst):
    return f"[{DS[ds]}].[{inst}]"


def deps(ds, *itens):
    cols, inst, vistos = [], [], set()
    for col, der, tipo, nome in itens:
        if col not in vistos:
            vistos.add(col)
            if col in CALCULOS:
                cols.append(coluna_calc(col, 12))
            else:
                t = COLUNAS[ds][col]
                papel = "measure" if t in ("real", "integer") else "dimension"
                tp = "quantitative" if papel == "measure" else ("ordinal" if t in ("date", "datetime") else "nominal")
                cols.append(f"            <column datatype='{t}' name='[{col}]' role='{papel}' type='{tp}' />")
        inst.append(f"            <column-instance column='[{col}]' derivation='{der}' name='[{nome}]' pivot='key' type='{tipo}' />")
    return (f"          <datasource-dependencies datasource='{DS[ds]}'>\n" + "\n".join(cols) + "\n"
            + "\n".join(inst) + "\n          </datasource-dependencies>")


def worksheet(nome, ds, dependencias, painel, linhas="", colunas="", estilo="", extras_view=""):
    return f"""    <worksheet name={quoteattr(nome)}>
      <table>
        <view>
          <datasources>
            <datasource caption={quoteattr(CAPTION[ds])} name='{DS[ds]}' />
          </datasources>
{dependencias}
{extras_view}          <aggregation value='true' />
        </view>
        <style>
{estilo}
        </style>
        <panes>
{painel}
        </panes>
        <rows>{linhas}</rows>
        <cols>{colunas}</cols>
      </table>{sid(nome)}
    </worksheet>"""


def planilha_texto(nome, calc, fundo, cor, tamanho, largura, altura):
    ds = CALCULOS[calc][0]
    inst = f"usr:{calc}:nk"
    estilo = f"""          <style-rule element='table'>
            <format attr='background-color' value='{fundo}' />
          </style-rule>
          <style-rule element='cell'>
            <format attr='width' value='{largura}' />
            <format attr='height' value='{altura}' />
            <format attr='text-align' value='center' />
            <format attr='vertical-align' value='center' />
          </style-rule>"""
    painel = f"""          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Text' />
            <encodings>
              <text column='{ref(ds, inst)}' />
            </encodings>
            <customized-label>
              <formatted-text>
                <run bold='true' fontcolor='{cor}' fontsize='{tamanho}'>&lt;{ref(ds, inst)}&gt;</run>
              </formatted-text>
            </customized-label>
            <style>
              <style-rule element='mark'>
                <format attr='mark-labels-show' value='true' />
                <format attr='mark-color' value='{fundo}' />
              </style-rule>
            </style>
          </pane>"""
    return worksheet(nome, ds, deps(ds, (calc, "User", "nominal", inst)), painel, estilo=estilo)


def estilo_grafico(ds, eixo, escopo, esconder="cols", largura=None, altura=None, sem_titulo_x=None):
    s = f"""          <style-rule element='axis'>
            <format attr='title' class='0' field='{ref(ds, eixo)}' scope='{escopo}' value='' />"""
    if sem_titulo_x:
        s += f"\n            <format attr='title' class='0' field='{ref(ds, sem_titulo_x)}' scope='cols' value='' />"
    s += f"""
          </style-rule>
          <style-rule element='worksheet'>
            <format attr='display-field-labels' scope='{esconder}' value='false' />
            <format attr='show-null-value-warning' value='false' />
          </style-rule>
          <style-rule element='gridline'>
            <format attr='line-visibility' value='off' />
          </style-rule>"""
    cel = []
    if largura:
        cel.append(f"<format attr='width' value='{largura}' />")
    if altura:
        cel.append(f"<format attr='height' value='{altura}' />")
    if cel:
        s += "\n          <style-rule element='cell'>\n" + "\n".join("            " + c for c in cel) + "\n          </style-rule>"
    return s


def painel(ds, classe, cor=None, cor_campo=None, detalhe=None, rotulos=False, extra=None):
    encs = []
    if cor_campo:
        encs.append(f"<color column='{ref(ds, cor_campo)}' />")
    if detalhe:
        encs.append(f"<lod column='{ref(ds, detalhe)}' />")
    enc = ("\n            <encodings>\n" + "\n".join("              " + e for e in encs) + "\n            </encodings>") if encs else ""
    fm = []
    if cor:
        fm.append(f"<format attr='mark-color' value='{cor}' />")
    if rotulos:
        fm.append("<format attr='mark-labels-show' value='true' />")
    if extra:
        fm.append(extra)
    est = ""
    if fm:
        est = ("\n            <style>\n              <style-rule element='mark'>\n"
               + "\n".join("                " + f for f in fm) + "\n              </style-rule>\n            </style>")
    return f"""          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{classe}' />{enc}{est}
          </pane>"""


def graficos():
    E, M = "energia", "matriz"
    mes_c = "tmn:inicio_mes:qk"             # mês contínuo
    hora_d, ano_d = "none:hora:ok", "none:ano:ok"
    p, lat = L.area_principal(), L.area_lateral()
    return [
        # CMO mensal (linha contínua)
        worksheet("CMO mensal", E,
                  deps(E, ("inicio_mes", "Month-Trunc", "quantitative", mes_c),
                       ("c_cmo_se_mensal", "User", "quantitative", "usr:c_cmo_se_mensal:qk")),
                  painel(E, "Line", cor=L.AZUL_2),
                  linhas=ref(E, "usr:c_cmo_se_mensal:qk"), colunas=ref(E, mes_c),
                  estilo=estilo_grafico(E, "usr:c_cmo_se_mensal:qk", "rows", sem_titulo_x=mes_c)),
        # CMO por hora do dia (barras)
        worksheet("CMO por hora", E,
                  deps(E, ("hora", "None", "ordinal", hora_d),
                       ("c_cmo_se_hora", "User", "quantitative", "usr:c_cmo_se_hora:qk")),
                  painel(E, "Bar", cor=L.AMARELO),
                  linhas=ref(E, "usr:c_cmo_se_hora:qk"), colunas=ref(E, hora_d),
                  estilo=estilo_grafico(E, "usr:c_cmo_se_hora:qk", "rows", largura=(lat[2] - 60) // 24)),
        # Geração por ano, empilhada por fonte
        worksheet("Geracao por ano", M,
                  deps(M, ("ano", "None", "ordinal", ano_d), ("fonte", "None", "nominal", "none:fonte:nk"),
                       ("m_twh", "User", "quantitative", "usr:m_twh:qk")),
                  painel(M, "Bar", cor_campo="none:fonte:nk"),
                  linhas=ref(M, "usr:m_twh:qk"), colunas=ref(M, ano_d),
                  estilo=estilo_grafico(M, "usr:m_twh:qk", "rows", largura=(p[2] - 80) // 7)),
        # Perfil horário do ano atual, empilhado por fonte
        worksheet("Perfil horario", M,
                  deps(M, ("hora", "None", "ordinal", hora_d), ("fonte", "None", "nominal", "none:fonte:nk"),
                       ("m_gw_ano", "User", "quantitative", "usr:m_gw_ano:qk")),
                  painel(M, "Bar", cor_campo="none:fonte:nk"),
                  linhas=ref(M, "usr:m_gw_ano:qk"), colunas=ref(M, hora_d),
                  estilo=estilo_grafico(M, "usr:m_gw_ano:qk", "rows", largura=(lat[2] - 60) // 24)),
        # Dispersão reservatório x preço (cada ponto = mês)
        worksheet("EAR x CMO", E,
                  deps(E, ("c_ear_se", "User", "quantitative", "usr:c_ear_se:qk"),
                       ("c_cmo_se_mensal", "User", "quantitative", "usr:c_cmo_se_mensal:qk"),
                       ("inicio_mes", "None", "ordinal", "none:inicio_mes:ok"), ("ano", "None", "ordinal", ano_d)),
                  painel(E, "Circle", cor_campo=ano_d, detalhe="none:inicio_mes:ok"),
                  linhas=ref(E, "usr:c_cmo_se_mensal:qk"), colunas=ref(E, "usr:c_ear_se:qk"),
                  estilo=estilo_grafico(E, "usr:c_cmo_se_mensal:qk", "rows", sem_titulo_x="usr:c_ear_se:qk")),
        # Reservatórios por subsistema (linhas)
        worksheet("EAR subsistemas", E,
                  deps(E, ("inicio_mes", "Month-Trunc", "quantitative", mes_c), ("subsistema", "None", "nominal", "none:subsistema:nk"),
                       ("c_ear_media", "User", "quantitative", "usr:c_ear_media:qk")),
                  painel(E, "Line", cor_campo="none:subsistema:nk"),
                  linhas=ref(E, "usr:c_ear_media:qk"), colunas=ref(E, mes_c),
                  estilo=estilo_grafico(E, "usr:c_ear_media:qk", "rows", sem_titulo_x=mes_c)),
    ]


NOMES_GRAFICOS = ["CMO mensal", "CMO por hora", "Geracao por ano", "Perfil horario", "EAR x CMO", "EAR subsistemas"]


def planilhas_texto():
    saida = {}
    for pagina in L.PAGINAS:
        c = L.CONTEUDO[pagina]
        for i, (_, calc) in enumerate(c["kpis"]):
            _, _, w, h = L.area_kpi(i)
            nome = "KPI · " + CALCULOS[calc][1].replace(" (texto)", "")
            saida[("KPI", calc)] = (nome, planilha_texto(nome, calc, "#ffffff", L.TEXTO, 30, w - 4, h - 4))
        for i, (_, calc) in enumerate(c["tiles"]):
            _, _, w, h = L.area_tile(i)
            nome = "Tile · " + CALCULOS[calc][1].replace(" (texto)", "")
            saida[("Tile", calc, i)] = (nome, planilha_texto(nome, calc, L.TILE_CORES[i], "#ffffff", 22, w - 4, h - 4))
    return saida


# ---------------------------------------------------------------- painéis e navegação
def u(v, total):
    return round(v / total * 100000)


def zona(zid, nome, box):
    x, y, w, h = box
    return (f"        <zone h='{u(h, L.H)}' id='{zid}' name={quoteattr(nome)} show-title='false' "
            f"w='{u(w, L.W)}' x='{u(x, L.W)}' y='{u(y, L.H)}' />")


def botao(zid, destino, box):
    x, y, w, h = box
    alvo = uuid_de("w-dash-" + destino)
    return f"""        <zone h='{u(h, L.H)}' id='{zid}' type-v2='dashboard-object' w='{u(w, L.W)}' x='{u(x, L.W)}' y='{u(y, L.H)}'>
          <button action='tabdoc:goto-sheet window-id=&quot;{{{alvo}}}&quot;' button-type='text'>
            <button-visual-state>
              <caption>{destino.upper()}</caption>
              <button-caption-font-style fontcolor='#ffffff' fontname='Tableau Bold' fontsize='11' />
              <format attr='background-color' value='#ffffff00' />
            </button-visual-state>
          </button>
        </zone>"""


def dashboards(textos):
    saida, visoes = [], {}
    for pagina in L.PAGINAS:
        c = L.CONTEUDO[pagina]
        zonas = ["        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0' />",
                 f"        <zone h='100000' id='2' is-scaled='1' param='Image/fundo_{L.slug(pagina)}.png' type-v2='bitmap' w='100000' x='0' y='0' />"]
        itens = [(textos[("KPI", calc)][0], L.area_kpi(i)) for i, (_, calc) in enumerate(c["kpis"])]
        itens += [(textos[("Tile", calc, i)][0], L.area_tile(i)) for i, (_, calc) in enumerate(c["tiles"])]
        itens += [(c["principal"][1], L.area_principal("leg_principal" in c)),
                  (c["lateral"][1], L.area_lateral("leg_lateral" in c))]
        zid = 3
        for nome, box in itens:
            zonas.append(zona(zid, nome, box))
            zid += 1
        for destino, box in L.ABAS.items():
            zonas.append(botao(zid, destino, box))
            zid += 1
        visoes[pagina] = [n for n, _ in itens]
        saida.append(f"""    <dashboard name={quoteattr(pagina)}>
      <style />
      <size maxheight='{L.H}' maxwidth='{L.W}' minheight='{L.H}' minwidth='{L.W}' sizing-mode='fixed' />
      <zones>
{chr(10).join(zonas)}
      </zones>{sid('dash-' + pagina)}
    </dashboard>""")
    return "\n".join(saida), visoes


def janelas(planilhas, visoes):
    ws = "\n".join(f"""    <window class='worksheet' hidden='true' maximized='true' name={quoteattr(n)}>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
        </edge>
      </cards>{sid('w-' + n)}
    </window>""" for n in planilhas)
    ds = "\n".join(f"""    <window class='dashboard' {"maximized='true' " if i == 0 else ""}name={quoteattr(p)}>
      <viewpoints>
{chr(10).join(f"        <viewpoint name={quoteattr(v)} />" for v in visoes[p])}
      </viewpoints>
      <active id='-1' />{sid('w-dash-' + p)}
    </window>""" for i, p in enumerate(L.PAGINAS))
    return f"  <windows source-height='30'>\n{ds}\n{ws}\n  </windows>"


def montar_xml():
    textos = planilhas_texto()
    planilhas = [x for _, x in textos.values()] + graficos()
    nomes = [n for n, _ in textos.values()] + NOMES_GRAFICOS
    dash, visoes = dashboards(textos)
    return (f"  <worksheets>\n{chr(10).join(planilhas)}\n  </worksheets>\n"
            f"  <dashboards>\n{dash}\n  </dashboards>\n{janelas(nomes, visoes)}")
