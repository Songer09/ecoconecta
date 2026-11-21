import { useEffect, useState } from 'react'
import { request } from '../services/authApi'
import type { Role, CollectionRequest } from '../domain/types'

type Weight = { waste_type_id: string; quantity: string }
type Pickup = { id: string; items: Weight[] }
type Choice = { id: string; name: string }
export function PickupOperations({item, role, refresh}: {item: CollectionRequest; role: Role; refresh: () => void}) {
  const [options, setOptions] = useState<Choice[]>([])
  const [selected, setSelected] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [weight, setWeight] = useState('')
  const [pickup, setPickup] = useState<Pickup | null>(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const coord = role === 'kelly' || role === 'vivi'
  const path = '/requests/' + item.id
  useEffect(() => {
    const controller = new AbortController()
    const init = { signal: controller.signal }
    async function load() {
      if (coord && item.status === 'UNDER_REVIEW') {
        const rows = await request<{collector_id: string; name: string}[]>('/collectors/availability?request_id='+item.id,init)
        setOptions([...new Map(rows.map(r=>[r.collector_id,{id:r.collector_id,name:r.name}])).values()])
      } else if (item.status === 'SCHEDULED') {
        setOptions(await request<Choice[]>('/public/materials?flow='+(item.flow === 'ORGANIC'?'organico':'reciclable'),init))
      }
    }
    void load().catch(e=>{if(!controller.signal.aborted)setMessage(e.message)})
    return ()=>controller.abort()
  },[item.id,item.flow,item.status,coord])
  const post = <T,>(url: string, body?: unknown) => request<T>(url,{method:'POST',body:JSON.stringify(body)})
  async function submit() {
    setBusy(true); setMessage('')
    try {
      if (coord && item.status==='RECEIVED') await post(path+'/review')
      else if (coord && item.status==='UNDER_REVIEW') await post(path+'/assignments',{collector_id:selected})
      else if (coord && item.status==='ASSIGNED') await post(path+'/schedule',{scheduled_start:start+':00-05:00',scheduled_end:end+':00-05:00'})
      else if (role==='collector') {
        const collection = await post<Pickup>(path+'/collection')
        await post('/collections/'+collection.id+'/items',{waste_type_id:selected,quantity:weight})
      } else if (!pickup) {
        setPickup(await request<Pickup>('/coordinator'+path+'/collection'))
        return
      } else await post('/collections/'+pickup.id+'/confirm',{items:pickup.items.map(({waste_type_id,quantity})=>({waste_type_id,quantity}))})
      setMessage('Cambio guardado.'); refresh()
    } catch(e) {setMessage(e instanceof Error?e.message:'No se pudo guardar.')}
    finally {setBusy(false)}
  }
  const label = coord ? ({RECEIVED:'Revisar solicitud',UNDER_REVIEW:'Asignar recolector',ASSIGNED:'Programar',SCHEDULED:pickup?'Confirmar pesos':'Consultar pesaje'} as Record<string,string>)[item.status] : role==='collector' && item.status==='SCHEDULED'?'Registrar peso':null
  if (!label) return null
  return <form className="admin-inline-form" onSubmit={e=>{e.preventDefault();void submit()}}>
    {(item.status==='UNDER_REVIEW'||role==='collector') && <label>{coord?'Recolector disponible':'Material'}<select required value={selected} onChange={e=>setSelected(e.target.value)}><option value="">Selecciona una opción</option>{options.map(o=><option key={o.id} value={o.id}>{o.name}</option>)}</select></label>}
    {item.status==='ASSIGNED' && <><label>Inicio (Colombia)<input type="datetime-local" required value={start} onChange={e=>setStart(e.target.value)}/></label><label>Fin (Colombia)<input type="datetime-local" required min={start} value={end} onChange={e=>setEnd(e.target.value)}/></label></>}
    {role==='collector' && <label>Peso en kg<input type="number" required min="0.0001" step="0.0001" value={weight} onChange={e=>setWeight(e.target.value)}/></label>}
    {pickup && <ul>{pickup.items.map(i=><li key={i.waste_type_id}>{options.find(o=>o.id===i.waste_type_id)?.name??'Material registrado'} · {i.quantity} kg</li>)}</ul>}
    <button className="button button-primary" disabled={busy||Boolean(pickup&&!pickup.items.length)}>{label}</button>{message&&<p role="status">{message}</p>}
  </form>
}
