import { useEffect, useState, type FormEvent } from 'react'
import { request } from '../services/authApi'

type Row = Record<string,string | number | boolean>
const labels: Record<string,string> = {code:'Código',scheduled_start:'Inicio',scheduled_end:'Fin',accounts:'Cuentas',active:'Activas',name:'Nombre',title:'Nombre',location:'Lugar',organizer:'Organiza',description:'Descripción',starts_at:'Inicio',ends_at:'Fin',flow:'Tipo de residuo',points_per_kg:'Puntos por kg',quantity:'Cantidad',unit:'Unidad',stock:'Disponibles',price:'Puntos necesarios',full_name:'Nombre',role:'Rol',kg:'Peso (kg)',estimated_cop:'Valor estimado (COP)',missing_prices:'Tarifas pendientes',is_available:'Disponible',is_published:'Publicado',weekday:'Día',address:'Dirección',balance:'Saldo',neighborhood:'Conjunto',member_role:'Función'}
export function LiveWorkspace({section}: {section:string}) {
  const [rows,setRows]=useState<Row[]>([])
  const [materials,setMaterials]=useState<Row[]>([])
  const [error,setError]=useState('')
  const [busy,setBusy]=useState(false)
  const [loading,setLoading]=useState(true)
  const [revision,setRevision]=useState(0)
  useEffect(()=>{
    const controller=new AbortController()
    const init={signal:controller.signal}
    async function load(){
      const end=new Date(), start=new Date(end.getTime()-30*86400000)
      const paths:Record<string,string>={zones:'/zones',routes:'/collector/route?day='+new Intl.DateTimeFormat('en-CA',{timeZone:'America/Bogota'}).format(end),events:'/admin/events',points:'/points/rules',inventory:'/garden/needs',redemptions:'/rewards',availability:'/collector/availability',income:'/coordinator/reports/purchase-value?'+new URLSearchParams({start:start.toISOString(),end:end.toISOString()}),profile:'/users/me/profile',team:'/public/community',home:'/admin/users',reports:'/admin/users'}
      if(section==='catalog'||section==='points'){
        const groups=await Promise.all(['organico','reciclable'].map(f=>request<Row[]>('/public/materials?flow='+f,init)))
        setMaterials(groups[1])
        if(section==='catalog'){setRows(groups.flat());return}
      }
      if(section==='home'||section==='reports'){
        const groups=new Map<string,{role:string;accounts:number;active:number}>()
        for(let offset=0;;offset+=100){
          const page=await request<Row[]>('/admin/users?limit=100&offset='+offset,init)
          for(const user of page){
            const role=String(user.role)
            const group=groups.get(role)??{role,accounts:0,active:0}
            group.accounts++; if(user.is_active&&user.is_pilot)group.active++
            groups.set(role,group)
          }
          if(page.length<100)break
        }
        setRows([...groups.values()]);return
      }
      if(section==='profile'){
        const [profile,points]=await Promise.all([request<Row>('/users/me/profile',init),request<Row>('/users/me/points',init)])
        setRows([{...profile,...points}]);return
      }
      const value=await request<Row[]|Row>(paths[section],init)
      setRows(Array.isArray(value)?value:[value])
    }
    setLoading(true); setError('')
    void load().catch(e=>{if(!controller.signal.aborted)setError(e.message)}).finally(()=>{if(!controller.signal.aborted)setLoading(false)})
    return ()=>controller.abort()
  },[section,revision])
  async function save(path:string,method:string,data:unknown){
    setBusy(true);setError('')
    try{await request(path,{method,body:JSON.stringify(data)});setRevision(v=>v+1);return true}
    catch(e){setError(e instanceof Error?e.message:'No se pudo guardar.');return false}
    finally{setBusy(false)}
  }
  async function submit(e:FormEvent<HTMLFormElement>){
    e.preventDefault();const form=e.currentTarget
    const data=Object.fromEntries(new FormData(form)) as Record<string,string>
    let ok=false
    if(section==='zones')ok=await save('/admin/zones','PUT',{code:data.code,name:data.name,is_active:true})
    if(section==='catalog')ok=await save('/admin/materials','PUT',{name:data.name,flow:data.flow,is_active:true})
    if(section==='points')ok=await save('/admin/points/rules/'+data.material,'POST',{points_per_kg:data.rate})
    if(section==='events')ok=await save('/admin/events','POST',{...data,starts_at:data.starts_at+':00-05:00',ends_at:data.ends_at+':00-05:00'})
    if(ok)form.reset()
  }
  return <section className="admin-workspace">
    {['zones','catalog','events','points'].includes(section)&&<form className="admin-inline-form" onSubmit={submit}>
      {section==='zones'&&<><label>Código de zona<input name="code" required/></label><label>Nombre<input name="name" required/></label></>}
      {section==='catalog'&&<><label>Material<input name="name" required/></label><label>Flujo<select name="flow"><option value="reciclable">Reciclable</option><option value="organico">Orgánico</option></select></label></>}
      {section==='events'&&['title','organizer','location','description','starts_at','ends_at'].map(k=><label key={k}>{labels[k]}<input name={k} type={k.endsWith('_at')?'datetime-local':'text'} required/></label>)}
      {section==='points'&&<><label>Regla<select name="material"><option value="organic">Orgánicos</option>{materials.map(r=><option key={String(r.id)} value={String(r.id)}>{r.name}</option>)}</select></label><label>Puntos por kilogramo<input name="rate" type="number" min="0.000001" step="0.000001" required/></label></>}
      <button className="button button-primary" disabled={busy}>{section==='events'?'Guardar borrador':'Guardar'}</button>
    </form>}
    {loading?<p role="status">Cargando…</p>:error?<p role="alert">{error} <button onClick={()=>setRevision(v=>v+1)}>Actualizar</button></p>:!rows.length?<p>Aún no hay registros.</p>:<div className="admin-record-list">{rows.map((r,i)=><article key={String(r.id??r.collective_id??i)}><div>{Object.entries(r).filter(([k])=>labels[k]).map(([k,v])=><p key={k}><strong>{labels[k]}</strong> {typeof v==='boolean'?(v?'Sí':'No'):String(v??'Pendiente')}</p>)}</div>
      {section==='availability'&&<button disabled={busy} onClick={()=>void save('/collector/availability/'+r.collective_id,'PUT',{is_available:!r.is_available})}>Cambiar disponibilidad</button>}
      {section==='events'&&<button disabled={busy} onClick={()=>void save('/admin/events/'+r.id,'PUT',{title:r.title,description:r.description,organizer:r.organizer,location:r.location,starts_at:r.starts_at,ends_at:r.ends_at,is_published:!r.is_published,expected_updated_at:r.updated_at})}>{r.is_published?'Retirar publicación':'Publicar'}</button>}
    </article>)}</div>}
  </section>
}
