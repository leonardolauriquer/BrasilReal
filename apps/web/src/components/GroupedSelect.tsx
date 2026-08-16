"use client";

import { useEffect, useId, useRef, useState } from "react";

export type SelectGroup = {
  key: string;
  label: string;
  items: Array<{ value: string; label: string }>;
};

type Props = {
  value: string;
  groups?: SelectGroup[];
  /** Flat list when no groups (e.g. years). */
  options?: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  "aria-label"?: string;
};

export function GroupedSelect({
  value,
  groups,
  options,
  onChange,
  disabled,
  placeholder = "Selecionar",
  "aria-label": ariaLabel,
}: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  const flat =
    options ||
    groups?.flatMap((g) => g.items.map((i) => ({ ...i, group: g.label }))) ||
    [];
  const current = flat.find((o) => o.value === value);
  const display = current?.label || placeholder;

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className={`gselect ${open ? "open" : ""}`} ref={rootRef}>
      <button
        type="button"
        className="gselect-trigger"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={ariaLabel}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="gselect-value">{display}</span>
        <span className="gselect-chevron" aria-hidden="true" />
      </button>
      {open ? (
        <div className="gselect-panel" role="listbox" id={listId} tabIndex={-1}>
          {groups
            ? groups.map((group) => (
                <div key={group.key} className="gselect-group" role="group" aria-label={group.label}>
                  <div className="gselect-group-label">{group.label}</div>
                  {group.items.map((item) => {
                    const selected = item.value === value;
                    return (
                      <button
                        key={item.value}
                        type="button"
                        role="option"
                        aria-selected={selected}
                        className={`gselect-option ${selected ? "selected" : ""}`}
                        onClick={() => {
                          onChange(item.value);
                          setOpen(false);
                        }}
                      >
                        {item.label}
                      </button>
                    );
                  })}
                </div>
              ))
            : (options || []).map((item) => {
                const selected = item.value === value;
                return (
                  <button
                    key={item.value}
                    type="button"
                    role="option"
                    aria-selected={selected}
                    className={`gselect-option ${selected ? "selected" : ""}`}
                    onClick={() => {
                      onChange(item.value);
                      setOpen(false);
                    }}
                  >
                    {item.label}
                  </button>
                );
              })}
        </div>
      ) : null}
    </div>
  );
}
