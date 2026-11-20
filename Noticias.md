# Noticias de EcoConecta

En `feat/backend-core`, la carga de fotos admite hasta 24 megapíxeles y 5 MiB.
Se probó una foto sintética de 3120 × 4160 con rotación EXIF. La API la envió
normalizada, con lado mayor de 1600 píxeles y sin metadatos. Pasaron las 17
pruebas en PostgreSQL.

En el Mac de visión, el equipo verificó el flujo real con la versión anterior
del adaptador y una foto reducida. EcoConecta recibió HTTP 200, clase
`banana_peel` y versión `0.3.0-bdwaste-individual-experimental`. Queda repetir
el caso con la foto original y conectar el formulario web. El piloto necesita
una instancia de Compost-AI con los pesos instalados.
