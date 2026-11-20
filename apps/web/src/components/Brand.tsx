export function Brand({ compact = false }: { compact?: boolean }) {
  return <div className={`brand ${compact ? 'brand-compact' : ''}`}><img src="/images/logo-ecoconecta.png" alt="EcoConecta" /><span>Villas de San Pablo</span></div>
}
