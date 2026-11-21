import { useEffect, useState } from 'react'
import { ApiRequestError, communityApi } from '../services/authApi'
import type { GardenReward } from '../services/authApi'
import { EmptyState } from './PanelStates'

// Values from the Figma wireframe, available only during the development demo.
const sampleRewards: GardenReward[] = [
  { id: 'figma-fruit', name: 'Bolsa de frutas', price: 50, stock: 1 },
  { id: 'figma-vegetables', name: 'Verduras frescas', price: 80, stock: 1 },
  { id: 'figma-herbs', name: 'Plantas aromáticas', price: 150, stock: 1 },
]
const pointsFormat = new Intl.NumberFormat('es-CO')
const pendingRedemptions = new Map<string, { rewardId: string; key: string }>()

export function GardenRedemptions({ accountId }: { accountId?: string }) {
  const [data, setData] = useState<{ balance: number; rewards: GardenReward[] } | null>(null)
  const [loadError, setLoadError] = useState(false)
  const [reload, setReload] = useState(0)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const pending = accountId ? pendingRedemptions.get(accountId) : undefined

  useEffect(() => {
    if (!accountId) return
    let current = true
    Promise.all([communityApi.getPoints(), communityApi.getRewards()])
      .then(([points, rewards]) => { if (current) setData({ balance: Number(points.balance), rewards }) })
      .catch(() => { if (current) setLoadError(true) })
    return () => { current = false }
  }, [accountId, reload])

  function refresh() {
    setLoadError(false)
    setData(null)
    setReload((previous) => previous + 1)
  }

  async function redeem(reward: GardenReward) {
    if (!accountId || busy) return
    const operation = pendingRedemptions.get(accountId) ?? { rewardId: reward.id, key: crypto.randomUUID() }
    if (operation.rewardId !== reward.id) return
    pendingRedemptions.set(accountId, operation)
    setBusy(true)
    setNotice('')
    setError('')
    try {
      await communityApi.redeemReward(reward.id, operation.key)
      pendingRedemptions.delete(accountId)
      setSelectedId(null)
      setNotice(`Canje confirmado: ${reward.name}.`)
      refresh()
    } catch (reason) {
      const declined = reason instanceof ApiRequestError && [400, 403, 404, 409, 422].includes(reason.status)
      if (declined) {
        pendingRedemptions.delete(accountId)
        setSelectedId(null)
        refresh()
      }
      setError(reason instanceof Error ? reason.message : 'No pudimos completar el canje.')
    } finally {
      setBusy(false)
    }
  }

  const demo = !accountId
  const rewards = demo ? sampleRewards : data?.rewards ?? []
  const balance = demo ? 120 : data?.balance

  return <div className="garden-redemptions">
    <section className="garden-points" aria-label="Saldo de puntos">
      <span>Tienes</span>
      <strong>{balance === undefined ? '—' : pointsFormat.format(balance)} puntos</strong>
      <small>para canjear en el huerto</small>
    </section>

    <section className="garden-catalog" aria-labelledby="garden-catalog-title">
      <h2 id="garden-catalog-title">Productos del huerto</h2>
      {demo && <p className="garden-catalog-note">Productos y valores de ejemplo.</p>}
      {notice && <p className="garden-catalog-note" role="status">{notice}</p>}
      {error && <p className="form-error" role="alert">{error}</p>}
      {loadError ? <EmptyState title="No pudimos consultar el saldo y el catálogo" detail="Intenta actualizar para ver tus puntos y los productos disponibles." action="Reintentar" onClick={refresh}/>
        : balance === undefined ? <p role="status">Cargando tus puntos y los productos…</p>
        : !rewards.length ? <EmptyState title="Aún no hay productos" detail="Los productos aparecerán aquí cuando estén publicados."/>
        : <div className="garden-products">{rewards.map((reward) => {
          const retry = pending?.rewardId === reward.id
          const confirming = selectedId === reward.id || retry
          const unavailable = !reward.stock ? 'Agotado' : balance < reward.price ? 'Puntos insuficientes' : ''
          return <article className="garden-product" key={reward.id}>
            <div className="garden-product-main">
              <span className="garden-product-icon" aria-hidden="true">❧</span>
              <div><h3>{reward.name}</h3><strong>{pointsFormat.format(reward.price)} puntos</strong></div>
            </div>
            {confirming ? <div className="garden-product-actions">
              {!retry && <button className="button button-secondary" disabled={busy} onClick={() => setSelectedId(null)}>Cancelar</button>}
              <button className="button button-primary" disabled={busy} onClick={() => void redeem(reward)}>{busy ? 'Guardando…' : retry && error ? 'Reintentar canje' : 'Confirmar canje'}</button>
            </div> : <button className="button button-primary" disabled={busy || Boolean(pending) || Boolean(unavailable)} onClick={() => {
              if (demo) setNotice('Este producto es un ejemplo del catálogo.')
              else { setSelectedId(reward.id); setError('') }
            }}>{unavailable || 'Canjear'}</button>}
          </article>
        })}</div>}
    </section>
  </div>
}
