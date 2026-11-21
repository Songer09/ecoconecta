export function Brand({ compact = false }: { compact?: boolean }) {
  return <div className={`brand ${compact ? 'brand-compact' : ''}`}><img src="/images/logo-ecoconecta.png" alt="EcoConecta Villas de San Pablo" /></div>
}
