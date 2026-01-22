import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import axios from 'axios'
import App from '../src/App.vue'
import HomePage from '../src/components/HomePage.vue'
import RecipesList from '../src/components/RecipesList.vue'
import AddRecipe from '../src/components/AddRecipe.vue'
import DinnerMenu from '../src/components/DinnerMenu.vue'

// Mock axios globally
vi.mock('axios')

describe('App Component', () => {
  let wrapper

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks()
    
    // Mock axios.get to prevent real API calls
    axios.get.mockResolvedValue({ 
      data: { 
        recipes: [] 
      } 
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
      wrapper = null
    }
  })

  it('renders the header', () => {
    wrapper = mount(App)
    expect(wrapper.find('h1').text()).toContain('Dinner Menu')
  })

  it('renders navigation buttons', () => {
    wrapper = mount(App)
    const buttons = wrapper.findAll('.nav button')
    
    expect(buttons.length).toBe(4)
    expect(buttons[0].text()).toContain('Home')
    expect(buttons[1].text()).toContain('Recipes')
    expect(buttons[2].text()).toContain('Add Recipe')
    expect(buttons[3].text()).toContain('Dinner Menu')
  })

  it('starts on home page', () => {
    wrapper = mount(App)
    expect(wrapper.vm.currentPage).toBe('home')
    expect(wrapper.findComponent(HomePage).exists()).toBe(true)
  })

  it('switches to recipes page when clicked', async () => {
    wrapper = mount(App)
    const buttons = wrapper.findAll('.nav button')
    
    await buttons[1].trigger('click')
    
    expect(wrapper.vm.currentPage).toBe('recipes')
  })

  it('switches to add recipe page when clicked', async () => {
    wrapper = mount(App)
    const buttons = wrapper.findAll('.nav button')
    
    await buttons[2].trigger('click')
    
    expect(wrapper.vm.currentPage).toBe('add')
  })

  it('switches to dinner menu page when clicked', async () => {
    wrapper = mount(App)
    const buttons = wrapper.findAll('.nav button')
    
    await buttons[3].trigger('click')
    
    expect(wrapper.vm.currentPage).toBe('menu')
  })

  it('highlights active page button', async () => {
    wrapper = mount(App)
    const buttons = wrapper.findAll('.nav button')
    
    // Home should be active initially
    expect(buttons[0].classes()).toContain('active')
    
    // Click recipes
    await buttons[1].trigger('click')
    await wrapper.vm.$nextTick()
    
    expect(buttons[1].classes()).toContain('active')
    expect(buttons[0].classes()).not.toContain('active')
  })

  it('computes current component correctly', () => {
    wrapper = mount(App)
    
    wrapper.vm.currentPage = 'home'
    expect(wrapper.vm.currentComponent).toBe('HomePage')
    
    wrapper.vm.currentPage = 'recipes'
    expect(wrapper.vm.currentComponent).toBe('RecipesList')
    
    wrapper.vm.currentPage = 'add'
    expect(wrapper.vm.currentComponent).toBe('AddRecipe')
    
    wrapper.vm.currentPage = 'menu'
    expect(wrapper.vm.currentComponent).toBe('DinnerMenu')
  })
})
