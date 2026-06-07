import type { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({ title, subtitle, icon, actions }: PageHeaderProps) {
  return (
    <header className="nb-page-header">
      <div className="nb-page-header-left">
        {icon ? <div className="nb-page-header-icon">{icon}</div> : null}
        <div>
          <h1 className="nb-page-title">{title}</h1>
          {subtitle ? <p className="nb-page-subtitle">{subtitle}</p> : null}
        </div>
      </div>
      {actions ? <div className="nb-page-header-actions">{actions}</div> : null}
    </header>
  );
}
