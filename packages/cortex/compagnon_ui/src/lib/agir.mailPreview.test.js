import test from 'node:test'
import assert from 'node:assert/strict'
import {
  extractMailPreviewMessages,
  formatMailPreviewLines,
  summarizeRouteResult,
} from './agir.js'

function mailRoutePayload(messages, { outcome = 'ok', matched_count } = {}) {
  return {
    ok: true,
    result: {
      routed_to: 'agent.desktop',
      output: {
        ok: true,
        outcome,
        messages,
        matched_count: matched_count ?? messages.length,
        desktop_target_host: '192.168.0.10',
      },
    },
  }
}

test('extrait les messages IMAP du payload route', () => {
  const msgs = extractMailPreviewMessages(
    mailRoutePayload([{ from: 'a@x.test', subject: 'Bonjour', body_preview: 'Hi' }]),
  )
  assert.equal(msgs.length, 1)
  assert.equal(msgs[0].subject, 'Bonjour')
})

test('résume le dry-run avec rappel Réel', () => {
  const text = summarizeRouteResult(
    mailRoutePayload(
      [
        {
          uid: '(dry-run)',
          from: 'expéditeur@exemple.invalid',
          subject: '… filtre (simulation)',
          body_preview: '[dry-run] Aucune connexion IMAP',
        },
      ],
      { outcome: 'dry_run' },
    ),
    'dry_run',
  )
  assert.match(text, /Dry-run · ok/)
  assert.match(text, /aperçu IMAP · 1 message/)
  assert.match(text, /simulation/i)
  assert.match(text, /Réel/)
})

test('résume le réel avec le compte de mails', () => {
  const text = summarizeRouteResult(
    mailRoutePayload(
      [
        { from: 'boss@co', subject: 'Facture', date: 'Mon', body_preview: 'Merci' },
        { from: 'hr@co', subject: 'Congés', body_preview: 'OK' },
      ],
      { outcome: 'ok' },
    ),
    'real',
  )
  assert.match(text, /Réel · ok/)
  assert.match(text, /aperçu IMAP · 2 messages/)
  assert.equal(/simulation/i.test(text), false)
})

test('formate des lignes lisibles', () => {
  const lines = formatMailPreviewLines([
    { from: 'a@x', subject: 'Sujet', date: 'Tue', body_preview: 'Corps court' },
  ])
  assert.match(lines[0], /1\. a@x — Sujet \(Tue\)/)
  assert.match(lines[0], /Corps court/)
})
