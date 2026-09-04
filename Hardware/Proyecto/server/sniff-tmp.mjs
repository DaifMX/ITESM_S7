import { SerialPort } from 'serialport'

const path = process.argv[2]
const baud = Number(process.argv[3] ?? 115200)
console.log(`abriendo ${path} @ ${baud}`)

const port = new SerialPort({ path, baudRate: baud, autoOpen: false })
let bytes = 0
const chunks = []

port.open((err) => {
  if (err) { console.log('ERROR AL ABRIR:', err.message); process.exit(1) }
  console.log('abierto OK')
  port.set({ dtr: false, rts: false }, (e) => console.log('set dtr/rts false:', e ? e.message : 'ok'))
})
port.on('data', (d) => { bytes += d.length; if (chunks.length < 12) chunks.push(d) })
port.on('error', (e) => console.log('ERROR:', e.message))

setTimeout(() => {
  const buf = Buffer.concat(chunks)
  console.log(`\n>>> bytes recibidos en 6s: ${bytes}`)
  console.log('>>> hex:', buf.subarray(0, 120).toString('hex'))
  console.log('>>> texto:', JSON.stringify(buf.subarray(0, 200).toString('utf8')))
  process.exit(0)
}, 6000)
