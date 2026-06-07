import type { ReactNode, CSSProperties } from "react";

type DashboardCardProps = {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
  style?: CSSProperties;
};

export function DashboardCard({
  title,
  subtitle,
  children,
  actions,
  className,
  style,
}: DashboardCardProps) {
  const classes = className
    ? `nb-card nb-card-padded ${className}`
    : "nb-card nb-card-padded";
  return (
    <section className={classes} style={style}>
      {title || subtitle || actions ? (
        <div className="nb-card-header">
          <div>
            {title ? <h2 className="nb-card-title">{title}</h2> : null}
            {subtitle ? (
              <p className="nb-card-subtitle">{subtitle}</p>
            ) : null}
          </div>
          {actions ? <div className="nb-card-actions">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
