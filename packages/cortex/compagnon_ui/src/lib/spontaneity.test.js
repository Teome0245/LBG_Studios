import test from 'node:test'
import assert from 'node:assert/strict'
import { toToastPayload, spontaneityApiUrl } from './spontaneity.js'

test('toToastPayload: conserve spontané + themes', () => {
  const toast = toToastPayload({
    offer: true,
    id: 'self:curiosity',
    message: 'Et si on testait un toast vivant ?',
    kind: 'self_drive',
    offerType: 'studio',
    intents: [{ id: 'a', label: 'A', sourceText: 'fais un selfcheck LAN' }],
    spontaneous: true,
    themes: ['toast'],
    evolution_seed: 'seed x',
    spice_mode: 'full',
  })
  assert.equal(toast.spontaneous, true)
  assert.deepEqual(toast.themes, ['toast'])
  assert.equal(toast.evolution_seed, 'seed x')
  assert.equal(toast.primary.id, 'a')
})

test('spontaneityApiUrl: chemin relatif hors prod vite', () => {
  assert.equal(spontaneityApiUrl('/spontaneity/propose'), '/spontaneity/propose')
})
