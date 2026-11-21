import { useEffect, useState } from 'react'
import { ApiRequestError, educationApi } from '../services/authApi'
import type { EducationModule, EducationModuleSummary, LearningProgress } from '../services/authApi'
import { EmptyState } from './PanelStates'

const lessonIcons = ['◇', '♻', '✓', '○', '✳', '▤']

function messageFrom(error: unknown) {
  return error instanceof Error ? error.message : 'Vuelve a intentarlo en unos momentos.'
}

export function EducationContent({ onSignIn }: { onSignIn: () => void }) {
  const [modules, setModules] = useState<EducationModuleSummary[]>([])
  const [progress, setProgress] = useState<LearningProgress | null>(null)
  const [selected, setSelected] = useState<EducationModuleSummary | null>(null)
  const [lesson, setLesson] = useState<EducationModule | null>(null)
  const [loadError, setLoadError] = useState('')
  const [lessonError, setLessonError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [expired, setExpired] = useState(false)
  const [saving, setSaving] = useState(false)
  const [catalogAttempt, setCatalogAttempt] = useState(0)
  const [lessonAttempt, setLessonAttempt] = useState(0)

  useEffect(() => {
    let current = true
    Promise.all([educationApi.listModules(), educationApi.getProgress()])
      .then(([catalog, accountProgress]) => {
        if (!current) return
        setModules(catalog)
        setProgress(accountProgress)
      })
      .catch((error: unknown) => {
        if (!current) return
        if (error instanceof ApiRequestError && error.status === 401) setExpired(true)
        else setLoadError(messageFrom(error))
      })
    return () => { current = false }
  }, [catalogAttempt])

  useEffect(() => {
    if (!selected) return
    let current = true
    educationApi.readModule(selected.id)
      .then((detail) => { if (current) setLesson(detail) })
      .catch((error: unknown) => { if (current) setLessonError(messageFrom(error)) })
    return () => { current = false }
  }, [selected, lessonAttempt])

  const completed = new Set(progress?.completions.map(({ module_id }) => module_id))

  async function finishLesson() {
    if (!lesson || !progress || saving || completed.has(lesson.id)) return
    setSaveError('')
    setSaving(true)
    try {
      const completion = await educationApi.complete(lesson.id)
      const count = progress.completed + 1
      setProgress({ ...progress, completed: count, percentage: progress.total ? Math.round(count * 100 / progress.total) : 0, completions: [...progress.completions, completion] })
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) setExpired(true)
      else setSaveError(messageFrom(error))
    } finally {
      setSaving(false)
    }
  }

  function openLesson(module: EducationModuleSummary) {
    setLesson(null)
    setLessonError('')
    setSaveError('')
    setSelected(module)
  }

  if (expired) return <EmptyState title="Tu sesión terminó" detail="Vuelve a iniciar sesión para continuar con tu avance." action="Iniciar sesión" onClick={onSignIn}/>
  if (loadError) return <EmptyState title="No pudimos cargar Educación" detail={loadError} action="Reintentar" onClick={() => { setLoadError(''); setCatalogAttempt((attempt) => attempt + 1) }}/>
  if (!progress) return <p role="status">Cargando tus temas y tu avance…</p>
  if (!modules.length) return <EmptyState title="Pronto habrá temas para leer" detail="Los contenidos aparecen aquí cuando el equipo los publica."/>

  return <>
    <section className="education-account-progress" aria-label="Tu avance">
      <div><strong>Tu avance</strong><span>{progress.completed} de {progress.total} temas completados</span></div>
      <progress value={progress.percentage} max={100} aria-label="Avance de aprendizaje"/>
      <b>{progress.percentage}%</b>
    </section>
    {selected ? <section className="lesson-card education-reading" aria-label="Lectura">
      <button type="button" className="text-button" disabled={saving} onClick={() => setSelected(null)}>← Todos los temas</button>
      <h2>{selected.title}</h2>
      {lessonError ? <><p role="alert">{lessonError}</p><button className="button button-secondary" onClick={() => { setLessonError(''); setLessonAttempt((attempt) => attempt + 1) }}>Reintentar</button></>
        : lesson ? <>
          <div className="education-lesson-text">{lesson.body}</div>
          {saveError && <p role="alert" className="login-api-notice">{saveError}</p>}
          {completed.has(lesson.id) ? <p className="education-completed" role="status">✓ Tema completado</p>
            : <button className="button button-primary" disabled={saving} onClick={() => void finishLesson()}>{saving ? 'Guardando avance…' : 'Marcar como completado'}</button>}
        </> : <p role="status">Cargando la lectura…</p>}
    </section> : <section className="education-lesson-grid" aria-label="Temas de aprendizaje">
      {modules.map((module, index) => <button type="button" className="education-lesson-tile" key={module.id} onClick={() => openLesson(module)}>
        <span className="education-lesson-icon" aria-hidden="true">{lessonIcons[index % lessonIcons.length]}</span>
        <strong>{module.title}</strong>
        <small>{completed.has(module.id) ? '✓ Completado' : module.category}</small>
      </button>)}
    </section>}
  </>
}
