<template>
  <div>
    <h2>➕ Add New Recipe</h2>

    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>

    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
    </div>

    <!-- Ingredients Section (with fuzzy matching) -->
    <div class="ingredient-input-section">
      <h3>Ingredients</h3>
      
      <div class="ingredient-search">
        <input
          v-model="ingredientInput"
          @input="onIngredientInput"
          type="text"
          placeholder="Start typing ingredient... (e.g., tomato, pasta, chicken)"
          class="form-control"
        />
        <button
          @click="addIngredient"
          :disabled="!ingredientInput.trim()"
          class="btn btn-success btn-small"
        >
          ➕ Add
        </button>
      </div>

      <!-- Fuzzy Matches -->
      <div v-if="fuzzyMatches.length > 0" class="fuzzy-matches">
        <button
          v-for="(match, index) in fuzzyMatches"
          :key="index"
          @click="addIngredientFromMatch(match)"
          class="fuzzy-match-btn"
        >
          {{ match }}
        </button>
      </div>

      <div v-if="ingredientInput.length >= 2 && fuzzyMatches.length === 0" class="alert alert-info" style="margin-top: 10px;">
        No similar ingredients found. "{{ ingredientInput }}" will be a new ingredient.
      </div>

      <!-- Current Ingredients List -->
      <div v-if="ingredients.length > 0">
        <h4 style="margin-top: 20px; margin-bottom: 10px;">Added Ingredients:</h4>
        <ul class="ingredients-list">
          <li v-for="(ingredient, index) in ingredients" :key="index">
            <span>{{ index + 1 }}. {{ ingredient }}</span>
            <button @click="removeIngredient(index)" class="btn btn-danger btn-small">
              🗑️ Remove
            </button>
          </li>
        </ul>
      </div>
      <div v-else class="alert alert-info" style="margin-top: 15px;">
        No ingredients added yet. Start typing above to add ingredients.
      </div>
    </div>

    <!-- Recipe Form -->
    <form @submit.prevent="submitRecipe">
      <div class="form-group">
        <label>Recipe Title *</label>
        <input
          v-model="recipe.title"
          type="text"
          placeholder="e.g., Spaghetti Carbonara"
          required
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="checkbox-group">
            <input v-model="recipe.oven" type="checkbox" />
            Requires Oven
          </label>
          
          <label style="margin-top: 15px;">Portions</label>
          <input
            v-model.number="recipe.portions"
            type="number"
            min="1"
            max="20"
          />
        </div>

        <div class="form-group">
          <label class="checkbox-group">
            <input v-model="recipe.stove" type="checkbox" />
            Requires Stove
          </label>
          
          <label style="margin-top: 15px;">Date</label>
          <input v-model="recipe.date" type="date" />
        </div>
      </div>

      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Adding Recipe...' : 'Add Recipe' }}
      </button>
    </form>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'AddRecipe',
  setup() {
    const recipe = ref({
      title: '',
      oven: false,
      stove: false,
      portions: 4,
      date: new Date().toISOString().split('T')[0]
    })

    const ingredients = ref([])
    const ingredientInput = ref('')
    const allIngredients = ref([])
    const fuzzyMatches = ref([])
    const loading = ref(false)
    const successMessage = ref('')
    const errorMessage = ref('')

    const loadAllIngredients = async () => {
      try {
        const response = await axios.get('/api/recipes')
        const recipes = response.data.recipes || []
        
        const ingredientsSet = new Set()
        recipes.forEach(r => {
          if (r.ingredients) {
            r.ingredients.forEach(ing => {
              ingredientsSet.add(ing.toLowerCase().trim())
            })
          }
        })
        
        allIngredients.value = Array.from(ingredientsSet).sort()
      } catch (error) {
        console.error('Error loading ingredients:', error)
      }
    }

    const calculateSimilarity = (str1, str2) => {
      const s1 = str1.toLowerCase()
      const s2 = str2.toLowerCase()
      
      // Substring match gets highest priority
      if (s2.includes(s1)) return 1.0
      
      // Levenshtein distance based similarity
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

    const onIngredientInput = () => {
      const input = ingredientInput.value.trim()
      
      if (input.length < 2) {
        fuzzyMatches.value = []
        return
      }

      const matches = allIngredients.value
        .map(ing => ({
          ingredient: ing,
          score: calculateSimilarity(input, ing)
        }))
        .filter(m => m.score >= 0.4)
        .sort((a, b) => b.score - a.score)
        .slice(0, 8)
        .map(m => m.ingredient)

      fuzzyMatches.value = matches
    }

    const addIngredient = () => {
      const ing = ingredientInput.value.trim()
      if (ing && !ingredients.value.includes(ing)) {
        ingredients.value.push(ing)
        ingredientInput.value = ''
        fuzzyMatches.value = []
      }
    }

    const addIngredientFromMatch = (match) => {
      if (!ingredients.value.includes(match)) {
        ingredients.value.push(match)
        ingredientInput.value = ''
        fuzzyMatches.value = []
      }
    }

    const removeIngredient = (index) => {
      ingredients.value.splice(index, 1)
    }

    const submitRecipe = async () => {
      if (!recipe.value.title.trim()) {
        errorMessage.value = 'Please enter a recipe title'
        return
      }

      if (ingredients.value.length === 0) {
        errorMessage.value = 'Please add at least one ingredient'
        return
      }

      loading.value = true
      errorMessage.value = ''
      successMessage.value = ''

      try {
        const recipeData = {
          title: recipe.value.title,
          date: recipe.value.date,
          ingredients: ingredients.value,
          oven: recipe.value.oven,
          stove: recipe.value.stove,
          portions: String(recipe.value.portions)
        }

        await axios.post('/api/recipes', recipeData)
        
        successMessage.value = `✅ Recipe "${recipe.value.title}" added successfully!`
        
        // Reset form
        recipe.value = {
          title: '',
          oven: false,
          stove: false,
          portions: 4,
          date: new Date().toISOString().split('T')[0]
        }
        ingredients.value = []
        ingredientInput.value = ''
        fuzzyMatches.value = []
        
        // Reload ingredients for future searches
        await loadAllIngredients()
        
      } catch (error) {
        errorMessage.value = `Error: ${error.response?.data?.error || error.message}`
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadAllIngredients()
    })

    return {
      recipe,
      ingredients,
      ingredientInput,
      fuzzyMatches,
      loading,
      successMessage,
      errorMessage,
      onIngredientInput,
      addIngredient,
      addIngredientFromMatch,
      removeIngredient,
      submitRecipe
    }
  }
}
</script>
