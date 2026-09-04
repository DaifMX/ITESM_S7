/**
 * Arranca la API de Express y el dashboard de Vite a la vez.
 *
 * Sin dependencias extra: lanza los dos procesos, mezcla su salida y se
 * asegura de que Ctrl-C no deje ninguno huérfano.
 */
import { spawn } from 'node:child_process'

const tasks = [
  { name: 'api', args: ['--dir', 'server', 'start'], color: '\x1b[36m' },
  { name: 'ui ', args: ['--dir', 'dashboard', 'dev'], color: '\x1b[35m' },
]

const reset = '\x1b[0m'
const children = []
let shuttingDown = false

for (const task of tasks) {
  const child = spawn('pnpm', task.args, { stdio: ['ignore', 'pipe', 'pipe'] })
  children.push(child)

  const prefix = `${task.color}[${task.name}]${reset} `
  for (const stream of [child.stdout, child.stderr]) {
    stream.setEncoding('utf8')
    let partial = ''
    stream.on('data', (chunk) => {
      const lines = (partial + chunk).split('\n')
      partial = lines.pop() ?? ''
      for (const line of lines) console.log(prefix + line)
    })
  }

  child.on('exit', (code) => {
    if (shuttingDown) return
    console.log(`${prefix}terminó con código ${code}`)
    shutdown(code ?? 0)
  })
}

function shutdown(code) {
  if (shuttingDown) return
  shuttingDown = true
  for (const child of children) child.kill('SIGTERM')
  setTimeout(() => process.exit(code), 300).unref()
}

process.on('SIGINT', () => shutdown(0))
process.on('SIGTERM', () => shutdown(0))
