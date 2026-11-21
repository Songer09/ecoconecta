export function InstitutionalSection() {
  return <section className="about-ecoconecta" id="conocenos" aria-labelledby="about-title">
    <header className="about-intro">
      <p className="eyebrow">ECOCONECTA · VILLAS DE SAN PABLO</p>
      <h2 id="about-title">Un barrio que conecta comunidad, reciclaje y huerta</h2>
      <p>EcoConecta acompaña la organización comunitaria para aprovechar mejor los residuos y cuidar los espacios compartidos de Villas de San Pablo, en Barranquilla.</p>
    </header>

    <div className="about-institutions">
      <article className="about-institution-card about-foundation">
        <span className="about-card-label">QUIÉNES ACOMPAÑAN</span>
        <h3>Fundación Santo Domingo</h3>
        <p>Impulsa procesos de transformación y movilidad social en Colombia junto con aliados y comunidades.</p>
      </article>
      <article className="about-institution-card about-territory">
        <span className="about-card-label">DÓNDE NOS ENCONTRAMOS</span>
        <h3>Villas de San Pablo</h3>
        <p>Una comunidad de Barranquilla donde hogares, equipamientos y organizaciones locales pueden conectarse para cuidar el barrio.</p>
      </article>
    </div>

    <section className="about-process" aria-labelledby="about-process-title">
      <div className="about-process-heading">
        <p className="eyebrow">ASÍ FUNCIONA</p>
        <h3 id="about-process-title">Cada aporte sigue un camino claro</h3>
      </div>
      <ol className="about-process-steps">
        <li><span>1</span><div><strong>Separa</strong><p>Elige reciclaje o residuos orgánicos para la huerta.</p></div></li>
        <li><span>2</span><div><strong>Coordina</strong><p>El equipo comunitario revisa la solicitud y acuerda la recolección.</p></div></li>
        <li><span>3</span><div><strong>Verifica</strong><p>La coordinación confirma el aporte; los puntos se reconocen después del cierre según las reglas vigentes.</p></div></li>
      </ol>
    </section>

    <div className="about-lines">
      <article className="about-line-card about-line-recycling">
        <span className="about-line-tag">RECICLAJE</span>
        <h3>Materiales limpios y aprovechables</h3>
        <p>La coordinación de reciclaje organiza la revisión y la recolección de materiales reciclables.</p>
      </article>
      <article className="about-line-card about-line-garden">
        <span className="about-line-tag">ORGÁNICO · HUERTA</span>
        <h3>Aportes conectados con el huerto</h3>
        <p>La coordinación de huerteros identifica prioridades cuando el equipo confirma qué necesita el inventario del huerto.</p>
      </article>
    </div>
    <p className="about-community-note">También puedes consultar educación ambiental y los eventos que publique la coordinación.</p>
  </section>
}
