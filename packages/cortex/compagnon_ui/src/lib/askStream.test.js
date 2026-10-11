/**
 * node --test src/lib/askStream.test.js
 */
import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { createSSEDecoder, parseSSE } from './askStream.js'

describe('askStream SSE decoder', () => {
  it('parseSSE lit start + delta + done', () => {
    const raw =
      'event: start\ndata: {"ok":true}\n\n' +
      'event: delta\ndata: {"content":"Bon"}\n\n' +
      'event: delta\ndata: {"content":"jour"}\n\n' +
      'event: done\ndata: {"ok":true,"response":{"content":"Bonjour"}}\n\n'
    const frames = parseSSE(raw)
    assert.equal(frames.length, 4)
    assert.equal(frames[0].event, 'start')
    assert.equal(frames[1].event, 'delta')
    assert.equal(frames[3].event, 'done')
  })

  it('createSSEDecoder empile les chunks partiels', () => {
    const sse = createSSEDecoder()
    assert.deepEqual(sse.push('event: start\ndata: {"ok":'), [])
    const a = sse.push('true}\n\nevent: delta\ndata: {"content":"x"}\n\n')
    assert.equal(a.length, 2)
    assert.equal(a[0].event, 'start')
    assert.equal(a[1].event, 'delta')
  })
})
