import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

if (!Object.fromEntries) {
  Object.fromEntries = ((entries: Iterable<readonly [PropertyKey, unknown]>) => {
    const obj: Record<PropertyKey, unknown> = {}
    for (const [key, value] of entries) obj[key] = value
    return obj
  }) as ObjectConstructor['fromEntries']
}

if (!Array.prototype.flat) {
  ;(Array.prototype as any).flat = function(depth = 1) {
    const flatten = (items: unknown[], level: number): unknown[] =>
      level > 0
        ? items.reduce<unknown[]>((acc, item) => acc.concat(Array.isArray(item) ? flatten(item, level - 1) : item), [])
        : items.slice()
    return flatten(this as unknown[], Number(depth) || 0)
  }
}

if (!Array.prototype.flatMap) {
  ;(Array.prototype as any).flatMap = function(callback: any, thisArg: any) {
    return this.map(callback, thisArg).flat()
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter basename="/admin">
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
