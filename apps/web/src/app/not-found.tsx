import Link from "next/link";
import { BrandMark } from "@/components/BrandMark";

export default function NotFound() {
  return (
    <main className="nf">
      <div className="nf-atmosphere" aria-hidden="true">
        <div className="boot-glow boot-glow-a" />
        <div className="boot-glow boot-glow-b" />
      </div>
      <div className="nf-core">
        <BrandMark className="nf-mark" />
        <p className="boot-kicker">Atlas exploratório</p>
        <h1 className="nf-title">Página não encontrada</h1>
        <p className="nf-line">
          Esse endereço não existe no Brasil Real. O mapa, com fonte em cada número, está na raiz.
        </p>
        <Link className="nf-home" href="/">
          Abrir o mapa
        </Link>
      </div>
    </main>
  );
}
