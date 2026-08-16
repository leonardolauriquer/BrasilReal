declare module "maplibre-gl" {
  namespace maplibregl {
    class LngLatBounds {
      extend(coord: [number, number] | number[]): this;
      isEmpty(): boolean;
    }

    class Map {
      constructor(options: Record<string, unknown>);
      addControl(control: unknown, position?: string): this;
      on(type: string, layerOrFn: string | ((e: any) => void), fn?: (e: any) => void): this;
      once(type: string, fn: (...args: any[]) => void): this;
      off(type: string, fn: (...args: any[]) => void): this;
      fire(type: string): this;
      addSource(id: string, source: Record<string, unknown>): this;
      addLayer(layer: Record<string, unknown>): this;
      getSource(id: string): GeoJSONSource | undefined;
      getLayer(id: string): unknown;
      setPaintProperty(layer: string, name: string, value: unknown): this;
      setLayoutProperty(layer: string, name: string, value: unknown): this;
      getLayoutProperty(layer: string, name: string): unknown;
      setFilter(layer: string, filter: unknown): this;
      setFeatureState(
        feature: { source: string; id: string | number; sourceLayer?: string },
        state: Record<string, unknown>,
      ): this;
      queryRenderedFeatures(
        pointOrBox?: unknown,
        options?: { layers?: string[]; filter?: unknown },
      ): Array<{ id?: string | number; properties?: Record<string, unknown> }>;
      getCanvas(): HTMLCanvasElement;
      isStyleLoaded(): boolean;
      getZoom(): number;
      setPadding(padding: Record<string, number>, options?: Record<string, unknown>): this;
      fitBounds(
        bounds: LngLatBounds | [[number, number], [number, number]],
        options?: Record<string, unknown>,
      ): this;
      resize(): this;
      remove(): void;
    }

    class NavigationControl {
      constructor(options?: Record<string, unknown>);
    }

    interface GeoJSONSource {
      setData(data: unknown): void;
    }
  }

  interface GeoJSONSource {
    setData(data: unknown): void;
  }

  const maplibregl: {
    Map: typeof maplibregl.Map;
    NavigationControl: typeof maplibregl.NavigationControl;
    LngLatBounds: typeof maplibregl.LngLatBounds;
  };

  export type { GeoJSONSource };
  export default maplibregl;
}

declare module "maplibre-gl/dist/maplibre-gl.css";
