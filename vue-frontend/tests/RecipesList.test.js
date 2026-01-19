import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import RecipesList from '../src/components/RecipesList.vue'
import axios from 'axios'

vi.mock('axios')

describe('RecipesList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    const wrapper = mount(RecipesList)
    expect(wrapper.find('.loading').exists()).toBe(true)
  })

  it('loads and displays recipes', async () => {
    const mockRecipes = [
      {
        title: 'Spaghetti',
        ingredients: ['pasta', 'sauce'],
        oven: false,
        stove: true,
        portions: '4',
        date: '2026-01-18'
      },
      {
        title: 'Pizza',
        ingredients: ['dough', 'cheese'],
        oven: true,
        stove: false,
        portions: '2',
        date: '2026-01-17'
      }
    ]

    axios.get.mockResolvedValue({ data: { recipes: mockRecipes } })

    const wrapper = mount(RecipesList)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.vm.recipes).toEqual(mockRecipes)
    expect(wrapper.vm.loading).toBe(false)
    expect(wrapper.findAll('.recipe-card').length).toBe(2)
  })

  it('displays recipe details correctly', async () => {
    const mockRecipes = [
      {
        title: 'Test Recipe',
        ingredients: ['ingredient1', 'ingredient2'],
        oven: true,
        stove: true,
        portions: '4',
        date: '2026-01-18'
      }
    ]

    axios.get.mockResolvedValue({ data: { recipes: mockRecipes } })

    const wrapper = mount(RecipesList)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    const card = wrapper.find('.recipe-card')
    expect(card.text()).toContain('Test Recipe')
    expect(card.text()).toContain('ingredient1')
    expect(card.text()).toContain('ingredient2')
    expect(card.text()).toContain('4 portions')
  })

  it('shows badges for oven and stove', async () => {
    const mockRecipes = [
      {
        title: 'Test',
        ingredients: [],
        oven: true,
        stove: true,
        portions: '2',
        date: '2026-01-18'
      }
    ]

    axios.get.mockResolvedValue({ data: { recipes: mockRecipes } })

    const wrapper = mount(RecipesList)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.find('.badge-oven').exists()).toBe(true)
    expect(wrapper.find('.badge-stove').exists()).toBe(true)
  })

  it('shows empty state when no recipes', async () => {
    axios.get.mockResolvedValue({ data: { recipes: [] } })

    const wrapper = mount(RecipesList)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.find('.alert-info').text()).toContain('No recipes found')
  })

  it('deletes recipe with confirmation', async () => {
    const mockRecipes = [
      {
        title: 'Recipe 1',
        ingredients: [],
        oven: false,
        stove: false,
        portions: '4',
        date: '2026-01-18'
      }
    ]

    axios.get.mockResolvedValue({ data: { recipes: mockRecipes } })
    axios.delete.mockResolvedValue({ data: { success: true } })

    // Mock window.confirm
    global.confirm = vi.fn(() => true)

    const wrapper = mount(RecipesList)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    await wrapper.vm.deleteRecipe(0)

    expect(axios.delete).toHaveBeenCalledWith('/api/recipes/0')
    expect(axios.get).toHaveBeenCalledTimes(2) // Initial load + reload after delete
  })

  it('cancels delete when user declines confirmation', async () => {
    const mockRecipes = [{ title: 'Test', ingredients: [], portions: '4', date: '2026-01-18' }]

    axios.get.mockResolvedValue({ data: { recipes: mockRecipes } })
    global.confirm = vi.fn(() => false)

    const wrapper = mount(RecipesList)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    await wrapper.vm.deleteRecipe(0)

    expect(axios.delete).not.toHaveBeenCalled()
  })

  it('handles API errors gracefully', async () => {
    axios.get.mockRejectedValue(new Error('Network error'))

    const wrapper = mount(RecipesList)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.vm.recipes).toEqual([])
    expect(wrapper.vm.loading).toBe(false)
  })
})
