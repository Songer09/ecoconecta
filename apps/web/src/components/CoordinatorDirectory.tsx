const coordinators = [
  {
    name: 'Coordinador de recicladores',
    role: 'Flujo de materiales reciclables',
  },
  {
    name: 'Coordinador de huerteros',
    role: 'Flujo orgánico y huerta comunitaria',
  },
]

export function CoordinatorDirectory() {
  return <section className="coordinator-directory" aria-labelledby="coordinator-directory-title">
    <div className="coordinator-directory-intro">
      <p className="eyebrow">EQUIPO ECOCONECTA</p>
      <h2 id="coordinator-directory-title">Directorio de coordinadores</h2>
      <p>Roles del equipo operativo. Los nombres, teléfonos y zonas se mostrarán cuando estén disponibles en el directorio oficial.</p>
    </div>
    <div className="coordinator-directory-grid">
      {coordinators.map((person) => <article className="coordinator-contact-card" key={person.name}>
        <span className="coordinator-contact-icon" aria-hidden="true">{person.name.slice(0, 1)}</span>
        <div className="coordinator-contact-heading"><h3>{person.name}</h3><p>{person.role}</p></div>
        <dl>
          <div><dt>Teléfono</dt><dd>Sin datos disponibles</dd></div>
          <div><dt>Zonas asignadas</dt><dd>Sin datos disponibles</dd></div>
        </dl>
      </article>)}
    </div>
  </section>
}
