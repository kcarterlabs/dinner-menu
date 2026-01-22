<template>
  <div>
    <h2>🍲 Generate Dinner Menu</h2>

    <div class="form-group">
      <label>Number of days: <strong>{{ days }}</strong></label>
      <input
        v-model.number="days"
        type="range"
        min="1"
        max="14"
        style="width: 100%; cursor: pointer;"
      />
      <div style="display: flex; justify-content: space-between; font-size: 12px; color: #666; margin-top: 5px;">
        <span>1 day</span>
        <span>14 days</span>
      </div>
    </div>

    <button
      @click="generateMenu"
      class="btn btn-primary"
      :disabled="loading"
    >
      {{ loading ? 'Generating...' : '🎲 Generate Menu' }}
    </button>

    <div v-if="errorMessage" class="alert alert-error" style="margin-top: 20px;">
      {{ errorMessage }}
    </div>

    <div v-if="weatherData && weatherData.forecast" style="margin-top: 30px;">
      <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 25px; border-radius: 12px; color: white;">
        <h3 style="margin: 0 0 20px 0; color: white;">📍 Location: {{ weatherData.location }}</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
          <div
            v-for="(day, index) in weatherData.forecast"
            :key="index"
            style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 8px; text-align: center;"
          >
            <div style="font-size: 14px; margin-bottom: 5px; opacity: 0.9;">{{ day.day }}</div>
            <div style="font-size: 32px; font-weight: bold;">{{ Math.round(day.temp) }}°F</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="menu.length > 0" style="margin-top: 30px;">
      <h3>Your Dinner Menu:</h3>
      
      <div
        v-for="(recipe, index) in menu"
        :key="index"
        class="recipe-card"
      >
        <div style="display: flex; gap: 20px;">
          <!-- Left side: Recipe details -->
          <div style="flex: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h3>Day {{ index + 1 }}: {{ recipe.title }}</h3>
              <button
                @click="rerollRecipe(index)"
                class="btn btn-small"
                style="background: #e6f2ff; color: #667eea;"
                title="Re-roll this recipe"
              >
                🔄
              </button>
            </div>
            
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
          </div>

          <!-- Right side: Recipe image -->
          <div v-if="recipe.image" style="flex: 0 0 250px;">
            <img
              :src="recipe.image"
              :alt="recipe.title"
              style="width: 100%; height: 250px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
            />
          </div>
        </div>
      </div>

      <div v-if="groceryList.length > 0" style="margin-top: 40px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
          <h3 style="margin: 0;">🛒 Shopping List:</h3>
          <button
            @click="downloadGroceryList"
            class="btn btn-small"
            style="background: #667eea; color: white;"
          >
            📥 Download
          </button>
        </div>
        <div class="recipe-card">
          <ul style="list-style: none; padding: 0; margin: 0;">
            <li
              v-for="(item, idx) in groceryList"
              :key="idx"
              style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #eee;"
            >
              <span style="text-transform: capitalize; flex: 1;">{{ item.ingredient }}</span>
              <span class="badge" style="background: #667eea; color: white;">
                {{ item.count }}
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'

export default {
  name: 'DinnerMenu',
  setup() {
    const days = ref(7)
    const menu = ref([])
    const groceryList = ref([])
    const weatherData = ref(null)
    const loading = ref(false)
    const errorMessage = ref('')

    const generateMenu = async () => {
      loading.value = true
      errorMessage.value = ''

      try {
        const response = await axios.get('/api/dinner-menu', {
          params: { days: days.value }
        })

        if (response.data.success) {
          menu.value = response.data.dinner_plan?.selected_recipes || response.data.selected_recipes || []
          weatherData.value = response.data.weather
          groceryList.value = response.data.dinner_plan?.grocery_list || []
        } else {
          errorMessage.value = response.data.error || 'Failed to generate menu'
        }
      } catch (error) {
        errorMessage.value = `Error: ${error.response?.data?.error || error.message}`
      } finally {
        loading.value = false
      }
    }

    const rerollRecipe = async (index) => {
      loading.value = true
      errorMessage.value = ''

      try {
        const response = await axios.post('/api/dinner-menu', {
          days: days.value,
          reroll_index: index,
          current_menu: menu.value,
          weather: weatherData.value
        })

        if (response.data.success) {
          menu.value = response.data.dinner_plan?.selected_recipes || response.data.selected_recipes || []
          groceryList.value = response.data.dinner_plan?.grocery_list || []
        } else {
          errorMessage.value = response.data.error || 'Failed to re-roll recipe'
        }
      } catch (error) {
        errorMessage.value = `Error: ${error.response?.data?.error || error.message}`
      } finally {
        loading.value = false
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

    const downloadGroceryList = () => {
      // Create formatted text content
      let content = '🛒 Shopping List\n'
      content += '='.repeat(40) + '\n\n'
      
      groceryList.value.forEach(item => {
        const capitalizedIngredient = item.ingredient.charAt(0).toUpperCase() + item.ingredient.slice(1)
        content += `☐ ${capitalizedIngredient} (${item.count})\n`
      })
      
      content += '\n' + '='.repeat(40) + '\n'
      content += `Generated: ${new Date().toLocaleDateString()}\n`
      
      // Create blob and download
      const blob = new Blob([content], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `shopping-list-${new Date().toISOString().split('T')[0]}.txt`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }

    return {
      days,
      menu,
      groceryList,
      weatherData,
      loading,
      errorMessage,
      generateMenu,
      rerollRecipe,
      downloadGroceryList,
      formatIngredient
    }
  }
}
</script>
