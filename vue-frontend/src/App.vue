<template>
  <div>
    <header class="header">
      <h1>🍽️ Dinner Menu</h1>
      <p>Vue.js Edition with Smart Ingredient Matching</p>
    </header>

    <nav class="nav">
      <button @click="currentPage = 'home'" :class="{ active: currentPage === 'home' }">
        🏠 Home
      </button>
      <button @click="currentPage = 'recipes'" :class="{ active: currentPage === 'recipes' }">
        📋 Recipes
      </button>
      <button @click="currentPage = 'add'" :class="{ active: currentPage === 'add' }">
        ➕ Add Recipe
      </button>
      <button @click="currentPage = 'menu'" :class="{ active: currentPage === 'menu' }">
        🍲 Dinner Menu
      </button>
    </nav>

    <div class="container">
      <component :is="currentComponent" />
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import HomePage from './components/HomePage.vue'
import RecipesList from './components/RecipesList.vue'
import AddRecipe from './components/AddRecipe.vue'
import DinnerMenu from './components/DinnerMenu.vue'

export default {
  name: 'App',
  components: {
    HomePage,
    RecipesList,
    AddRecipe,
    DinnerMenu
  },
  setup() {
    const currentPage = ref('home')
    
    const currentComponent = computed(() => {
      const pages = {
        home: 'HomePage',
        recipes: 'RecipesList',
        add: 'AddRecipe',
        menu: 'DinnerMenu'
      }
      return pages[currentPage.value] || 'HomePage'
    })

    return {
      currentPage,
      currentComponent
    }
  }
}
</script>
