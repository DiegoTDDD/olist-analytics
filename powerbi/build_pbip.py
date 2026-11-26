"""Generate the Power BI project (PBIP) for the Olist star schema.

    python powerbi/build_pbip.py

Writes powerbi/OlistEntregas.pbip with its semantic model (TMDL) and report (PBIR). The model
imports the six Parquet files from data/powerbi/ (written by export_powerbi.py) through the
DataFolder parameter; open the .pbip in Power BI Desktop, set DataFolder to the absolute path of
data/powerbi on your machine and refresh.

Everything is generated from this file so the model, the measures and the pages can be reviewed
as code and rebuilt identically.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "OlistEntregas"
# Where Power BI looks for the Parquet files: a URL or a local folder. Change it in Power BI
# (Transform data > Edit parameters) or set OLIST_PBI_FOLDER before generating.
# Default: the committed files on GitHub, so the report refreshes with no setup. A local folder
# (for example C:\olist-analytics\data\powerbi) works too.
DEFAULT_FOLDER = os.environ.get(
    "OLIST_PBI_FOLDER", "https://raw.githubusercontent.com/DiegoTDDD/olist-analytics/main/data/powerbi"
)

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
VISUAL_SCHEMA = f"{SCHEMA}/item/report/definition/visualContainer/2.4.0/schema.json"
PAGE_SCHEMA = f"{SCHEMA}/item/report/definition/page/2.0.0/schema.json"

# Theme colors, shared by the theme file and by explicit formatting below.
NAVY, TEAL, AMBER, INK, MUTED, PAPER, CARD = "#13233A", "#0B7A70", "#B45309", "#13233A", "#5B6676", "#F3F5F7", "#FFFFFF"


def uid(seed: str) -> str:
    """Stable 20-character id, so regenerating does not churn every file name."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"olist-powerbi/{seed}").hex[:20]


def guid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"olist-powerbi/{seed}"))


# ---------------------------------------------------------------- semantic model

# table -> (parquet file, [(column name, source column, dataType, formatString or None, extra props)])
TABLES = {
    "Pedidos": ("fct_orders", [
        ("ID do pedido", "order_id", "string", None, {}),
        ("ID do cliente", "customer_id", "string", None, {"isHidden": True}),
        ("Status", "status", "string", None, {}),
        ("Data da compra", "purchase_date", "dateTime", "dd/mm/yyyy", {}),
        ("Valor pago", "total_payment_value", "decimal", "\\R$ #,0.00", {}),
        ("Parcelas", "max_installments", "int64", "0", {}),
        ("Itens", "item_count", "int64", "0", {}),
        ("Valor dos itens", "total_item_price", "decimal", "\\R$ #,0.00", {}),
        ("Frete", "total_freight", "decimal", "\\R$ #,0.00", {}),
        ("Nota", "review_score", "int64", "0", {}),
        ("Dias até a entrega", "delivery_days", "int64", "0", {}),
        ("Dias de atraso", "delay_days", "int64", "0", {}),
        ("Atrasado", "is_delayed", "boolean", None, {}),
    ]),
    "Itens": ("fct_order_items", [
        ("ID do pedido", "order_id", "string", None, {"isHidden": True}),
        ("Item", "order_item_id", "int64", "0", {}),
        ("ID do produto", "product_id", "string", None, {"isHidden": True}),
        ("ID do vendedor", "seller_id", "string", None, {"isHidden": True}),
        ("Status", "status", "string", None, {}),
        ("Data da compra", "purchase_date", "dateTime", "dd/mm/yyyy", {"isHidden": True}),
        ("Preço", "price", "decimal", "\\R$ #,0.00", {}),
        ("Frete", "freight_value", "decimal", "\\R$ #,0.00", {}),
        ("Atrasado", "is_delayed", "boolean", None, {}),
        ("Dias de atraso", "delay_days", "int64", "0", {}),
        ("Nota", "review_score", "int64", "0", {}),
    ]),
    "Clientes": ("dim_customers", [
        ("ID do cliente", "customer_id", "string", None, {"isHidden": True}),
        ("ID único do cliente", "customer_unique_id", "string", None, {}),
        ("CEP (prefixo)", "customer_zip_code_prefix", "string", None, {}),
        ("Cidade", "customer_city", "string", None, {}),
        ("Estado", "customer_state", "string", None, {"dataCategory": "StateOrProvince"}),
    ]),
    "Produtos": ("dim_products", [
        ("ID do produto", "product_id", "string", None, {"isHidden": True}),
        ("Categoria original", "product_category_name", "string", None, {"isHidden": True}),
        ("Categoria", "category_name_pt", "string", None, {}),
        ("Categoria (inglês)", "category_name_english", "string", None, {}),
        ("Peso (g)", "product_weight_g", "int64", "#,0", {}),
        ("Comprimento (cm)", "product_length_cm", "int64", "0", {}),
        ("Altura (cm)", "product_height_cm", "int64", "0", {}),
        ("Largura (cm)", "product_width_cm", "int64", "0", {}),
        ("Fotos", "product_photos_qty", "int64", "0", {}),
    ]),
    "Vendedores": ("dim_sellers", [
        ("ID do vendedor", "seller_id", "string", None, {}),
        ("CEP (prefixo)", "seller_zip_code_prefix", "string", None, {}),
        ("Cidade", "seller_city", "string", None, {}),
        ("Estado do vendedor", "seller_state", "string", None, {"dataCategory": "StateOrProvince"}),
    ]),
    "Calendário": ("dim_dates", [
        ("Data", "date_day", "dateTime", "dd/mm/yyyy", {"isKey": True}),
        ("Ano", "year", "int64", "0", {"summarizeBy": "none"}),
        ("Trimestre", "quarter", "int64", "0", {"summarizeBy": "none"}),
        ("Mês nº", "month", "int64", "0", {"summarizeBy": "none", "isHidden": True}),
        ("Dia", "day", "int64", "0", {"summarizeBy": "none"}),
        ("Dia da semana nº", "day_of_week", "int64", "0", {"summarizeBy": "none", "isHidden": True}),
        ("Dia da semana (inglês)", "day_name", "string", None, {"isHidden": True}),
        ("Mês (inglês)", "month_name", "string", None, {"isHidden": True}),
        ("Fim de semana", "is_weekend", "boolean", None, {}),
    ]),
}  # fmt: skip

M_TYPES = {"string": "type text", "dateTime": "type date", "decimal": "Currency.Type", "int64": "Int64.Type",
           "boolean": "type logical", "double": "type number"}  # fmt: skip

# table -> [(name, DAX, dataType, formatString, extra props)]
CALC_COLUMNS = {
    "Pedidos": [
        ("Faixa de atraso", """
VAR d = Pedidos[Dias de atraso]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( d ), "Não entregue",
        d <= 0, "No prazo",
        d >= 11, "11+ dias",
        d = 1, "1 dia",
        FORMAT ( d, "0" ) & " dias"
    )""", "string", None, {"sortByColumn": "Faixa ordem"}),
        ("Faixa ordem", """
VAR d = Pedidos[Dias de atraso]
RETURN SWITCH ( TRUE (), ISBLANK ( d ), 99, d <= 0, 0, d >= 11, 11, d )""", "int64", "0",
         {"isHidden": True, "summarizeBy": "none"}),
    ],
    "Calendário": [
        ("Ano-mês", "'Calendário'[Ano] * 100 + 'Calendário'[Mês nº]", "int64", "0",
         {"isHidden": True, "summarizeBy": "none"}),
        ("Mês", 'FORMAT ( \'Calendário\'[Data], "mmm/yy" )', "string", None, {"sortByColumn": "Ano-mês"}),
    ],
}  # fmt: skip

DELIVERED = 'Pedidos[Status] = "delivered"'

# (name, DAX, formatString, display folder, description)
MEASURES = [
    ("Faturamento", "SUM ( Pedidos[Valor pago] )", "\\R$ #,0", "Vendas",
     "Soma do valor pago pelos pedidos, todas as formas de pagamento."),
    ("Pedidos (qtd)", "COUNTROWS ( Pedidos )", "#,0", "Vendas", "Quantidade de pedidos."),
    ("Ticket médio", "DIVIDE ( [Faturamento], [Pedidos (qtd)] )", "\\R$ #,0.00", "Vendas",
     "Faturamento dividido pela quantidade de pedidos."),
    ("Faturamento ano anterior",
     "CALCULATE ( [Faturamento], SAMEPERIODLASTYEAR ( 'Calendário'[Data] ) )", "\\R$ #,0", "Vendas",
     "Faturamento no mesmo período do ano anterior."),
    ("Crescimento anual %",
     "VAR anterior = [Faturamento ano anterior]\nRETURN IF ( NOT ISBLANK ( anterior ), DIVIDE ( [Faturamento] - anterior, anterior ) )",
     "+0.0%;-0.0%;0.0%", "Vendas", "Variação do faturamento contra o mesmo período do ano anterior."),
    ("Pedidos entregues", f"CALCULATE ( [Pedidos (qtd)], {DELIVERED} )", "#,0", "Entrega",
     "Pedidos com status entregue."),
    ("Pedidos atrasados", f"CALCULATE ( [Pedidos (qtd)], {DELIVERED}, Pedidos[Atrasado] = TRUE () )", "#,0",
     "Entrega", "Pedidos entregues num dia posterior à data prometida."),
    ("% atrasados", "DIVIDE ( [Pedidos atrasados], [Pedidos entregues] )", "0.0%", "Entrega",
     "Parcela dos pedidos entregues que chegou depois do dia prometido."),
    ("Dias médios até a entrega", f"CALCULATE ( AVERAGE ( Pedidos[Dias até a entrega] ), {DELIVERED} )", "0.0",
     "Entrega", "Média de dias entre a compra e a entrega."),
    ("Nota média", "AVERAGE ( Pedidos[Nota] )", "0.00", "Satisfação",
     "Média da nota de avaliação (1 a 5), última avaliação de cada pedido."),
    ("Nota média (entregues)",
     f"CALCULATE ( [Nota média], {DELIVERED}, NOT ISBLANK ( Pedidos[Dias de atraso] ) )", "0.00", "Satisfação",
     "Nota média só dos pedidos entregues, base da análise de atraso."),
    ("% nota 1",
     "DIVIDE (\n    CALCULATE ( COUNTROWS ( Pedidos ), Pedidos[Nota] = 1 ),\n"
     "    CALCULATE ( COUNTROWS ( Pedidos ), NOT ISBLANK ( Pedidos[Nota] ) )\n)",
     "0.0%", "Satisfação", "Parcela das avaliações com nota 1."),
    ("% nota 1 (entregues)",
     f"CALCULATE ( [% nota 1], {DELIVERED}, NOT ISBLANK ( Pedidos[Dias de atraso] ) )", "0.0%", "Satisfação",
     "Parcela de notas 1 entre os pedidos entregues."),
    ("Nota no prazo", f"CALCULATE ( [Nota média], {DELIVERED}, Pedidos[Atrasado] = FALSE () )", "0.00",
     "Satisfação", "Nota média dos pedidos entregues até o dia prometido."),
    ("Nota com atraso", f"CALCULATE ( [Nota média], {DELIVERED}, Pedidos[Atrasado] = TRUE () )", "0.00",
     "Satisfação", "Nota média dos pedidos entregues depois do dia prometido."),
    ("Pontos perdidos no atraso", "[Nota no prazo] - [Nota com atraso]", "0.00", "Satisfação",
     "Diferença de nota entre pedidos no prazo e atrasados."),
    ("Faturamento (meses completos)",
     "VAR mes = SELECTEDVALUE ( 'Calendário'[Ano-mês] )\nRETURN IF ( mes >= 201701 && mes <= 201808, [Faturamento] )",
     "\\R$ #,0", "Vendas",
     "Faturamento só de jan/2017 a ago/2018: os meses antes e depois têm poucos pedidos e distorcem a série."),
    ("% atrasados (meses completos)",
     "VAR mes = SELECTEDVALUE ( 'Calendário'[Ano-mês] )\nRETURN IF ( mes >= 201701 && mes <= 201808, [% atrasados] )",
     "0.0%", "Entrega",
     "% de entregas atrasadas só de jan/2017 a ago/2018, pelo mesmo motivo."),
    ("Vendas (itens)", "SUM ( Itens[Preço] )", "\\R$ #,0", "Categorias e vendedores",
     "Soma do preço dos itens vendidos, sem frete."),
    ("Pedidos com o item", "DISTINCTCOUNT ( Itens[ID do pedido] )", "#,0", "Categorias e vendedores",
     "Pedidos que contêm ao menos um item da seleção."),
    ("% atrasados (itens)",
     'VAR entregues = CALCULATE ( DISTINCTCOUNT ( Itens[ID do pedido] ), Itens[Status] = "delivered" )\n'
     'VAR atrasados = CALCULATE ( DISTINCTCOUNT ( Itens[ID do pedido] ), Itens[Status] = "delivered", Itens[Atrasado] = TRUE () )\n'
     "RETURN DIVIDE ( atrasados, entregues )",
     "0.0%", "Categorias e vendedores", "Parcela dos pedidos entregues com itens da seleção que chegou atrasada."),
    ("Nota média (itens)",
     "AVERAGEX (\n    VALUES ( Itens[ID do pedido] ),\n    CALCULATE ( MAX ( Itens[Nota] ) )\n)", "0.00",
     "Categorias e vendedores", "Nota média por pedido que contém itens da seleção (cada pedido conta uma vez)."),
    ("% atrasados (100+ pedidos)",
     'VAR entregues = CALCULATE ( DISTINCTCOUNT ( Itens[ID do pedido] ), Itens[Status] = "delivered" )\n'
     "RETURN IF ( entregues >= 100, [% atrasados (itens)] )",
     "0.0%", "Categorias e vendedores",
     "% atrasados (itens) só onde há ao menos 100 pedidos entregues: com menos, a taxa é ruído."),
]  # fmt: skip

RELATIONSHIPS = [
    ("Pedidos", "Data da compra", "Calendário", "Data"),
    ("Pedidos", "ID do cliente", "Clientes", "ID do cliente"),
    ("Itens", "ID do pedido", "Pedidos", "ID do pedido"),
    ("Itens", "ID do produto", "Produtos", "ID do produto"),
    ("Itens", "ID do vendedor", "Vendedores", "ID do vendedor"),
]


def q(name: str) -> str:
    """Quote a TMDL object name when it needs it."""
    return name if name.replace("_", "").isalnum() and name.isascii() else "'" + name.replace("'", "''") + "'"


def dax_block(expr: str, indent: str) -> str:
    expr = expr.strip("\n")
    if "\n" not in expr:
        return " " + expr
    body = "\n".join(indent + "\t" + line for line in expr.split("\n"))
    return f" ```\n{body}\n{indent}\t```"


def props(extra: dict, indent: str) -> list[str]:
    out = []
    for k, v in extra.items():
        if v is True:
            out.append(f"{indent}{k}")
        elif k == "sortByColumn":
            out.append(f"{indent}{k}: {q(v)}")
        else:
            out.append(f"{indent}{k}: {v}")
    return out


def table_tmdl(table: str) -> str:
    source, columns = TABLES[table]
    lines = [f"table {q(table)}", f"\tlineageTag: {guid('t/' + table)}"]
    if table == "Calendário":
        lines.append("\tdataCategory: Time")
    lines.append("")
    for name, src, dtype, fmt, extra in columns:
        lines += [f"\tcolumn {q(name)}", f"\t\tdataType: {dtype}"]
        if fmt:
            lines.append(f"\t\tformatString: {fmt}")
        extra = dict(extra)
        summarize = extra.pop("summarizeBy", "none" if dtype in ("string", "dateTime", "boolean") else "sum")
        if src.endswith("_id") or "zip" in src:
            summarize = "none"
        lines.append(f"\t\tlineageTag: {guid('c/' + table + '/' + name)}")
        lines.append(f"\t\tsummarizeBy: {summarize}")
        lines.append(f"\t\tsourceColumn: {src}")
        lines += props(extra, "\t\t")
        lines += ["", "\t\tannotation SummarizationSetBy = User", ""]
    for name, dax, dtype, fmt, extra in CALC_COLUMNS.get(table, []):
        lines.append(f"\tcolumn {q(name)} ={dax_block(dax, chr(9))}")
        lines.append(f"\t\tdataType: {dtype}")
        if fmt:
            lines.append(f"\t\tformatString: {fmt}")
        extra = dict(extra)
        summarize = extra.pop("summarizeBy", "none")
        lines.append(f"\t\tlineageTag: {guid('cc/' + table + '/' + name)}")
        lines.append(f"\t\tsummarizeBy: {summarize}")
        lines += props(extra, "\t\t")
        lines += ["", "\t\tannotation SummarizationSetBy = User", ""]
    types = ", ".join(f'{{"{src}", {M_TYPES[dtype]}}}' for _, src, dtype, _, _ in columns)
    lines += [
        f"\tpartition {q(table)} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\t\tlet",
        "\t\t\t\t    Arquivo = if Text.StartsWith ( DataFolder, \"http\" )",
        f'\t\t\t\t        then Binary.Buffer ( Web.Contents ( DataFolder & "/{source}.parquet" ) )',
        f'\t\t\t\t        else File.Contents ( DataFolder & "\\{source}.parquet" ),',
        "\t\t\t\t    Fonte = Parquet.Document ( Arquivo ),",
        f"\t\t\t\t    Tipos = Table.TransformColumnTypes ( Fonte, {{{types}}} )",
        "\t\t\t\tin",
        "\t\t\t\t    Tipos",
        "",
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    return "\n".join(lines)


def measures_tmdl() -> str:
    lines = ["table Medidas", f"\tlineageTag: {guid('t/Medidas')}", ""]
    for name, dax, fmt, folder, desc in MEASURES:
        lines.append(f"\t/// {desc}")
        lines.append(f"\tmeasure {q(name)} ={dax_block(dax, chr(9))}")
        lines.append(f"\t\tformatString: {fmt}")
        lines.append(f"\t\tdisplayFolder: {folder}")
        lines.append(f"\t\tlineageTag: {guid('m/' + name)}")
        lines.append("")
    # A measure-only table still needs one hidden column and a partition.
    lines += [
        "\tcolumn Coluna",
        "\t\tdataType: string",
        "\t\tisHidden",
        f"\t\tlineageTag: {guid('c/Medidas/Coluna')}",
        "\t\tsummarizeBy: none",
        "\t\tsourceColumn: [Coluna]",
        "",
        "\t\tannotation SummarizationSetBy = Automatic",
        "",
        "\tpartition Medidas = calculated",
        "\t\tmode: import",
        '\t\tsource = ROW ( "Coluna", "" )',
        "",
        "\tannotation PBI_Id = medidas",
        "",
    ]
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, obj: dict) -> None:
    write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def platform(kind: str, display: str) -> dict:
    return {
        "$schema": f"{SCHEMA}/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind, "displayName": display},
        "config": {"version": "2.0", "logicalId": guid("platform/" + kind)},
    }


def build_model(root: Path) -> None:
    sm = root / f"{NAME}.SemanticModel"
    write_json(sm / ".platform", platform("SemanticModel", NAME))
    write_json(sm / "definition.pbism", {
        "$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {},
    })  # fmt: skip
    d = sm / "definition"
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
    all_tables = list(TABLES) + ["Medidas"]
    write(d / "model.tmdl", "\n".join([
        "model Model",
        "\tculture: pt-BR",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: pt-BR",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        "annotation PBI_QueryOrder = " + json.dumps(["DataFolder", *TABLES], ensure_ascii=False),
        "",
        *[f"ref table {q(t)}" for t in all_tables],
        "",
        "ref cultureInfo pt-BR",
        "",
    ]))  # fmt: skip
    write(d / "expressions.tmdl", "\n".join([
        "/// Pasta local ou endereço web com os arquivos Parquet de export_powerbi.py (data/powerbi).",
        f'expression DataFolder = "{DEFAULT_FOLDER}" meta [IsParameterQuery = true, Type = "Text", '
        "IsParameterQueryRequired = true]",
        f"\tlineageTag: {guid('e/DataFolder')}",
        "",
        "\tannotation PBI_ResultType = Text",
        "",
    ]))  # fmt: skip
    write(d / "cultures" / "pt-BR.tmdl", "cultureInfo pt-BR\n")
    for t in TABLES:
        write(d / "tables" / f"{t}.tmdl", table_tmdl(t))
    write(d / "tables" / "Medidas.tmdl", measures_tmdl())
    rel = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rel += [f"relationship {guid('r/' + ft + fc)}", f"\tfromColumn: {q(ft)}.{q(fc)}", f"\ttoColumn: {q(tt)}.{q(tc)}", ""]
    write(d / "relationships.tmdl", "\n".join(rel))


# ---------------------------------------------------------------- report

def lit(value) -> dict:
    if isinstance(value, bool):
        v = "true" if value else "false"
    elif isinstance(value, int):
        v = f"{value}L"
    elif isinstance(value, float):
        v = f"{value}D"
    else:
        v = "'" + str(value).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": v}}}


def color(hex_: str) -> dict:
    return {"solid": {"color": lit(hex_)}}


def field(kind: str, table: str, prop: str) -> dict:
    return {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}}


def proj(kind: str, table: str, prop: str, label: str | None = None) -> dict:
    p = {"field": field(kind, table, prop), "queryRef": f"{table}.{prop}", "nativeQueryRef": prop}
    if label:
        p["displayName"] = label
    return p


def M(prop: str, label: str | None = None) -> dict:
    return proj("Measure", "Medidas", prop, label)


def C(table: str, prop: str, label: str | None = None) -> dict:
    return proj("Column", table, prop, label)


def container(title: str | None, *, show_title: bool = True, bg: bool = True) -> dict:
    out = {
        "background": [{"properties": {"show": lit(bg), "color": color(CARD), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(False)}}],
        "dropShadow": [{"properties": {"show": lit(False)}}],
        "padding": [{"properties": {"top": lit(10.0), "bottom": lit(10.0), "left": lit(14.0), "right": lit(14.0)}}],
        "visualHeader": [{"properties": {"show": lit(False)}}],
    }
    if title and show_title:
        out["title"] = [{"properties": {
            "show": lit(True), "text": lit(title), "fontColor": color(INK), "fontSize": lit(12.0),
            "bold": lit(True), "fontFamily": lit("Segoe UI Semibold"),
        }}]  # fmt: skip
    else:
        out["title"] = [{"properties": {"show": lit(False)}}]
    return out


class Page:
    def __init__(self, key: str, display: str):
        self.key, self.display = key, display
        self.name = uid("page/" + key)
        self.visuals: list[dict] = []

    def add(self, key: str, x, y, w, h, visual: dict) -> None:
        self.visuals.append({
            "$schema": VISUAL_SCHEMA,
            "name": uid(f"visual/{self.key}/{key}"),
            "position": {"x": x, "y": y, "z": (len(self.visuals) + 1) * 1000, "height": h, "width": w,
                         "tabOrder": (len(self.visuals) + 1) * 1000},
            "visual": visual,
        })  # fmt: skip

    def text(self, key, x, y, w, h, runs: list[tuple[str, str, str, bool]]):
        """runs: (text, size, color, bold); a run ending with \\n starts a new paragraph."""
        paragraphs, current = [], []
        for text, size, col, bold in runs:
            style = {"fontSize": size, "color": col, "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI"}
            if bold:
                style["fontWeight"] = "bold"
            current.append({"value": text.rstrip("\n"), "textStyle": style})
            if text.endswith("\n"):
                paragraphs.append({"textRuns": current})
                current = []
        if current:
            paragraphs.append({"textRuns": current})
        self.add(key, x, y, w, h, {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
            "visualContainerObjects": container(None, bg=False),
            "drillFilterOtherVisuals": True,
        })  # fmt: skip

    def card(self, key, x, y, w, h, measure: str, label: str, value_color: str = INK, units: float = 0.0):
        """units: 0 = automatic (16 Mi), 1 = none (99.441)."""
        self.add(key, x, y, w, h, {
            "visualType": "card",
            "query": {"queryState": {"Values": {"projections": [M(measure, label)]}}},
            "objects": {
                "labels": [{"properties": {"color": color(value_color), "fontSize": lit(26.0),
                                           "fontFamily": lit("Segoe UI Semibold"), "labelDisplayUnits": lit(units)}}],
                "categoryLabels": [{"properties": {"show": lit(True), "color": color(MUTED), "fontSize": lit(10.0)}}],
            },
            "visualContainerObjects": container(None),
            "drillFilterOtherVisuals": True,
        })  # fmt: skip

    def slicer(self, key, x, y, w, h, table, column, title):
        self.add(key, x, y, w, h, {
            "visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [C(table, column)]}}},
            "objects": {
                "data": [{"properties": {"mode": lit("Dropdown")}}],
                "header": [{"properties": {"show": lit(True), "text": lit(title), "fontColor": color(MUTED),
                                           "textSize": lit(10.0)}}],
                "items": [{"properties": {"fontColor": color(INK), "textSize": lit(11.0)}}],
            },
            "visualContainerObjects": container(None),
            "syncGroup": {"groupName": f"{table}.{column}", "fieldChanges": True, "filterChanges": True},
            "drillFilterOtherVisuals": True,
        })  # fmt: skip

    def chart(self, key, x, y, w, h, vtype, title, roles: dict, sort=None, objects=None, filters=None):
        query = {"queryState": {role: {"projections": ps} for role, ps in roles.items()}}
        if sort:
            kind, table, prop, direction = sort
            query["sortDefinition"] = {"sort": [{"field": field(kind, table, prop), "direction": direction}],
                                       "isDefaultSort": False}  # fmt: skip
        self.add(key, x, y, w, h, {
            "visualType": vtype,
            "query": query,
            "objects": objects or {},
            "visualContainerObjects": container(title),
            "drillFilterOtherVisuals": True,
        })  # fmt: skip
        if filters:
            self.visuals[-1]["filterConfig"] = {"filters": filters}

    def json(self) -> dict:
        return {
            "$schema": PAGE_SCHEMA,
            "name": self.name,
            "displayName": self.display,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
            "objects": {"background": [{"properties": {"color": color(PAPER), "transparency": lit(0.0)}}]},
        }


def axis_objects(fill: str, line: str | None = None, labels: bool = True, legend: bool = False) -> dict:
    obj = {
        "dataPoint": [{"properties": {"fill": color(fill)}}],
        "categoryAxis": [{"properties": {"labelColor": color(MUTED), "fontSize": lit(9.0), "showAxisTitle": lit(False)}}],
        "valueAxis": [{"properties": {"show": lit(False), "gridlineShow": lit(False), "showAxisTitle": lit(False),
                                      "secShowAxisTitle": lit(False), "secLabelColor": color(MUTED)}}],
        "labels": [{"properties": {"show": lit(labels), "color": color(INK), "fontSize": lit(9.0),
                                   "labelOverflow": lit(True)}}],
        "legend": [{"properties": {"show": lit(legend), "position": lit("Top"), "labelColor": color(MUTED)}}],
    }
    if line:
        obj["lineStyles"] = [{"properties": {"strokeWidth": lit(3)}}]
    return obj


def build_pages(stats: dict) -> list[Page]:
    p1 = Page("overview", "Visão geral")
    p1.text("title", 24, 10, 820, 76, [
        ("Olist: vendas, entregas e satisfação\n", "20pt", INK, True),
        (stats["subtitle"] + "\n", "10pt", MUTED, False),
    ])
    p1.slicer("year", 880, 18, 180, 58, "Calendário", "Ano", "Ano")
    p1.slicer("state", 1076, 18, 180, 58, "Clientes", "Estado", "Estado do cliente")
    cards = [("Faturamento", "Faturamento", INK), ("Pedidos (qtd)", "Pedidos", INK),
             ("Ticket médio", "Ticket médio", INK), ("% atrasados", "Entregas atrasadas", AMBER),
             ("Nota média", "Nota média (1 a 5)", TEAL)]  # fmt: skip
    for i, (m, label, col) in enumerate(cards):
        p1.card(f"card{i}", 24 + i * 248, 92, 236, 96, m, label, col, units=1.0 if m == "Pedidos (qtd)" else 0.0)
    p1.chart("monthly", 24, 204, 812, 500, "lineClusteredColumnComboChart",
             "Faturamento por mês (colunas) e entregas atrasadas (linha)",
             {"Category": [C("Calendário", "Mês")], "Y": [M("Faturamento (meses completos)", "Faturamento")],
              "Y2": [M("% atrasados (meses completos)", "% atrasados")]},
             sort=("Column", "Calendário", "Mês", "Ascending"),
             objects={**axis_objects(NAVY, line=AMBER, labels=False, legend=True),
                      "dataPoint": [{"properties": {"fill": color(NAVY)}, "selector": {"metadata": "Medidas.Faturamento (meses completos)"}},
                                    {"properties": {"fill": color(AMBER)}, "selector": {"metadata": "Medidas.% atrasados (meses completos)"}}]})  # fmt: skip
    p1.chart("states", 848, 204, 408, 500, "clusteredBarChart", "Faturamento por estado do cliente",
             {"Category": [C("Clientes", "Estado")], "Y": [M("Faturamento")]},
             sort=("Measure", "Medidas", "Faturamento", "Descending"), objects=axis_objects(TEAL))

    p2 = Page("delay", "Atraso e nota")
    p2.text("title", 24, 10, 1232, 80, [
        (stats["headline"] + "\n", "20pt", INK, True),
        (stats["curve"] + "\n", "10pt", MUTED, False),
    ])
    p2.chart("curve", 24, 100, 812, 436, "lineClusteredColumnComboChart",
             "Nota média (colunas) e parcela de notas 1 (linha) por dias de atraso, pedidos entregues",
             {"Category": [C("Pedidos", "Faixa de atraso")], "Y": [M("Nota média (entregues)", "Nota média")],
              "Y2": [M("% nota 1 (entregues)", "% nota 1")]},
             sort=("Column", "Pedidos", "Faixa de atraso", "Ascending"),
             objects={**axis_objects(TEAL, line=AMBER, labels=True, legend=True),
                      "dataPoint": [{"properties": {"fill": color(TEAL)}, "selector": {"metadata": "Medidas.Nota média (entregues)"}},
                                    {"properties": {"fill": color(AMBER)}, "selector": {"metadata": "Medidas.% nota 1 (entregues)"}}]})  # fmt: skip
    small = [("Pedidos atrasados", "Pedidos atrasados", AMBER), ("% atrasados", "Entregas atrasadas", AMBER),
             ("Nota no prazo", "Nota no prazo", TEAL), ("Nota com atraso", "Nota com atraso", AMBER)]  # fmt: skip
    for i, (m, label, col) in enumerate(small):
        p2.card(f"card{i}", 848 + (i % 2) * 208, 100 + (i // 2) * 102, 200, 94, m, label, col)
    p2.chart("late_states", 848, 304, 408, 400, "clusteredBarChart", "Entregas atrasadas por estado do cliente",
             {"Category": [C("Clientes", "Estado")], "Y": [M("% atrasados")]},
             sort=("Measure", "Medidas", "% atrasados", "Descending"), objects=axis_objects(AMBER))
    p2.text("decision", 24, 548, 812, 156, [
        ("O que fazer com isso\n", "13pt", INK, True),
        (stats["decision"] + "\n", "11pt", INK, False),
        ("Correlação em dados observados: pedidos atrasados podem diferir em outros aspectos.\n", "9pt", MUTED, False),
    ])

    p3 = Page("categories", "Categorias e vendedores")
    p3.text("title", 24, 10, 1232, 76, [
        ("Onde vendemos e onde atrasamos\n", "20pt", INK, True),
        ("Vendas sem frete por categoria de produto, e atraso e nota medidos por pedido que contém o item.\n",
         "10pt", MUTED, False),
    ])
    # Light bars with dark labels at the bar end: the longest bar keeps its value (an outside label has
    # no room there and Power BI drops it), and labels that spill past a short bar stay readable.
    cats_objects = axis_objects("#9FB8D6")
    cats_objects["labels"][0]["properties"].update({"labelPosition": lit("InsideEnd"), "labelDensity": lit(100.0), "labelPrecision": lit(2)})
    cats_objects["categoryAxis"][0]["properties"]["maxMarginFactor"] = lit(45.0)
    p3.chart("cats", 24, 92, 520, 612, "clusteredBarChart", "Vendas por categoria",
             {"Category": [C("Produtos", "Categoria")], "Y": [M("Vendas (itens)")]},
             sort=("Measure", "Medidas", "Vendas (itens)", "Descending"), objects=cats_objects)
    p3.chart("table", 556, 92, 700, 330, "tableEx", "Categorias: vendas, atraso e nota",
             {"Values": [C("Produtos", "Categoria"), M("Vendas (itens)", "Vendas"),
                         M("Pedidos com o item", "Pedidos"), M("% atrasados (itens)", "Atrasados"),
                         M("Nota média (itens)", "Nota média")]},
             sort=("Measure", "Medidas", "Vendas (itens)", "Descending"),
             objects={"values": [{"properties": {"fontSize": lit(10.0)}}],
                      "columnHeaders": [{"properties": {"fontSize": lit(10.0), "fontColor": color(MUTED)}}]})  # fmt: skip
    # Seller states as bars: São Paulo has ~70k orders, which squeezed every other state into one corner
    # of a scatter. States with under 100 delivered orders (AM has 3) are left out.
    sellers_objects = axis_objects("#9CCFC9")
    sellers_objects["labels"][0]["properties"].update(
        {"labelPosition": lit("InsideEnd"), "labelDensity": lit(100.0), "labelPrecision": lit(1)})
    p3.chart("sellers", 556, 434, 700, 270, "clusteredBarChart",
             "Entregas atrasadas por estado do vendedor (estados com 100+ pedidos)",
             {"Category": [C("Vendedores", "Estado do vendedor")], "Y": [M("% atrasados (100+ pedidos)", "Atrasados")],
              "Tooltips": [M("Pedidos com o item", "Pedidos")]},
             sort=("Measure", "Medidas", "% atrasados (100+ pedidos)", "Descending"), objects=sellers_objects)
    return [p1, p2, p3]


def theme() -> dict:
    return {
        "name": "Olist",
        "dataColors": [NAVY, TEAL, AMBER, "#4C6A92", "#7FB8B1", "#D89A5B", "#9AA5B4"],
        "background": CARD,
        "foreground": INK,
        "tableAccent": TEAL,
        "textClasses": {
            "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 26, "color": INK},
            "title": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": INK},
            "header": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": INK},
            "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": MUTED},
        },
    }


def build_report(root: Path, stats: dict) -> None:
    rp = root / f"{NAME}.Report"
    write_json(rp / ".platform", platform("Report", NAME))
    write_json(rp / "definition.pbir", {
        "$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}},
    })  # fmt: skip
    base_dir = rp / "StaticResources" / "SharedResources" / "BaseThemes"
    base_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "BaseThemes" / "CY24SU10.json", base_dir / "CY24SU10.json")
    write_json(rp / "StaticResources" / "RegisteredResources" / "OlistTheme.json", theme())
    d = rp / "definition"
    write_json(d / "version.json", {"$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json",
                                    "version": "2.0.0"})  # fmt: skip
    write_json(d / "report.json", {
        "$schema": f"{SCHEMA}/item/report/definition/report/3.0.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": {"visual": "1.8.95", "report": "2.0.95",
                                                                         "page": "1.3.95"}, "type": "SharedResources"},
            "customTheme": {"name": "OlistTheme.json", "reportVersionAtImport": {"visual": "2.1.0", "report": "2.1.0",
                                                                                 "page": "2.0.0"},
                            "type": "RegisteredResources"},
        },
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "OlistTheme.json", "path": "OlistTheme.json", "type": "CustomTheme"}]},
        ],
        "objects": {"outspacePane": [{"properties": {"expanded": lit(False)}}]},
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    })  # fmt: skip
    pages = build_pages(stats)
    write_json(d / "pages" / "pages.json", {
        "$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p.name for p in pages], "activePageName": pages[0].name,
    })  # fmt: skip
    for p in pages:
        write_json(d / "pages" / p.name / "page.json", p.json())
        for v in p.visuals:
            write_json(d / "pages" / p.name / "visuals" / v["name"] / "visual.json", v)


def stats_from_data() -> dict:
    """Texts on the pages, computed from the exported data so they always match it."""
    import duckdb

    folder = (HERE.parent / "data" / "powerbi").as_posix()
    con = duckdb.connect()
    o = f"'{folder}/fct_orders.parquet'"
    n, first, last = con.execute(f"select count(*), min(purchase_date), max(purchase_date) from {o}").fetchone()
    late = con.execute(f"select avg(is_delayed::int) from {o} where status = 'delivered'").fetchone()[0]
    by_day = dict(con.execute(
        f"select least(greatest(delay_days, 0), 11), avg(review_score) from {o} "
        "where status = 'delivered' and delay_days is not null group by 1"
    ).fetchall())
    # The plateau is the average of orders 11 or more days late; the turn is the first day whose
    # average is within 0.15 of it (single days beyond that are a few hundred orders each, noisy).
    floor = by_day[11]
    turn = next(d for d in range(1, 12) if by_day[d] <= floor + 0.15)
    months = "jan fev mar abr mai jun jul ago set out nov dez".split()

    def br(x: float) -> str:
        return f"{x:.2f}".replace(".", ",")

    return {
        "subtitle": f"{n:,} pedidos de {months[first.month - 1]}/{first.year} a {months[last.month - 1]}/{last.year}"
        .replace(",", ".") + " · dados públicos da Olist, modelados em dbt",
        "headline": f"Cada dia de atraso derruba a nota, até o {turn}º dia",
        "curve": f"{late * 100:.1f}".replace(".", ",") + f"% das entregas chegam atrasadas. No prazo a nota média "
        f"é {br(by_day[0])}; com 1 dia de atraso, {br(by_day[1])}; com {turn} dias, {br(by_day[turn])}. "
        f"Depois disso fica perto de {br(floor)}.",
        "decision": f"O dinheiro de logística rende dentro da primeira semana de atraso: transformar um atraso de "
        f"3 dias em 1 dia recupera {br(by_day[1] - by_day[3])} ponto de nota; reduzir um atraso de 20 dias "
        "para 12 quase não muda nada. A prioridade são os pedidos que acabaram de passar do prazo.",
    }


def main() -> None:
    root = Path(os.environ.get("OLIST_PBI_OUT", HERE))
    for old in (root / f"{NAME}.SemanticModel", root / f"{NAME}.Report"):
        shutil.rmtree(old, ignore_errors=True)
    write_json(root / f"{NAME}.pbip", {
        "$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    })  # fmt: skip
    build_model(root)
    build_report(root, stats_from_data())
    print(f"wrote {root / (NAME + '.pbip')}")


if __name__ == "__main__":
    main()
