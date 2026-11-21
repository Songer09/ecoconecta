export function TerritoryMap({ onLearn }: { onLearn: () => void }) {
  return <section className="map-card" aria-labelledby="map-heading">
    <div className="map-heading"><div><p className="eyebrow">UN BARRIO QUE SE CONECTA</p><h2 id="map-heading">Villas de San Pablo</h2></div><span className="map-mark" aria-hidden="true">EC</span></div>
    <div className="territory-map" role="group" aria-label="Representación esquemática del territorio">
      <svg viewBox="0 0 520 270" aria-hidden="true" className="map-drawing">
        <path className="map-path" d="M14 66 C95 88 151 24 223 57 S352 90 506 37 M8 176 C98 151 156 222 238 180 S367 147 510 208 M130 7 C149 77 118 130 153 262 M342 5 C320 75 380 115 345 268" />
        <path className="map-path map-path-light" d="M20 126 C100 137 158 107 229 128 S370 109 500 130 M247 11 C228 80 270 190 247 258 M430 10 C412 73 451 165 422 257" />
        <path className="map-green" d="M227 153 C244 136 269 138 283 156 C301 178 285 199 262 202 C240 204 216 179 227 153Z" />
        <g className="map-blocks"><rect x="31" y="24" width="66" height="28" rx="8"/><rect x="170" y="27" width="57" height="24" rx="8"/><rect x="381" y="57" width="76" height="27" rx="8"/><rect x="44" y="92" width="49" height="27" rx="8"/><rect x="185" y="88" width="44" height="27" rx="8"/><rect x="370" y="105" width="70" height="26" rx="8"/><rect x="50" y="194" width="64" height="29" rx="8"/><rect x="173" y="218" width="68" height="27" rx="8"/><rect x="379" y="187" width="83" height="28" rx="8"/></g>
        <text x="257" y="174" textAnchor="middle">HUERTA</text>
      </svg>
      <button className="map-learning-point" onClick={onLearn} aria-label="Abrir aprendizaje ambiental desde el mapa"><span className="map-point-pulse"/><span className="map-point-label">Aprende</span></button>
      <div className="map-caption"><span className="map-caption-dot"/> Representación del territorio · no está a escala</div>
    </div>
    <button className="map-link" onClick={onLearn}>Explorar aprendizaje ambiental <span aria-hidden="true">→</span></button>
  </section>
}
