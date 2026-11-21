const villasWebsite = 'https://villasdesanpablo.com/'

export function VillasStorySection() {
  return <>
    <section className="villas-story" aria-labelledby="villas-story-title">
      <a
        className="villas-story-media"
        href={villasWebsite}
        target="_blank"
        rel="noreferrer"
        aria-label="Ver el sitio de Villas de San Pablo"
      >
        <span className="villas-story-logo-plate">
          <img src="/images/logo-villas-san-pablo.png" alt="Villas de San Pablo, Barranquilla" />
        </span>
        <span className="villas-story-play" aria-hidden="true">↗</span>
      </a>
      <div className="villas-story-copy">
        <h2 id="villas-story-title">
          <strong>Visita nuestro sitio web</strong>
          <span>y conoce más sobre nosotros</span>
        </h2>
        <p>Descubre las <strong>iniciativas y espacios de la comunidad</strong> de Villas de San Pablo y lee las últimas noticias del barrio.</p>
        <a className="villas-website-link" href={villasWebsite} target="_blank" rel="noopener noreferrer">Visitar Villas de San Pablo <span aria-hidden="true">↗</span></a>
      </div>
    </section>
  </>
}

export function CommunityFooter() {
  return <footer className="community-footer">
    <div className="community-footer-grid">
      <div className="footer-brand-stack" aria-label="Villas de San Pablo con el apoyo de Fundación Santo Domingo">
        <img className="footer-villas-logo" src="/images/footer-villas-san-pablo.png" alt="Villas de San Pablo" />
        <span>Con el apoyo de</span>
        <img className="footer-foundation-logo" src="/images/footer-fundacion-santo-domingo.png" alt="Fundación Santo Domingo" />
      </div>

      <section className="footer-column" aria-labelledby="footer-sales-title">
        <h2 id="footer-sales-title">Salas de ventas</h2>
        <p><strong>Ubicación:</strong><br/>Cra 9 G # 110 - 187<br/>Parque Logístico Caribe Verde<br/>Barranquilla</p>
        <p><strong>Lunes a sábado:</strong><br/>9:00 a.m. - 4:00 p.m.</p>
        <p><strong>Domingos y festivos:</strong><br/>10:00 a.m. - 5:00 p.m.</p>
      </section>

      <nav className="footer-column footer-links" aria-labelledby="footer-links-title">
        <h2 id="footer-links-title">Enlaces recomendados</h2>
        <a href="https://porquequieroestarbien.com/" target="_blank" rel="noreferrer">Porque Quiero Estar Bien</a>
        <a href="https://villasdesanpablo.com/vivienda-propia/" target="_blank" rel="noreferrer">Ventas</a>
        <a href="https://fundacionsantodomingo.org/conocenos/politica-de-proteccion-de-datos/" target="_blank" rel="noreferrer">Protección de datos</a>
      </nav>

      <section className="footer-column" aria-labelledby="footer-office-title">
        <h2 id="footer-office-title">Oficina de la Fundación Santo Domingo en Villas de San Pablo</h2>
        <p><strong>Dirección:</strong><br/>Carrera 28 C # 143 C - 58.</p>
        <p><strong>Lunes a sábado:</strong><br/>9:00 a.m. - 4:00 p.m.</p>
      </section>
    </div>
    <p className="footer-copyright">© 2026 Todos los derechos reservados. <strong>Fundación Santo Domingo</strong></p>
  </footer>
}
