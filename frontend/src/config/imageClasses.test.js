import test from 'node:test'
import assert from 'node:assert/strict'
import { IMAGE_CLASS_MAPPING, IMAGE_CLASS_ORDER, SEPARATE_MODEL_OUTPUTS } from './imageClasses.js'

test('mapping exactly matches the frozen seven-class model order', () => {
  assert.deepEqual(Object.keys(IMAGE_CLASS_MAPPING), IMAGE_CLASS_ORDER)
  assert.deepEqual(IMAGE_CLASS_ORDER, ['HEALTHY', 'LSD', 'RINGWORM', 'FMD', 'IBK', 'PEDICULOSIS', 'DERMATOPHILOSIS'])
})

test('each image class has translated display name and characteristics', () => {
  for (const item of Object.values(IMAGE_CLASS_MAPPING)) {
    for (const language of ['en', 'hi', 'mr']) {
      assert.ok(item.displayName[language])
      assert.ok(item.characteristics[language].length)
    }
    assert.ok(['LOW', 'MEDIUM', 'HIGH'].includes(item.severity))
  }
})

test('mastitis remains a separate available output', () => {
  assert.equal(SEPARATE_MODEL_OUTPUTS.mastitis.availability, 'available')
  assert.equal(IMAGE_CLASS_MAPPING.MASTITIS, undefined)
})
