import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import Card from '../components/Card.jsx'
import Loader from '../components/Loader.jsx'
import ErrorBox from '../components/ErrorBox.jsx'

function renderMarkdown(md) {
  // Minimal Markdown rendering for headings, paragraphs, lists, inline code, and code blocks.
  const lines = md.split('\n')
  const out = []
  let inCode = false
  let buffer = []
  let listItems = []

  const flushList = () => {
    if (listItems.length) {
      out.push(<ul key={`ul-${out.length}`}>{listItems.map((li, i) => <li key={i}>{li}</li>)}</ul>)
      listItems = []
    }
  }

  for (const raw of lines) {
    const line = raw

    if (line.startsWith('```')) {
      flushList()
      if (inCode) {
        out.push(<pre key={`pre-${out.length}`}>{buffer.join('\n')}</pre>)
        buffer = []
        inCode = false
      } else {
        inCode = true
      }
      continue
    }
    if (inCode) {
      buffer.push(line)
      continue
    }

    if (line.startsWith('### ')) {
      flushList()
      out.push(<h3 key={`h3-${out.length}`}>{line.slice(4)}</h3>)
    } else if (line.startsWith('## ')) {
      flushList()
      out.push(<h2 key={`h2-${out.length}`}>{line.slice(3)}</h2>)
    } else if (line.startsWith('# ')) {
      flushList()
      out.push(<h1 key={`h1-${out.length}`}>{line.slice(2)}</h1>)
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      listItems.push(formatInline(line.slice(2)))
    } else if (line.trim() === '') {
      flushList()
    } else {
      flushList()
      out.push(<p key={`p-${out.length}`}>{formatInline(line)}</p>)
    }
  }
  flushList()
  return out
}

function formatInline(text) {
  const parts = []
  let i = 0
  let buffer = ''
  const flush = (key) => {
    if (buffer) {
      parts.push(<span key={`t-${key}-${i}`}>{buffer}</span>)
      buffer = ''
    }
  }
  while (i < text.length) {
    if (text[i] === '`') {
      const end = text.indexOf('`', i + 1)
      if (end > -1) {
        flush(parts.length)
        parts.push(<code key={`c-${parts.length}`}>{text.slice(i + 1, end)}</code>)
        i = end + 1
        continue
      }
    }
    buffer += text[i]
    i += 1
  }
  flush(parts.length)
  return parts
}

export default function Report() {
  const { slug } = useParams()
  const { data, loading, error } = useApi(api.reports, [])
  const [active, setActive] = useState(slug || null)

  useEffect(() => {
    if (!active && data && data.length) setActive(data[0].slug)
  }, [data, active])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  if (!data || !data.length) return <p className="text-slate-400 italic">No reports available.</p>

  const current = data.find((r) => r.slug === active) || data[0]

  return (
    <div className="space-y-4">
      <nav className="flex gap-2 flex-wrap">
        {data.map((r) => (
          <Link
            key={r.slug}
            to={`/report/${r.slug}`}
            onClick={() => setActive(r.slug)}
            className={`px-3 py-1.5 rounded-md text-sm ${
              r.slug === current.slug
                ? 'bg-accent/20 text-accent'
                : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            {r.title}
          </Link>
        ))}
      </nav>

      <Card title={current.title}>
        <div className="markdown max-w-none text-slate-200">
          {renderMarkdown(current.content)}
        </div>
      </Card>
    </div>
  )
}
