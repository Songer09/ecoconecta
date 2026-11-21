import { useEffect, useState } from 'react'
import { ApiRequestError, request } from '../services/authApi'
import type { Role, CollectionRequest } from '../domain/types'

type Weight = { waste_type_id: string; quantity: string; unit: string }
type Pickup = { id: string; items: Weight[]; confirmed_at: string | null }
type Choice = { id: string; name: string }
export function PickupOperations({item, role, refresh, onDone}: {item: CollectionRequest; role: Role; refresh: () => void; onDone: () => void}) {
  const [options, setOptions] = useState<Choice[]>([])
  const [selected, setSelected] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [weight, setWeight] = useState('')
  const [pickup, setPickup] = useState<Pickup | null>(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [loadingChoices, setLoadingChoices] = useState(true)
  const coord = role === 'kelly' || role === 'vivi'
  const path = '/requests/' + item.id
  useEffect(() => {
    const controller = new AbortController()
    const init = { signal: controller.signal }
    async function load() {
      setLoadingChoices(true)
      setOptions([])
      setSelected('')
      try {
        if (coord && item.status === 'UNDER_REVIEW') {
          const rows = await request<{collector_id: string; name: string}[]>('/collectors/availability?request_id='+item.id,init)
          setOptions([...new Map(rows.map(r=>[r.collector_id,{id:r.collector_id,name:r.name}])).values()])
        } else if (item.status === 'SCHEDULED') {
          setOptions(await request<Choice[]>('/public/materials?flow='+(item.flow === 'ORGANIC'?'organico':'reciclable'),init))
          if (role === 'collector') {
            try {
              setPickup(await request<Pickup>(path + '/collection', init))
            } catch (error) {
              if (!(error instanceof ApiRequestError) || error.status !== 404) throw error
              setPickup(null)
            }
          }
        }
      } catch (error) {
        if (!controller.signal.aborted) setMessage(error instanceof Error ? error.message : 'No se pudieron cargar las opciones.')
      } finally {
        if (!controller.signal.aborted) setLoadingChoices(false)
      }
    }
    void load()
    return ()=>controller.abort()
  },[item.id,item.flow,item.status,coord,role])
  const post = <T,>(url: string, body?: unknown) => request<T>(url,{method:'POST',body:JSON.stringify(body)})
  async function submit() {
    if (coord && item.status === 'ASSIGNED') {
      if (!start || !end || start.slice(0,10) !== end.slice(0,10) || end <= start) {
        setMessage('La visita debe comenzar y terminar el mismo día, con fin posterior al inicio.'); return
      }
      if (new Date(start + ':00-05:00').getTime() <= Date.now()) {
        setMessage('Elige una fecha y hora futuras.'); return
      }
    }
    setBusy(true); setMessage('')
    try {
      if (coord && item.status==='RECEIVED') await post(path+'/review')
      else if (coord && item.status==='UNDER_REVIEW') await post(path+'/assignments',{collector_id:selected})
      else if (coord && item.status==='ASSIGNED') await post(path+'/schedule',{scheduled_start:start+':00-05:00',scheduled_end:end+':00-05:00'})
      else if (role==='collector') {
        const collection = pickup ?? await post<Pickup>(path+'/collection')
        await post('/collections/'+collection.id+'/items',{waste_type_id:selected,quantity:weight})
        setPickup(await request<Pickup>(path+'/collection'))
        setSelected('')
        setWeight('')
        setMessage('Peso guardado. Puedes agregar otro material o terminar el registro.')
        return
      } else if (!pickup) {
        setPickup(await request<Pickup>('/coordinator'+path+'/collection'))
        return
      } else await post('/collections/'+pickup.id+'/confirm',{items:pickup.items.map(({waste_type_id,quantity})=>({waste_type_id,quantity}))})
      setMessage('Cambio guardado.'); refresh()
    } catch(e) {setMessage(e instanceof Error?e.message:'No se pudo guardar.')}
    finally {setBusy(false)}
  }
  const label = coord ? ({RECEIVED:'Revisar solicitud',UNDER_REVIEW:'Asignar recolector',ASSIGNED:'Programar',SCHEDULED:pickup?'Confirmar pesos':'Consultar pesaje'} as Record<string,string>)[item.status] : role==='collector' && item.status==='SCHEDULED'?'Guardar peso':null
  if (!label) return null
  const savedMaterials = new Set(pickup?.items.map((entry) => entry.waste_type_id) ?? [])
  const selectableOptions = role === 'collector' ? options.filter((option) => !savedMaterials.has(option.id)) : options
  const needsMaterial = item.status === 'UNDER_REVIEW' || (role === 'collector' && item.status === 'SCHEDULED')
  return <form className="admin-inline-form" onSubmit={e=>{e.preventDefault();void submit()}}>
    {needsMaterial && <label>{coord?'Recolector disponible':'Material'}<select required value={selected} onChange={e=>setSelected(e.target.value)}><option value="">Selecciona una opción</option>{selectableOptions.map(o=><option key={o.id} value={o.id}>{o.name}</option>)}</select></label>}
    {item.status==='ASSIGNED' && <><p>Elige una jornada: inicio y fin deben corresponder al mismo día.</p><label>Inicio (Colombia)<input type="datetime-local" required value={start} onChange={e=>{ const value=e.target.value; setStart(value); if(value){ const date=new Date(value+':00-05:00'); date.setMinutes(date.getMinutes()+30); const suggested=new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Bogota',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(date).replace(' ','T'); setEnd(suggested.slice(0,10)===value.slice(0,10)?suggested:value.slice(0,10)+'T23:59') } }}/></label><label>Fin (Colombia)<input type="datetime-local" required min={start} max={start ? start.slice(0,10)+'T23:59' : undefined} value={end} onChange={e=>setEnd(e.target.value)}/></label></>}
    {role==='collector' && <label>Peso en kg<input type="number" required min="0.0001" step="0.0001" value={weight} onChange={e=>setWeight(e.target.value)}/></label>}
    {pickup && <ul>{pickup.items.map(i=><li key={i.waste_type_id}>{options.find(o=>o.id===i.waste_type_id)?.name??'Material registrado'} · {i.quantity} {i.unit}</li>)}</ul>}
    {role === 'collector' && pickup && !selectableOptions.length && <p role="status">Todos los materiales activos ya están registrados.</p>}
    <button className="button button-primary" disabled={busy || loadingChoices || (role === 'collector' && (!selectableOptions.length || !selected || !weight)) || Boolean(coord && item.status === 'SCHEDULED' && pickup && (!pickup.items.length || pickup.confirmed_at))}>{loadingChoices ? 'Cargando…' : busy?'Guardando…':label}</button>
    {role === 'collector' && pickup && <button type="button" className="button button-secondary" onClick={onDone}>Terminé de registrar</button>}
    {message&&<p role="status">{message}</p>}
  </form>
}
