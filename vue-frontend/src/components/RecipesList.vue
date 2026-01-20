<template>
  <div>
    <h2>📋 Recipe Collection</h2>

    <div v-if="loading" class="loading">Loading recipes...</div>

    <div v-else-if="recipes.length === 0" class="alert alert-info">
      No recipes found. Add your first recipe!
    </div>

    <div v-else>
      <p style="margin-bottom: 20px; color: #666;">
        Total recipes: <strong>{{ recipes.length }}</strong>
      </p>

      <div
        v-for="(recipe, index) in recipes"
        :key="recipe._id || index"
        class="recipe-card"
      >
        <h3>{{ recipe.title }}</h3>
        
        <div style="margin: 10px 0;">
          <span v-if="recipe.oven" class="badge badge-oven">🔥 Oven</span>
          <span v-if="recipe.stove" class="badge badge-stove">🍳 Stove</span>
          <span class="badge" style="background: #e6f2ff; color: #667eea;">
            👥 {{ recipe.portions }} portions
          </span>
        </div>

        <div style="margin-top: 15px;">
          <strong>Ingredients:</strong>
          <ul style="margin-left: 20px; margin-top: 8px;">
            <li v-for="(ingredient, idx) in recipe.ingredients" :key="idx">
              {{ formatIngredient(ingredient) }}
            </li>
          </ul>
        </div>

        <div style="margin-top: 10px; color: #666; font-size: 14px;">
          📅 Added: {{ recipe.date }}
        </div>

        <button
          @click="deleteRecipe(recipe._id)"
          class="btn btn-danger btn-small"
          style="margin-top: 15px;"
        >
          🗑️ Delete Recipe
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'RecipesList',
  setup() {
    const recipes = ref([])
    const loading = ref(true)

    const loadRecipes = async () => {
      try {
        loading.value = true
        const response = await axios.get('/api/recipes')
        recipes.value = response.data.recipes || []
      } catch (error) {
        console.error('Error loading recipes:', error)
      } finally {
        loading.value = false
      }
    }

    const deleteRecipe = async (recipeId) => {
      if (!confirm('Are you sure you want to delete this recipe?')) {
        return
      }

      try {
        await axios.delete(`/api/recipes/${recipeId}`)
        await loadRecipes()
      } catch (error) {
        alert(`Error deleting recipe: ${error.message}`)
      }
    }

    const formatIngredient = (ingredient) => {
      // Handle both structured {quantity, unit, item} and legacy string formats
      if (typeof ingredient === 'string') {
        return ingredient
      }
      
      // Use the original field if available (preserves user's exact input)
      if (ingredient.original) {
        return ingredient.original
      }
      
      // Otherwise construct from structured fields
      const parts = []
      if (ingredient.quantity) parts.push(ingredient.quantity)
      if (ingredient.unit) parts.push(ingredient.unit)
      if (ingredient.item) parts.push(ingredient.item)
      
      return parts.join(' ') || 'Unknown ingredient'
    }

    onMounted(() => {
      loadRecipes()
    })

    return {
      recipes,
      loading,
      deleteRecipe,
      formatIngredient
    }
  }
}
</script>
