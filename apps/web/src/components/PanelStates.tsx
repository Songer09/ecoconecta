export function OperationPanel({ title, subtitle, items, action, onAction }: { title: string; subtitle: string; items: string[]; action: string; onAction: () => void }) {
  return <section className="content-card operation-panel"><div><p className="eyebrow">OPERACIÓN COMUNITARIA</p><h2>{title}</h2><p>{subtitle}</p></div><ul>{items.map((item) => <li key={item}><span className="operation-check">✓</span>{item}</li>)}</ul><button className="button button-secondary" onClick={onAction}>{action}</button></section>
}

export function InfoSection({ title, description, badge }: { title: string; description: string; badge: string }) {
  return <section className="content-card info-panel"><span className="info-badge">{badge}</span><p className="eyebrow">ECOCONECTA · VILLAS DE SAN PABLO</p><h2>{title}</h2><p>{description}</p></section>
}

export function EmptyState({ title, detail, action, onClick }: { title: string; detail: string; action?: string; onClick?: () => void }) {
  return <div className="empty-state"><span className="empty-symbol" aria-hidden="true">○</span><h3>{title}</h3><p>{detail}</p>{action && onClick && <button className="button button-secondary" onClick={onClick}>{action}</button>}</div>
}
