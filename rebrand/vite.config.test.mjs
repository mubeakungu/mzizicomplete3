import assert from 'node:assert/strict'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

globalThis.__dirname = path.dirname(fileURLToPath(import.meta.url))
const { default: config } = await import('./vite.config.js')
const gtm = config.plugins.find(({ name }) => name === 'google-tag-manager')

test('Google Tag Manager only applies to production builds', () => {
    assert.ok(gtm, 'Google Tag Manager plugin is missing')
    assert.equal(gtm.apply({}, { command: 'build', mode: 'production' }), true)
    assert.equal(gtm.apply({}, { command: 'serve', mode: 'development' }), false)
    assert.equal(gtm.apply({}, { command: 'build', mode: 'development' }), false)
})

test('Google Tag Manager injects the required script and noscript tags', () => {
    assert.ok(gtm, 'Google Tag Manager plugin is missing')

    const tags = gtm.transformIndexHtml.handler()
    const script = tags.find(({ tag }) => tag === 'script')
    const noscript = tags.find(({ tag }) => tag === 'noscript')

    assert.equal(script.injectTo, 'head-prepend')
    assert.match(script.children, /GTM-MZ825NFC/)
    assert.equal(noscript.injectTo, 'body-prepend')
    assert.match(noscript.children, /GTM-MZ825NFC/)
})
