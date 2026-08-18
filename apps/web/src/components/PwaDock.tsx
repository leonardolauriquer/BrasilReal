"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BrandMark } from "@/components/BrandMark";
import {
  canInstallApp,
  isIosSafari,
  isStandaloneDisplay,
  readDismissedAt,
  shouldOfferInstall,
  writeDismissedAt,
  type BeforeInstallPromptEvent,
} from "@/lib/pwa";

type Mode = "hidden" | "install" | "ios" | "update";

type Props = {
  ready: boolean;
  onOfferInstall?: (offer: boolean) => void;
};

export function PwaDock({ ready, onOfferInstall }: Props) {
  const deferred = useRef<BeforeInstallPromptEvent | null>(null);
  const autoShown = useRef(false);
  const [mode, setMode] = useState<Mode>("hidden");
  const [canPrompt, setCanPrompt] = useState(false);

  const computeOffer = useCallback(() => {
    return shouldOfferInstall({
      standalone: isStandaloneDisplay(),
      canPrompt: Boolean(deferred.current),
      iosSafari: isIosSafari(),
      dismissedAt: readDismissedAt(window.localStorage),
      now: Date.now(),
    });
  }, []);

  const publishOffer = useCallback(() => {
    const offer = computeOffer();
    onOfferInstall?.(
      canInstallApp({
        standalone: isStandaloneDisplay(),
        canPrompt: Boolean(deferred.current),
        iosSafari: isIosSafari(),
      }),
    );
    return offer;
  }, [computeOffer, onOfferInstall]);

  useEffect(() => {
    const onBip = (event: Event) => {
      event.preventDefault();
      deferred.current = event as BeforeInstallPromptEvent;
      setCanPrompt(true);
    };
    const onInstalled = () => {
      deferred.current = null;
      setCanPrompt(false);
      writeDismissedAt(window.localStorage, Date.now());
      setMode("hidden");
      onOfferInstall?.(false);
    };
    const onAsk = () => {
      if (
        !canInstallApp({
          standalone: isStandaloneDisplay(),
          canPrompt: Boolean(deferred.current),
          iosSafari: isIosSafari(),
        })
      ) {
        return;
      }
      setMode(isIosSafari() && !deferred.current ? "ios" : "install");
    };
    window.addEventListener("beforeinstallprompt", onBip);
    window.addEventListener("appinstalled", onInstalled);
    window.addEventListener("br:pwa-install", onAsk as EventListener);
    document.documentElement.classList.toggle("is-pwa", isStandaloneDisplay());
    return () => {
      window.removeEventListener("beforeinstallprompt", onBip);
      window.removeEventListener("appinstalled", onInstalled);
      window.removeEventListener("br:pwa-install", onAsk as EventListener);
    };
  }, [computeOffer, onOfferInstall]);

  useEffect(() => {
    publishOffer();
  }, [canPrompt, publishOffer]);

  useEffect(() => {
    if (!ready || autoShown.current) return;
    if (!computeOffer()) return;
    const timer = window.setTimeout(() => {
      if (autoShown.current || !publishOffer()) return;
      autoShown.current = true;
      setMode(isIosSafari() && !deferred.current ? "ios" : "install");
    }, 1800);
    return () => window.clearTimeout(timer);
  }, [ready, canPrompt, computeOffer, publishOffer]);

  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;
    if (process.env.NODE_ENV !== "production") return;

    const hadController = Boolean(navigator.serviceWorker.controller);
    let skipEcho = sessionStorage.getItem("br-pwa-reloaded") === "1";
    if (skipEcho) sessionStorage.removeItem("br-pwa-reloaded");
    const echoTimer = window.setTimeout(() => {
      skipEcho = false;
    }, 4000);
    let registration: ServiceWorkerRegistration | null = null;
    let reloading = false;

    const reloadOnce = () => {
      if (!hadController || skipEcho || reloading) return;
      reloading = true;
      sessionStorage.setItem("br-pwa-reloaded", "1");
      window.location.reload();
    };

    const onMessage = (event: MessageEvent) => {
      if (event.data?.type !== "BR_UPDATED") return;
      reloadOnce();
    };

    const onControllerChange = () => reloadOnce();

    navigator.serviceWorker.addEventListener("message", onMessage);
    navigator.serviceWorker.addEventListener("controllerchange", onControllerChange);
    navigator.serviceWorker
      .register("/sw.js", { updateViaCache: "none" })
      .then((reg) => {
        registration = reg;
        void reg.update();
      })
      .catch(() => undefined);

    const poke = () => void registration?.update();
    const onVis = () => {
      if (document.visibilityState === "visible") poke();
    };
    window.addEventListener("focus", poke);
    document.addEventListener("visibilitychange", onVis);
    const interval = window.setInterval(poke, 15 * 60 * 1000);

    return () => {
      navigator.serviceWorker.removeEventListener("message", onMessage);
      navigator.serviceWorker.removeEventListener("controllerchange", onControllerChange);
      window.removeEventListener("focus", poke);
      document.removeEventListener("visibilitychange", onVis);
      window.clearInterval(interval);
      window.clearTimeout(echoTimer);
    };
  }, []);

  const dismissInstall = () => {
    writeDismissedAt(window.localStorage, Date.now());
    setMode("hidden");
    onOfferInstall?.(
      canInstallApp({
        standalone: isStandaloneDisplay(),
        canPrompt: Boolean(deferred.current),
        iosSafari: isIosSafari(),
      }),
    );
  };

  const installNow = async () => {
    const event = deferred.current;
    if (!event) {
      setMode(isIosSafari() ? "ios" : "hidden");
      return;
    }
    await event.prompt();
    const choice = await event.userChoice;
    deferred.current = null;
    setCanPrompt(false);
    if (choice.outcome === "accepted") {
      onOfferInstall?.(false);
      setMode("hidden");
    } else {
      dismissInstall();
    }
  };

  if (mode === "hidden") return null;
  if (isStandaloneDisplay() && mode !== "update") return null;
  if (!ready && mode !== "update") return null;

  if (mode === "update") {
    return (
      <aside className="pwa-dock pwa-dock--update" role="status">
        <BrandMark className="pwa-dock-mark" />
        <div className="pwa-dock-copy">
          <p className="pwa-dock-kicker">Versão nova no ar</p>
          <p className="pwa-dock-title">O atlas atualizou</p>
          <p className="pwa-dock-line">
            Camadas, correções e o texto do produto. Recarregar puxa o pacote publicado agora —
            os números oficiais continuam vindo da API, sem cache velho.
          </p>
        </div>
        <div className="pwa-dock-actions">
          <button type="button" className="pwa-dock-primary" onClick={() => window.location.reload()}>
            Atualizar
          </button>
          <button type="button" className="pwa-dock-ghost" onClick={() => setMode("hidden")}>
            Depois
          </button>
        </div>
      </aside>
    );
  }

  const iosCopy = mode === "ios";

  return (
    <aside className="pwa-dock" role="dialog" aria-labelledby="pwa-install-title">
      <BrandMark className="pwa-dock-mark" />
      <div className="pwa-dock-copy">
        <p className="pwa-dock-kicker">{iosCopy ? "Na tela inicial" : "App na tela inicial"}</p>
        <h2 id="pwa-install-title" className="pwa-dock-title">
          {iosCopy ? "Levar o Brasil Real com você" : "Quer o mapa como aplicativo?"}
        </h2>
        <p className="pwa-dock-line">
          {iosCopy ? (
            <>
              No Safari, toque em <strong>Compartilhar</strong> e depois em{" "}
              <strong>Adicionar à Tela de Início</strong>. Sem App Store. Sempre a versão
              publicada — dados só com fonte.
            </>
          ) : (
            <>
              Abre em tela cheia, sem loja e sem conta. Cada publicação substitui o pacote
              antigo — o que você vê é a versão no ar, com números oficiais ao vivo.
            </>
          )}
        </p>
      </div>
      <div className="pwa-dock-actions">
        {iosCopy ? (
          <button type="button" className="pwa-dock-primary" onClick={dismissInstall}>
            Entendi
          </button>
        ) : (
          <button type="button" className="pwa-dock-primary" onClick={() => void installNow()}>
            Instalar
          </button>
        )}
        <button type="button" className="pwa-dock-ghost" onClick={dismissInstall}>
          Agora não
        </button>
      </div>
    </aside>
  );
}
