"use client";

type Props = {
  title: string;
  disclaimer: string;
  onExit: () => void;
};

export function SimuladoBanner({ title, disclaimer, onExit }: Props) {
  return (
    <div className="sim-banner" role="status">
      <div>
        <p className="sim-kicker">SIMULADO — não é fato observado</p>
        <p className="sim-title">{title || "Fundo federal hipotético"}</p>
        <p className="sim-text">{disclaimer}</p>
      </div>
      <button type="button" onClick={onExit}>
        Voltar ao observado
      </button>
    </div>
  );
}
