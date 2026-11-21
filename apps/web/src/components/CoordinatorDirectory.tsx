const coordinators = [
  {
    name: 'Vivi',
    role: 'Coordinadora de recicladores',
    phone: 'Pendiente de confirmación',
    zones: 'Pendientes de confirmación',
  },
  {
    name: 'Kelly',
    role: 'Coordinadora de huerteros',
    phone: 'Pendiente de confirmación',
    zones: 'Pendientes de confirmación',
  },
]

export function CoordinatorDirectory() {
  return <section className="coordinator-directory" aria-labelledby="coordinator-directory-title">
    <div className="coordinator-directory-intro">
      <p className="eyebrow">EQUIPO ECOCONECTA</p>
      <h2 id="coordinator-directory-title">Directorio de coordinadoras</h2>
      <p>Contactos de las dos líneas comunitarias. Los teléfonos y las zonas deben confirmarse antes de publicarse.</p>
    </div>
    <div className="coordinator-directory-grid">
      {coordinators.map((person) => <article className="coordinator-contact-card" key={person.name}>
        <span className="coordinator-contact-icon" aria-hidden="true">{person.name.slice(0, 1)}</span>
        <div className="coordinator-contact-heading"><h3>{person.name}</h3><p>{person.role}</p></div>
        <dl>
          <div><dt>Número telefónico</dt><dd>{person.phone}</dd></div>
          <div><dt>Zonas asignadas</dt><dd>{person.zones}</dd></div>
        </dl>
      </article>)}
    </div>
  </section>
}
