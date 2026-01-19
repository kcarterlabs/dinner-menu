import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import DinnerMenu from '../src/components/DinnerMenu.vue'
import axios from 'axios'

vi.mock('axios')

describe('DinnerMenu Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the form correctly', () => {
    const wrapper = mount(DinnerMenu)
    
    expect(wrapper.find('h2').text()).toBe('🍲 Generate Dinner Menu')
    expect(wrapper.find('input[type="range"]').exists()).toBe(true)
  })

  it('has default value of 7 days', () => {
    const wrapper = mount(DinnerMenu)
    expect(wrapper.vm.days).toBe(7)
  })

  it('generates menu successfully', async () => {
    const mockMenu = [
      {
        title: 'Pasta',
        ingredients: ['pasta', 'sauce'],
        oven: false,
        stove: true,
        portions: '4'
      },
      {
        title: 'Pizza',
        ingredients: ['dough', 'cheese'],
        oven: true,
        stove: false,
        portions: '2'
      }
    ]

    axios.get.mockResolvedValue({
      data: {
        success: true,
        weather: { forecast: 'sunny' },
        dinner_plan: {
          selected_recipes: mockMenu,
          grocery_list: []
        }
      }
    })

    const wrapper = mount(DinnerMenu)
    
    wrapper.vm.days = 2
    await wrapper.vm.generateMenu()

    expect(axios.get).toHaveBeenCalledWith('/api/dinner-menu', { params: { days: 2 } })
    expect(wrapper.vm.menu).toEqual(mockMenu)
    expect(wrapper.vm.loading).toBe(false)
  })

  it('displays generated menu recipes', async () => {
    const mockMenu = [
      {
        title: 'Test Recipe',
        ingredients: ['test1', 'test2'],
        oven: true,
        stove: true,
        portions: '4'
      }
    ]

    axios.get.mockResolvedValue({
      data: {
        success: true,
        weather: { forecast: 'sunny' },
        dinner_plan: {
          selected_recipes: mockMenu,
          grocery_list: []
        }
      }
    })

    const wrapper = mount(DinnerMenu)
    await wrapper.vm.generateMenu()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Your Dinner Menu')
    expect(wrapper.text()).toContain('Day 1: Test Recipe')
    expect(wrapper.text()).toContain('test1')
    expect(wrapper.text()).toContain('test2')
  })

  it('shows error message on API failure', async () => {
    axios.get.mockResolvedValue({
      data: {
        success: false,
        error: 'Not enough recipes'
      }
    })

    const wrapper = mount(DinnerMenu)
    await wrapper.vm.generateMenu()

    expect(wrapper.vm.errorMessage).toBe('Not enough recipes')
  })

  it('handles network errors', async () => {
    axios.get.mockRejectedValue(new Error('Network error'))

    const wrapper = mount(DinnerMenu)
    await wrapper.vm.generateMenu()

    expect(wrapper.vm.errorMessage).toContain('Network error')
  })

  it('re-rolls individual recipe', async () => {
    const initialMenu = [
      { title: 'Recipe 1', ingredients: [], portions: '4' },
      { title: 'Recipe 2', ingredients: [], portions: '4' },
      { title: 'Recipe 3', ingredients: [], portions: '4' }
    ]

    const newMenu = [
      { title: 'Recipe 1', ingredients: [], portions: '4' },
      { title: 'New Recipe', ingredients: [], portions: '4' },
      { title: 'Recipe 3', ingredients: [], portions: '4' }
    ]

    const mockWeather = { forecast: 'sunny' }
    
    axios.get
      .mockResolvedValueOnce({
        data: {
          success: true,
          weather: mockWeather,
          dinner_plan: { selected_recipes: initialMenu, grocery_list: [] }
        }
      })
    
    axios.post.mockResolvedValueOnce({
        data: {
          success: true,
          weather: mockWeather,
          dinner_plan: { selected_recipes: newMenu, grocery_list: [] }
        }
      })

    const wrapper = mount(DinnerMenu)
    wrapper.vm.days = 3
    
    // Generate initial menu
    await wrapper.vm.generateMenu()
    expect(wrapper.vm.menu).toEqual(initialMenu)

    // Re-roll recipe at index 1
    await wrapper.vm.rerollRecipe(1)

    expect(axios.post).toHaveBeenCalledWith('/api/dinner-menu', {
      days: 3,
      reroll_index: 1,
      current_menu: initialMenu,
      weather: mockWeather
    })
    expect(wrapper.vm.menu).toEqual(newMenu)
  })

  it('shows loading state during generation', async () => {
    axios.get.mockImplementation(() => new Promise(resolve => {
      setTimeout(() => resolve({
        data: {
          success: true,
          weather: {},
          dinner_plan: { selected_recipes: [], grocery_list: [] }
        }
      }), 100)
    }))

    const wrapper = mount(DinnerMenu)
    
    const promise = wrapper.vm.generateMenu()
    expect(wrapper.vm.loading).toBe(true)
    
    await promise
    expect(wrapper.vm.loading).toBe(false)
  })

  it('displays re-roll button for each recipe', async () => {
    const mockMenu = [
      { title: 'Recipe 1', ingredients: [], portions: '4' },
      { title: 'Recipe 2', ingredients: [], portions: '4' }
    ]

    axios.get.mockResolvedValue({
      data: {
        success: true,
        weather: {},
        dinner_plan: { selected_recipes: mockMenu, grocery_list: [] }
      }
    })

    const wrapper = mount(DinnerMenu)
    await wrapper.vm.generateMenu()
    await wrapper.vm.$nextTick()

    const rerollButtons = wrapper.findAll('button').filter(btn => btn.text().includes('🔄'))
    // Should have 2 re-roll buttons (one for each recipe) plus 1 generate button
    expect(rerollButtons.length).toBe(2)
  })

  it('clears error message on successful generation', async () => {
    axios.get
      .mockRejectedValueOnce(new Error('First error'))
      .mockResolvedValueOnce({
        data: {
          success: true,
          weather: {},
          dinner_plan: { selected_recipes: [], grocery_list: [] }
        }
      })

    const wrapper = mount(DinnerMenu)
    
    await wrapper.vm.generateMenu()
    expect(wrapper.vm.errorMessage).toBeTruthy()

    await wrapper.vm.generateMenu()
    expect(wrapper.vm.errorMessage).toBe('')
  })

  it('preserves recipe order when re-rolling', async () => {
    const initialMenu = [
      { title: 'Day 1 Recipe', ingredients: ['a'], portions: '2' },
      { title: 'Day 2 Recipe', ingredients: ['b'], portions: '2' },
      { title: 'Day 3 Recipe', ingredients: ['c'], portions: '2' },
      { title: 'Day 4 Recipe', ingredients: ['d'], portions: '2' }
    ]

    const menuAfterReroll = [
      { title: 'Day 1 Recipe', ingredients: ['a'], portions: '2' },
      { title: 'NEW Recipe', ingredients: ['new'], portions: '2' },
      { title: 'Day 3 Recipe', ingredients: ['c'], portions: '2' },
      { title: 'Day 4 Recipe', ingredients: ['d'], portions: '2' }
    ]

    axios.get.mockResolvedValueOnce({
      data: {
        success: true,
        weather: { forecast: 'sunny' },
        dinner_plan: { selected_recipes: initialMenu, grocery_list: [] }
      }
    })

    axios.post.mockResolvedValueOnce({
      data: {
        success: true,
        weather: { forecast: 'sunny' },
        dinner_plan: { selected_recipes: menuAfterReroll, grocery_list: [] }
      }
    })

    const wrapper = mount(DinnerMenu)
    wrapper.vm.days = 4

    // Generate initial menu
    await wrapper.vm.generateMenu()
    expect(wrapper.vm.menu.length).toBe(4)
    expect(wrapper.vm.menu[1].title).toBe('Day 2 Recipe')

    // Re-roll recipe at index 1 (Day 2)
    await wrapper.vm.rerollRecipe(1)

    // Verify the API was called with correct parameters
    expect(axios.post).toHaveBeenCalledWith('/api/dinner-menu', {
      days: 4,
      reroll_index: 1,
      current_menu: initialMenu,
      weather: { forecast: 'sunny' }
    })

    // Verify menu length stays the same
    expect(wrapper.vm.menu.length).toBe(4)
    
    // Verify only index 1 changed
    expect(wrapper.vm.menu[0].title).toBe('Day 1 Recipe')
    expect(wrapper.vm.menu[1].title).toBe('NEW Recipe')
    expect(wrapper.vm.menu[2].title).toBe('Day 3 Recipe')
    expect(wrapper.vm.menu[3].title).toBe('Day 4 Recipe')
  })

  it('displays grocery list when menu is generated', async () => {
    const mockMenu = [
      { title: 'Pasta', ingredients: ['pasta', 'tomato sauce', 'garlic'], portions: '4' },
      { title: 'Salad', ingredients: ['lettuce', 'tomato sauce', 'olive oil'], portions: '2' }
    ]

    const mockGroceryList = [
      { ingredient: 'garlic', count: 1 },
      { ingredient: 'lettuce', count: 1 },
      { ingredient: 'olive oil', count: 1 },
      { ingredient: 'pasta', count: 1 },
      { ingredient: 'tomato sauce', count: 2 }
    ]

    axios.get.mockResolvedValue({
      data: {
        success: true,
        weather: { forecast: 'sunny' },
        dinner_plan: {
          selected_recipes: mockMenu,
          grocery_list: mockGroceryList
        }
      }
    })

    const wrapper = mount(DinnerMenu)
    await wrapper.vm.generateMenu()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.groceryList).toEqual(mockGroceryList)
    expect(wrapper.text()).toContain('Shopping List')
    expect(wrapper.text()).toContain('tomato sauce')
    expect(wrapper.text()).toContain('2')
  })
})
