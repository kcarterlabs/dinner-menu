import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HomePage from '../src/components/HomePage.vue'

describe('HomePage Component', () => {
  it('renders welcome message', () => {
    const wrapper = mount(HomePage)
    expect(wrapper.text()).toContain('Welcome to Dinner Menu')
  })

  it('displays feature list', () => {
    const wrapper = mount(HomePage)
    const text = wrapper.text()
    
    expect(text).toContain('Manage your recipe collection')
    expect(text).toContain('Smart ingredient fuzzy search')
    expect(text).toContain('Generate dinner menus')
    expect(text).toContain('Real-time autocomplete')
  })

  it('shows pro tip section', () => {
    const wrapper = mount(HomePage)
    expect(wrapper.text()).toContain('Pro Tip')
    expect(wrapper.text()).toContain('similar ingredients')
  })
})
