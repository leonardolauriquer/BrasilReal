import type { Indicator } from "@/lib/api";

export type RankingPresetGroup = {
  key: string;
  label: string;
  items: Array<{ value: string; label: string }>;
};

/** Shortcuts + two editorial lenses (DERIVADO). Isolated metrics are not «melhor estado». */
const RANKING_PRESET_GROUPS: RankingPresetGroup[] = [
  {
    key: "lentes",
    label: "Lentes (pesos declarados)",
    items: [
      { value: "lens_live", label: "Melhor para morar" },
      { value: "lens_venture", label: "Melhor para empreender" },
      { value: "lens_family", label: "Melhor para criança" },
      { value: "lens_aging", label: "Pressão etária" },
    ],
  },
  {
    key: "economia",
    label: "Economia",
    items: [
      { value: "pib_per_capita", label: "PIB per capita" },
      { value: "household_income_pc", label: "Renda domiciliar per capita" },
      { value: "labor_income", label: "Renda do trabalho" },
      { value: "cempre_avg_wage", label: "Salário formal médio" },
      { value: "cempre_wage_in_sm", label: "Salário formal em SM" },
      { value: "cempre_firms", label: "Empresas formais" },
      { value: "employer_unit_birth_rate", label: "Taxa de abertura (empregadoras)" },
      { value: "employer_unit_births", label: "Aberturas (empregadoras)" },
      { value: "employer_survival_1y", label: "Sobrevivência 1 ano" },
      { value: "gini_household", label: "Gini (desigualdade)" },
      { value: "poverty_rate", label: "Pobreza" },
      { value: "unemployment_rate", label: "Desocupação" },
      { value: "informality_rate", label: "Informalidade" },
      { value: "pib", label: "PIB total" },
    ],
  },
  {
    key: "fiscal",
    label: "Fiscal (SICONFI)",
    items: [
      { value: "rcl_rreo", label: "RCL" },
      { value: "rcl_pc", label: "RCL por habitante" },
      { value: "receita_tributaria_rreo", label: "Receita tributária" },
      { value: "trib_share_rcl", label: "Tributária / RCL" },
      { value: "transf_uniao_rreo", label: "Transferências da União" },
      { value: "despesa_empenhada_rreo", label: "Despesa empenhada" },
      { value: "dcl_rreo", label: "Dívida líquida (DCL)" },
      { value: "dcl_rcl", label: "DCL / RCL" },
    ],
  },
  {
    key: "custo",
    label: "Custo na capital",
    items: [
      { value: "basket_capital", label: "Cesta básica (capital)" },
      { value: "basket_share_sm", label: "Cesta / SM líquido (capital)" },
    ],
  },
  {
    key: "moradia",
    label: "Moradia (Censo 2022)",
    items: [
      { value: "rented_share", label: "Domicílios alugados" },
      { value: "owned_paying_share", label: "Próprio ainda pagando" },
      { value: "owned_paid_share", label: "Próprio já pago" },
    ],
  },
  {
    key: "territorio",
    label: "Território",
    items: [
      { value: "population", label: "População" },
      { value: "population_density", label: "Densidade" },
      { value: "area_km2", label: "Área" },
      { value: "share_0_14", label: "0–14 anos" },
      { value: "share_60_plus", label: "60 anos ou mais" },
      { value: "median_age", label: "Idade mediana" },
      { value: "aging_index", label: "Índice de envelhecimento" },
      { value: "crude_birth_rate", label: "Natalidade bruta" },
      { value: "crude_death_rate", label: "Mortalidade bruta" },
      { value: "urban_share", label: "População urbana" },
      { value: "sex_ratio", label: "Razão de sexo" },
      { value: "dependency_ratio", label: "Dependência etária" },
    ],
  },
  {
    key: "geracoes",
    label: "Gerações (Censo 2022)",
    items: [
      { value: "share_gen_alpha", label: "Alpha (0–9 anos)" },
      { value: "share_gen_z", label: "Geração Z (10–24)" },
      { value: "share_gen_y", label: "Millennials (25–39)" },
      { value: "share_gen_x", label: "Geração X (40–59)" },
      { value: "share_gen_boomer", label: "Boomers (60–79)" },
      { value: "share_gen_silent", label: "80 anos ou mais" },
    ],
  },
  {
    key: "social",
    label: "Social / saneamento",
    items: [
      { value: "sanitation_adequate", label: "Esgoto adequado" },
      { value: "water_network_share", label: "Água da rede" },
      { value: "waste_collected_share", label: "Lixo coletado" },
      { value: "internet_home_share", label: "Internet no domicílio" },
      { value: "literacy_rate", label: "Alfabetização" },
      { value: "ideb_ai", label: "IDEB anos iniciais" },
      { value: "higher_education_share", label: "Superior completo" },
    ],
  },
  {
    key: "saude",
    label: "Saúde (PNS 2019 / censo)",
    items: [
      { value: "pns_hypertension", label: "Hipertensão (PNS 2019)" },
      { value: "pns_diabetes", label: "Diabetes (PNS 2019)" },
      { value: "pns_tobacco_smokers", label: "Fumantes (PNS 2019)" },
      { value: "pns_alcohol", label: "Álcool mensal (PNS 2019)" },
      { value: "pns_health_plan", label: "Plano de saúde (PNS 2019)" },
    ],
  },
  {
    key: "seguranca",
    label: "Segurança",
    items: [
      { value: "homicide_rate", label: "Homicídios /100 mil" },
      { value: "traffic_death_rate", label: "Mortos no trânsito /100 mil" },
      { value: "pns_violence", label: "Violência 12 meses (PNS 2019)" },
    ],
  },
  {
    key: "agro",
    label: "Exportações (FOB)",
    items: [
      { value: "export_fob", label: "Exportação total FOB" },
      { value: "export_fob_pc", label: "Exportação / hab." },
      { value: "export_soy_fob", label: "Soja em grão" },
      { value: "export_soy_oil_fob", label: "Óleo de soja" },
      { value: "export_soy_meal_fob", label: "Farelo de soja" },
      { value: "export_corn_fob", label: "Milho" },
      { value: "export_meat_fob", label: "Carnes" },
      { value: "export_bovine_fob", label: "Bovina" },
      { value: "export_iron_ore_fob", label: "Minérios (SH 26)" },
      { value: "export_petroleum_fob", label: "Combustíveis (SH 27)" },
    ],
  },
  {
    key: "eleicoes",
    label: "Eleições",
    items: [
      { value: "pres_winner_share", label: "Presidente — % vencedor" },
      { value: "pres_margin_pp", label: "Presidente — margem" },
      { value: "gov_winner_share", label: "Governador — % vencedor" },
      { value: "gov_margin_pp", label: "Governador — margem" },
    ],
  },
  {
    key: "povos",
    label: "Povos",
    items: [
      { value: "indigenous_share", label: "% indígena" },
      { value: "indigenous_population", label: "Pessoas indígenas" },
      { value: "quilombola_residents", label: "Quilombolas" },
      { value: "race_parda_share", label: "Parda (Censo)" },
      { value: "race_branca_share", label: "Branca (Censo)" },
      { value: "race_preta_share", label: "Preta (Censo)" },
    ],
  },
];

export function rankingPresetsFor(indicators: Indicator[]): RankingPresetGroup[] {
  const ids = new Set(indicators.map((i) => i.id));
  return RANKING_PRESET_GROUPS.map((g) => ({
    ...g,
    items: g.items.filter((i) => ids.has(i.value)),
  })).filter((g) => g.items.length > 0);
}

export const RANKING_PRESET_TIP = {
  definition:
    "O ranking à esquerda ordena as 27 UFs da camada escolhida. As lentes são receitas editoriais do Brasil Real (DERIVADO, pesos iguais, anos mistos). O resto são métricas isoladas da fonte — não um «melhor estado» oficial.",
  source: {
    organization: "Brasil Real",
    dataset: "Leituras = troca de camada, ou lente declarada",
  },
  reference_period: "rótulo da camada",
  status_label: "DERIVADO nas lentes; OBSERVADO/ESTIMADO nas métricas",
  limitations: [
    "Trocar um peso muda o 1º lugar das lentes — abra as camadas oficiais uma a uma.",
    "A cesta DIEESE não entra nas lentes: é preço da capital, não da UF.",
  ],
};

export const RECORTE_TIP = {
  definition:
    "Filtra o ranking (e o mapa) para um subconjunto de UFs. Macrorregiões = recorte IBGE N/NE/CO/SE/S. Litoral = UF com município na lista costeira/marinha do IBGE. Fronteira = estados com limite terrestre internacional.",
  source: {
    organization: "Brasil Real",
    dataset: "Recorte geográfico sobre camadas oficiais",
  },
  reference_period: "o da camada",
  status_label: "OBSERVADO",
  limitations: [
    "Não cria um indicador novo. UFs de fora do recorte ficam sem cor no mapa.",
    "Litoral ≠ custo de vida na praia. Fronteira ≠ comércio exterior.",
  ],
};

export const VARIATION_TIP = {
  definition:
    "Nível = valor oficial do período selecionado. Variação = esse valor menos o período oficial imediatamente anterior da mesma camada (delta local). Em porcentagens o delta entra como pontos percentuais.",
  source: {
    organization: "Brasil Real",
    dataset: "Delta entre dois períodos oficiais da mesma série",
  },
  reference_period: "atual vs anterior",
  status_label: "DERIVADO",
  limitations: [
    "A fonte não publica este ranking de variação.",
    "Nominal; não deflaciona BRL nem USD.",
    "Indisponível no primeiro período da série.",
  ],
};

export function legendScaleFor(
  indicator: Indicator | null,
  higherIsWorse: boolean,
): { low: string; high: string; note: string } {
  const unit = indicator?.unit;
  const id = indicator?.id;
  if (id === "lens_aging") {
    return {
      low: "menor pressão etária",
      high: "maior pressão etária",
      note: "lente DERIVADO · 60+, envelhecimento e dependência · não é qualidade de vida do idoso",
    };
  }
  if (
    id === "lens_live" ||
    id === "lens_venture" ||
    id === "lens_family" ||
    (typeof unit === "string" && unit.includes("nota"))
  ) {
    return {
      low: "mais baixa na lente",
      high: "mais alta na lente",
      note: "receita editorial 0–100 · DERIVADO · não é IDHM nem ranking oficial",
    };
  }
  if (id === "basket_capital") {
    return {
      low: "mais barata na capital",
      high: "mais cara na capital",
      note: "cesta DIEESE/Conab na CAPITAL — não é o interior da UF",
    };
  }
  if (id === "basket_share_sm") {
    return {
      low: "menor fatia do SM",
      high: "maior fatia do SM",
      note: "% do salário mínimo líquido na CAPITAL · não somar",
    };
  }
  if (unit === "índice") {
    return {
      low: "menor Gini",
      high: "maior Gini",
      note: "0 = igualdade · 1 = máxima desigualdade · não somar",
    };
  }
  if (unit === "BRL/mês") {
    return {
      low: "menor valor",
      high: "maior valor",
      note: "média mensal · não somar entre UFs",
    };
  }
  if (unit === "unidades locais") {
    return {
      low: "menos aberturas",
      high: "mais aberturas",
      note: "nascimentos de UL empregadoras · exclusive MEI · não é taxa",
    };
  }
  if (unit === "anos") {
    return {
      low: "mais jovem",
      high: "mais velha",
      note: "idade mediana censitária · não somar",
    };
  }
  if (unit === "por 100 jovens") {
    return {
      low: "menos envelhecida",
      high: "mais envelhecida",
      note: "65+ por 100 pessoas de 0–14 · Censo 2022",
    };
  }
  if (unit === "por mil hab") {
    return {
      low: "menor taxa",
      high: "maior taxa",
      note: "taxa bruta por mil habitantes · não padroniza idade",
    };
  }
  if (unit === "por 100 adultos") {
    return {
      low: "menos dependentes",
      high: "mais dependentes",
      note: "0–14 + 60+ por 100 pessoas de 15–59 · DERIVADO",
    };
  }
  if (unit === "homens/100 mulheres") {
    return {
      low: "mais mulheres",
      high: "mais homens",
      note: "homens por 100 mulheres · Censo 2022",
    };
  }
  if (unit === "salários mínimos") {
    return {
      low: "menos SM",
      high: "mais SM",
      note: "média formal CEMPRE em mínimos do ano · não é o piso legal da UF",
    };
  }
  if (unit === "empresas") {
    return {
      low: "menos empresas",
      high: "mais empresas",
      note: "estoque formal (CNPJ) · escuro = maior · exclusive MEI",
    };
  }
  if (unit === "DCL/RCL") {
    return {
      low: "menor dívida relativa",
      high: "maior dívida relativa",
      note: "DCL ÷ RCL do mesmo exercício RREO · pode ser negativa · não somar",
    };
  }
  if (unit === "% da RCL") {
    return {
      low: "menor autonomia tributária",
      high: "maior autonomia tributária",
      note: "receita tributária ÷ RCL · não é qualidade da gestão",
    };
  }
  if (unit === "USD/hab") {
    return {
      low: "menor FOB/hab",
      high: "maior FOB/hab",
      note: "exportação FOB ÷ população 2025 · não é exportação total",
    };
  }
  if (id === "ideb_ai") {
    return {
      low: "menor IDEB",
      high: "maior IDEB",
      note: "0 a 10 · rede total da UF · INEP · não é alfabetização",
    };
  }
  if (higherIsWorse) {
    return { low: "menor %", high: "maior %", note: "escala relativa entre UFs no período" };
  }
  if (unit === "pp") {
    return {
      low: "menor margem",
      high: "maior margem",
      note: "pontos percentuais entre 1º e 2º na UF",
    };
  }
  if (unit === "BRL") {
    return {
      low: "menor R$",
      high: "maior R$",
      note: "absoluto + % do recorte no rótulo · escuro = maior",
    };
  }
  if (unit === "habitantes") {
    return {
      low: "menos gente",
      high: "mais gente",
      note: "estimativa + % do Brasil no rótulo de cada UF",
    };
  }
  if (unit === "USD") {
    return {
      low: "menor FOB",
      high: "maior FOB",
      note: "absoluto + % do total no rótulo · escuro = maior valor",
    };
  }
  if (unit === "por 100 mil hab") {
    return {
      low: "menor taxa",
      high: "maior taxa",
      note: "por 100 mil habitantes · quanto maior, pior",
    };
  }
  if (unit === "homicídios") {
    return {
      low: "menos casos",
      high: "mais casos",
      note: "contagem absoluta · compare UFs pela taxa",
    };
  }
  if (unit === "BRL/hab") {
    return {
      low: id === "rcl_pc" ? "menor RCL/hab" : "menor PIB/hab",
      high: id === "rcl_pc" ? "maior RCL/hab" : "maior PIB/hab",
      note: "razão derivada · não somar entre UFs",
    };
  }
  if (unit === "km²") {
    return {
      low: "menor área",
      high: "maior área",
      note: "área 2010 + % do Brasil no rótulo · escuro = maior",
    };
  }
  if (unit === "hab/km²") {
    return {
      low: "menos densa",
      high: "mais densa",
      note: "população recente ÷ área 2010 · não somar",
    };
  }
  if (unit === "pessoas") {
    return {
      low: "menos pessoas",
      high: "mais pessoas",
      note: "contagem censitária + % do recorte no rótulo",
    };
  }
  return { low: "menor", high: "maior", note: "escala relativa entre UFs no período" };
}

export function groupIndicators(indicators: Indicator[]) {
  const order = [
    "lentes",
    "economia",
    "custo",
    "moradia",
    "fiscal",
    "territorio",
    "demografia",
    "social",
    "povos",
    "agro",
    "seguranca",
    "saude",
    "eleicoes",
    "justica",
  ];
  const map = new Map<string, { label: string; items: Indicator[] }>();
  for (const ind of indicators) {
    // Party share layers stay in the API; the Camada menu keeps winner + margin.
    if (ind.id.startsWith("pres_party_")) continue;
    const key = ind.group || "outros";
    const label = ind.group_label || key;
    if (!map.has(key)) map.set(key, { label, items: [] });
    map.get(key)!.items.push(ind);
  }
  const ranked = [...map.entries()].sort(([a], [b]) => {
    const ia = order.indexOf(a);
    const ib = order.indexOf(b);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });
  return ranked.map(([key, g]) => ({ key, ...g }));
}
