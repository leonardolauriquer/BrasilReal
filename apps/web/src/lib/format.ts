/** Shared number / period formatters for panel + map labels. */

let numberLocale = "pt-BR";

export function setFormatLocale(bcp47: string) {
  numberLocale = bcp47 || "pt-BR";
}

function loc() {
  return numberLocale;
}

const MONTHS: Record<string, string[]> = {
  "pt-BR": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  es: ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
};

function monthsFor() {
  return MONTHS[loc()] || MONTHS["pt-BR"];
}

export type FormatValueInput = {
  value: number;
  unit?: string | null;
};

type FormatOpts = {
  /** Compact map-friendly labels (R$ bi, mi hab, /100k). */
  compact?: boolean;
};

/** Variação de % vira pontos percentuais — não é a taxa do ano. */
export function deltaUnitFor(unit?: string | null): string {
  const u = (unit || "").trim();
  if (!u) return u;
  if (u === "%" || u.includes("%")) return "pp";
  return u;
}

export function formatPeriodLabel(period: string) {
  if (/^\d{4}-\d{2}$/.test(period)) {
    const month = Number(period.slice(5, 7));
    const label = monthsFor()[month - 1];
    return label ? `${label}/${period.slice(0, 4)}` : period;
  }
  if (/^\d{4}T[12]$/.test(period)) {
    const round = period.slice(5);
    if (loc().startsWith("en")) return `${period.slice(0, 4)} · round ${round}`;
    if (loc().startsWith("es")) return `${period.slice(0, 4)} · ${round}.ª vuelta`;
    return `${period.slice(0, 4)} · ${round}º turno`;
  }
  if (/^\d{6}$/.test(period)) {
    return `${period.slice(0, 4)} · T${Number(period.slice(4))}`;
  }
  return period;
}

export function comparePeriodKeys(a: string, b: string): number {
  return a.localeCompare(b, "en", { numeric: true });
}

/** Share of a total as pt-BR percent (e.g. 4,3%). */
/** Median of the displayed recorte — derived from the same official values, not a new source. */
export function medianNumbers(values: number[]): number | null {
  const nums = values.filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
  if (!nums.length) return null;
  const mid = Math.floor(nums.length / 2);
  return nums.length % 2 === 1 ? nums[mid] : (nums[mid - 1] + nums[mid]) / 2;
}

export function formatSharePercent(value: number, total: number, digits = 1) {
  if (!Number.isFinite(value) || !Number.isFinite(total) || total <= 0) return null;
  const pct = (value / total) * 100;
  return `${pct.toLocaleString(loc(), {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits > 0 ? Math.min(digits, 1) : 0,
  })}%`;
}

export function formatValue(
  obs: FormatValueInput,
  opts: FormatOpts = {},
): string {
  const { value, unit } = obs;
  const compact = Boolean(opts.compact);

  if (!Number.isFinite(value)) return "—";

  if (unit === "BRL") {
    if (compact) {
      const abs = Math.abs(value);
      if (abs >= 1e12) {
        return `R$ ${(value / 1e12).toLocaleString(loc(), { maximumFractionDigits: 1 })} tri`;
      }
      if (abs >= 1e9) {
        return `R$ ${(value / 1e9).toLocaleString(loc(), { maximumFractionDigits: 1 })} bi`;
      }
      if (abs >= 1e6) {
        return `R$ ${(value / 1e6).toLocaleString(loc(), { maximumFractionDigits: 0 })} mi`;
      }
      return `R$ ${value.toLocaleString(loc(), { maximumFractionDigits: 0 })}`;
    }
    return new Intl.NumberFormat(loc(), {
      style: "currency",
      currency: "BRL",
      maximumFractionDigits: 0,
    }).format(value);
  }

  if (unit === "%" || unit === "hab/km²") {
    if (compact && unit === "%") {
      return `${value.toLocaleString(loc(), { maximumFractionDigits: 1 })}%`;
    }
    return `${new Intl.NumberFormat(loc(), {
      maximumFractionDigits: unit === "%" ? 2 : 1,
    }).format(value)}${unit === "%" ? "%" : ` ${unit}`}`;
  }

  if (unit === "por 100 mil hab") {
    if (compact) {
      return `${value.toLocaleString(loc(), { maximumFractionDigits: 1 })}/100k`;
    }
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} /100 mil`;
  }

  if (unit === "por mil hab") {
    if (compact) {
      return `${value.toLocaleString(loc(), { maximumFractionDigits: 1 })}/mil`;
    }
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} /mil hab`;
  }

  if (unit === "por 100 jovens") {
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} /100 jovens`;
  }

  if (unit === "por 100 adultos") {
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} /100 adultos`;
  }

  if (unit === "homens/100 mulheres") {
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} homens/100 mulh.`;
  }

  if (unit === "salários mínimos") {
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} SM`;
  }

  if (unit === "empresas" || unit === "unidades locais") {
    if (compact && Math.abs(value) >= 1e6) {
      return `${(value / 1e6).toLocaleString(loc(), { maximumFractionDigits: 1 })} mi emp.`;
    }
    if (compact && Math.abs(value) >= 1e3) {
      return `${(value / 1e3).toLocaleString(loc(), { maximumFractionDigits: 0 })} mil emp.`;
    }
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 0 }).format(value)} emp.`;
  }

  if (unit === "anos") {
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} anos`;
  }

  if (unit === "pp") {
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} pp`;
  }

  if (unit === "USD") {
    const abs = Math.abs(value);
    if (abs >= 1e9) {
      return `US$ ${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value / 1e9)} bi`;
    }
    if (abs >= 1e6) {
      return `US$ ${new Intl.NumberFormat(loc(), { maximumFractionDigits: 0 }).format(value / 1e6)} mi`;
    }
    return `US$ ${new Intl.NumberFormat(loc(), { maximumFractionDigits: 0 }).format(value)}`;
  }

  if (unit && unit.toLowerCase().includes("nota")) {
    return `${value.toLocaleString(loc(), {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })}`;
  }

  if (unit === "índice") {
    return value.toLocaleString(loc(), {
      minimumFractionDigits: 3,
      maximumFractionDigits: 3,
    });
  }

  if (unit === "BRL/mês") {
    if (compact) {
      return `R$ ${value.toLocaleString(loc(), { maximumFractionDigits: 0 })}/mês`;
    }
    return `${new Intl.NumberFormat(loc(), {
      style: "currency",
      currency: "BRL",
      maximumFractionDigits: 0,
    }).format(value)}/mês`;
  }

  if (unit === "USD/hab") {
    const abs = Math.abs(value);
    if (compact) {
      if (abs >= 1e3) {
        return `US$ ${(value / 1e3).toLocaleString(loc(), { maximumFractionDigits: 1 })} mil/hab`;
      }
      return `US$ ${value.toLocaleString(loc(), { maximumFractionDigits: 0 })}/hab`;
    }
    return `US$ ${new Intl.NumberFormat(loc(), { maximumFractionDigits: 0 }).format(value)}/hab`;
  }

  if (unit === "DCL/RCL") {
    return new Intl.NumberFormat(loc(), {
      maximumFractionDigits: 2,
      minimumFractionDigits: 2,
    }).format(value);
  }

  if (unit === "% da RCL") {
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)}% da RCL`;
  }

  if (unit === "BRL/hab") {
    const abs = Math.abs(value);
    if (compact) {
      if (abs >= 1e6) {
        return `R$ ${(value / 1e6).toLocaleString(loc(), { maximumFractionDigits: 1 })} mi/hab`;
      }
      if (abs >= 1e3) {
        return `R$ ${(value / 1e3).toLocaleString(loc(), { maximumFractionDigits: 1 })} mil`;
      }
      return `R$ ${value.toLocaleString(loc(), { maximumFractionDigits: 0 })}`;
    }
    return `${new Intl.NumberFormat(loc(), {
      style: "currency",
      currency: "BRL",
      maximumFractionDigits: 0,
    }).format(value)}/hab`;
  }

  if (unit === "km²") {
    if (compact && Math.abs(value) >= 1e6) {
      return `${(value / 1e6).toLocaleString(loc(), { maximumFractionDigits: 1 })} mi km²`;
    }
    return `${new Intl.NumberFormat(loc(), { maximumFractionDigits: 1 }).format(value)} km²`;
  }

  if (compact && unit === "homicídios") {
    if (Math.abs(value) >= 1e3) {
      return `${(value / 1e3).toLocaleString(loc(), { maximumFractionDigits: 1 })} mil`;
    }
  }

  if (compact && (unit === "habitantes" || unit === "pessoas")) {
    if (Math.abs(value) >= 1e6) {
      return `${(value / 1e6).toLocaleString(loc(), { maximumFractionDigits: 1 })} mi`;
    }
    if (Math.abs(value) >= 1e3) {
      return `${(value / 1e3).toLocaleString(loc(), { maximumFractionDigits: 0 })} mil`;
    }
  }

  if (compact) {
    return value.toLocaleString(loc(), { maximumFractionDigits: 1 });
  }

  return new Intl.NumberFormat(loc()).format(value);
}

/** Alias kept for map call sites / readability. */
export function formatMapLabel(value: number, unit?: string): string {
  return formatValue({ value, unit }, { compact: true });
}
