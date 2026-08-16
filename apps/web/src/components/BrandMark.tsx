import { BRAZIL_SILHOUETTE_PATH } from "@/lib/brand";

type Props = {
  className?: string;
  decorative?: boolean;
};

export function BrandMark({ className, decorative = true }: Props) {
  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden={decorative ? true : undefined}
      role={decorative ? undefined : "img"}
    >
      {!decorative ? <title>Brasil Real</title> : null}
      <rect width="64" height="64" rx="14" fill="#14201c" />
      <path
        d={BRAZIL_SILHOUETTE_PATH}
        fill="#3dcf9a"
        stroke="#3dcf9a"
        strokeWidth="1.15"
        strokeLinejoin="round"
      />
    </svg>
  );
}
