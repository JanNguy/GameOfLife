import { useState, useRef, useEffect } from 'react'
import type { KeyboardEvent } from 'react'
import './App.css'

type LineType = 'command' | 'output' | 'error' | 'info'

interface Line {
  text: string
  type: LineType
}

const REMOTE_COMMANDS = ['run', 'clean', 'fclean', 'data', 'setup', 'model']

const HELP_LINES: Line[] = [
  { text: 'available commands:', type: 'info' },
  { text: '  setup   — run the data pipeline', type: 'info' },
  { text: '  run     — run a scenario: run <nb_agent> <scenario>', type: 'info' },
  { text: '  data    — rerun the data pipeline', type: 'info' },
  { text: '  model   — show / select the prediction model', type: 'info' },
  { text: '  clean   — remove generated game files', type: 'info' },
  { text: '  fclean  — clean the entire project', type: 'info' },
  { text: '  clear   — clear the terminal', type: 'info' },
  { text: '  help    — show this help', type: 'info' },
]

const BOOT_LINES: Line[] = [
  { text: 'GameOfLife Terminal', type: 'info' },
  { text: 'type "help" to see available commands', type: 'info' },
]

function App() {
  const [lines, setLines] = useState<Line[]>(BOOT_LINES)
  const [input, setInput] = useState('')
  const [running, setRunning] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'instant' })
  }, [lines])

  const append = (text: string, type: LineType = 'output') =>
    setLines(prev => [...prev, { text, type }])

  const execute = (raw: string) => {
    const cmd = raw.trim()
    if (!cmd) return

    if (cmd === 'clear') {
      setLines([])
      return
    }

    append(`> ${cmd}`, 'command')

    if (cmd === 'help') {
      setLines(prev => [...prev, ...HELP_LINES])
      return
    }

    const parts = cmd.split(/\s+/)
    const baseCmd = parts[0]

    if (!REMOTE_COMMANDS.includes(baseCmd)) {
      append(`unknown command: '${cmd}'. Type 'help'.`, 'error')
      return
    }

    setRunning(true)
    const url = parts.length > 1
      ? `/exec/${baseCmd}/${parts.slice(1).join('/')}`
      : `/exec/${baseCmd}`
    const es = new EventSource(url)

    es.onmessage = (e: MessageEvent<string>) => {
      if (e.data === '__END__') {
        es.close()
        setRunning(false)
        return
      }
      append(e.data, e.data.startsWith('[exit') ? 'info' : 'output')
    }

    es.onerror = () => {
      append('[connexion perdue — le serveur est-il lancé ?]', 'error')
      es.close()
      setRunning(false)
    }
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !running) {
      execute(input)
      setInput('')
    }
  }

  return (
    <div className="terminal" onClick={() => inputRef.current?.focus()}>
      <div className="output">
        {lines.map((line, i) => (
          <div key={i} className={`line ${line.type}`}>
            {line.text}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="input-row">
        <span className="prompt">{'>'}</span>
        <input
          ref={inputRef}
          className="input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={running}
          autoFocus
          spellCheck={false}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
        />
        {running && <span className="cursor" />}
      </div>
    </div>
  )
}

export default App
