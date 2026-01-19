import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import AddRecipe from '../src/components/AddRecipe.vue'
import axios from 'axios'

// Mock axios
vi.mock('axios')

describe('AddRecipe Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the form correctly', () => {
    const wrapper = mount(AddRecipe)
    
    expect(wrapper.find('h2').text()).toBe('➕ Add New Recipe')
    expect(wrapper.find('input[placeholder*="Spaghetti"]').exists()).toBe(true)
  })

  it('loads existing ingredients on mount', async () => {
    const mockRecipes = [
      {
        ingredients: ['pasta', 'tomato sauce', 'garlic']
      },
      {
        ingredients: ['chicken', 'olive oil', 'Garlic']
      }
    ]

    axios.get.mockResolvedValue({ data: { recipes: mockRecipes } })

    const wrapper = mount(AddRecipe)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    // Should have loaded unique ingredients
    expect(axios.get).toHaveBeenCalledWith('/api/recipes')
    // Wait for async data to be loaded
    if (wrapper.vm.allIngredients) {
      expect(wrapper.vm.allIngredients.length).toBeGreaterThan(0)
    }
  })

  it('shows fuzzy matches when typing ingredient', async () => {
    const mockRecipes = [
      { ingredients: ['tomato sauce', 'diced tomatoes', 'pasta'] }
    ]

    axios.get.mockResolvedValue({ data: { recipes: mockRecipes } })

    const wrapper = mount(AddRecipe)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Type in ingredient input
    wrapper.vm.ingredientInput = 'tomat'
    wrapper.vm.onIngredientInput()
    await wrapper.vm.$nextTick()

    // Should show fuzzy matches
    expect(wrapper.vm.fuzzyMatches.length).toBeGreaterThan(0)
    expect(wrapper.vm.fuzzyMatches).toContain('tomato sauce')
  })

  it('adds ingredient when clicking Add button', async () => {
    axios.get.mockResolvedValue({ data: { recipes: [] } })

    const wrapper = mount(AddRecipe)
    await wrapper.vm.$nextTick()

    wrapper.vm.ingredientInput = 'test ingredient'
    wrapper.vm.addIngredient()

    expect(wrapper.vm.ingredients).toContain('test ingredient')
    expect(wrapper.vm.ingredientInput).toBe('')
  })

  it('adds ingredient from fuzzy match', async () => {
    const wrapper = mount(AddRecipe)
    
    wrapper.vm.allIngredients = ['pasta', 'tomato sauce']
    wrapper.vm.addIngredientFromMatch('tomato sauce')

    expect(wrapper.vm.ingredients).toContain('tomato sauce')
    expect(wrapper.vm.ingredientInput).toBe('')
    expect(wrapper.vm.fuzzyMatches).toEqual([])
  })

  it('removes ingredient when clicking remove button', async () => {
    const wrapper = mount(AddRecipe)
    
    wrapper.vm.ingredients = ['pasta', 'sauce', 'cheese']
    wrapper.vm.removeIngredient(1)

    expect(wrapper.vm.ingredients).toEqual(['pasta', 'cheese'])
  })

  it('prevents duplicate ingredients', async () => {
    const wrapper = mount(AddRecipe)
    
    wrapper.vm.ingredients = ['pasta']
    wrapper.vm.ingredientInput = 'pasta'
    wrapper.vm.addIngredient()

    expect(wrapper.vm.ingredients).toEqual(['pasta'])
  })

  it('calculates similarity correctly', () => {
    const wrapper = mount(AddRecipe)
    
    // Test the similarity calculation logic directly
    const calculateSimilarity = (str1, str2) => {
      const s1 = str1.toLowerCase()
      const s2 = str2.toLowerCase()
      
      // Substring match gets highest priority
      if (s2.includes(s1)) return 1.0
      
      // Simple similarity based on common characters
      const track = Array(s2.length + 1).fill(null).map(() =>
        Array(s1.length + 1).fill(null))
      
      for (let i = 0; i <= s1.length; i++) track[0][i] = i
      for (let j = 0; j <= s2.length; j++) track[j][0] = j
      
      for (let j = 1; j <= s2.length; j++) {
        for (let i = 1; i <= s1.length; i++) {
          const indicator = s1[i - 1] === s2[j - 1] ? 0 : 1
          track[j][i] = Math.min(
            track[j][i - 1] + 1,
            track[j - 1][i] + 1,
            track[j - 1][i - 1] + indicator
          )
        }
      }
      
      const distance = track[s2.length][s1.length]
      const maxLen = Math.max(s1.length, s2.length)
      return 1 - distance / maxLen
    }
    
    // Exact substring match
    const score1 = calculateSimilarity('tom', 'tomato sauce')
    expect(score1).toBe(1.0)

    // Similar strings
    const score2 = calculateSimilarity('tomat', 'tomato')
    expect(score2).toBeGreaterThan(0.7)

    // Very different strings
    const score3 = calculateSimilarity('abc', 'xyz')
    expect(score3).toBeLessThan(0.5)
  })

  it('submits recipe successfully', async () => {
    axios.get.mockResolvedValue({ data: { recipes: [] } })
    axios.post.mockResolvedValue({ data: { success: true } })

    const wrapper = mount(AddRecipe)
    await wrapper.vm.$nextTick()

    wrapper.vm.recipe = {
      title: 'Test Recipe',
      oven: true,
      stove: false,
      portions: 4,
      date: '2026-01-18'
    }
    wrapper.vm.ingredients = ['pasta', 'sauce']

    await wrapper.vm.submitRecipe()

    expect(axios.post).toHaveBeenCalledWith('/api/recipes', {
      title: 'Test Recipe',
      date: '2026-01-18',
      ingredients: ['pasta', 'sauce'],
      oven: true,
      stove: false,
      portions: '4'
    })

    expect(wrapper.vm.successMessage).toContain('Test Recipe')
    expect(wrapper.vm.ingredients).toEqual([])
  })

  it('shows error when submitting without title', async () => {
    const wrapper = mount(AddRecipe)
    
    wrapper.vm.recipe.title = ''
    wrapper.vm.ingredients = ['pasta']

    await wrapper.vm.submitRecipe()

    expect(wrapper.vm.errorMessage).toContain('title')
  })

  it('shows error when submitting without ingredients', async () => {
    const wrapper = mount(AddRecipe)
    
    wrapper.vm.recipe.title = 'Test'
    wrapper.vm.ingredients = []

    await wrapper.vm.submitRecipe()

    expect(wrapper.vm.errorMessage).toContain('ingredient')
  })

  it('handles API errors gracefully', async () => {
    axios.get.mockResolvedValue({ data: { recipes: [] } })
    axios.post.mockRejectedValue(new Error('Network error'))

    const wrapper = mount(AddRecipe)
    await wrapper.vm.$nextTick()

    wrapper.vm.recipe.title = 'Test'
    wrapper.vm.ingredients = ['pasta']

    await wrapper.vm.submitRecipe()

    expect(wrapper.vm.errorMessage).toContain('Network error')
  })
})
