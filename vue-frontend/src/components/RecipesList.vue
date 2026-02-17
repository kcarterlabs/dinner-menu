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
        <div style="display: flex; gap: 20px;">
          <!-- Left side: Recipe details -->
          <div style="flex: 1;">
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

            <div style="display: flex; gap: 10px; margin-top: 15px;">
              <button
                @click="openEditModal(recipe)"
                class="btn btn-small"
                style="background: #48bb78; color: white;"
              >
                ✏️ Edit
              </button>
              <button
                @click="openImageUpload(recipe._id)"
                class="btn btn-small"
                style="background: #667eea; color: white;"
              >
                📷 {{ recipe.image ? 'Change' : 'Add' }} Image
              </button>
              <button
                @click="deleteRecipe(recipe._id)"
                class="btn btn-danger btn-small"
              >
                🗑️ Delete
              </button>
            </div>
          </div>

          <!-- Right side: Recipe image -->
          <div style="flex: 0 0 250px;">
            <div v-if="recipe.image" style="position: relative;">
              <img
                :src="recipe.image"
                :alt="recipe.title"
                style="width: 100%; height: 250px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
              />
              <button
                @click="removeImage(recipe._id)"
                class="btn btn-small"
                style="position: absolute; top: 8px; right: 8px; background: rgba(255, 107, 107, 0.9); color: white; padding: 4px 8px;"
              >
                🗑️
              </button>
            </div>
            <div
              v-else
              @drop="handleDropOnRecipe($event, recipe._id)"
              @dragover="handleDragOverRecipe($event, recipe._id)"
              @dragleave="handleDragLeaveRecipe"
              @click="focusPlaceholder($event, recipe._id)"
              :ref="el => setPlaceholderRef(el, recipe._id)"
              tabindex="0"
              :class="['image-placeholder', { 'dragging': dragRecipeId === recipe._id }]"
            >
              <div style="text-align: center;">
                <div style="font-size: 48px;">📷</div>
                <div style="margin-top: 8px; font-size: 14px;">No image</div>
                <div style="margin-top: 4px; font-size: 11px; color: #aaa;">Drag, drop, or paste here</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Hidden file input for image upload -->
    <input
      ref="imageInput"
      type="file"
      accept="image/*"
      @change="handleImageUpload"
      style="display: none;"
    />

    <!-- Edit Recipe Modal -->
    <div v-if="editModalOpen" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <h3>✏️ Edit Recipe</h3>
        
        <div style="margin-top: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: bold;">
            Recipe Name:
          </label>
          <input
            v-model="editForm.title"
            type="text"
            placeholder="Recipe name"
            style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px;"
          />
        </div>

        <div style="margin-top: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: bold;">
            Ingredients:
          </label>
          <div v-for="(ingredient, idx) in editForm.ingredients" :key="idx" style="display: flex; gap: 8px; margin-bottom: 8px;">
            <input
              v-model="editForm.ingredients[idx]"
              type="text"
              placeholder="e.g., 2 cups flour"
              style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
            />
            <button
              @click="removeIngredient(idx)"
              class="btn btn-danger btn-small"
              style="padding: 8px 12px;"
            >
              🗑️
            </button>
          </div>
          <button
            @click="addIngredient"
            class="btn btn-small"
            style="margin-top: 8px; background: #667eea; color: white;"
          >
            ➕ Add Ingredient
          </button>
        </div>

        <div style="display: flex; gap: 10px; margin-top: 30px; justify-content: flex-end;">
          <button
            @click="closeEditModal"
            class="btn"
            style="background: #e2e8f0; color: #333;"
          >
            Cancel
          </button>
          <button
            @click="saveEdit"
            class="btn"
            style="background: #48bb78; color: white;"
          >
            💾 Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

export default {
  name: 'RecipesList',
  setup() {
    const recipes = ref([])
    const loading = ref(true)
    const imageInput = ref(null)
    const currentRecipeId = ref(null)
    const dragRecipeId = ref(null)
    const placeholderRefs = ref({})
    const editModalOpen = ref(false)
    const editForm = ref({
      _id: null,
      title: '',
      ingredients: []
    })

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

    const openImageUpload = (recipeId) => {
      currentRecipeId.value = recipeId
      imageInput.value.click()
    }

    const resizeImage = (file, maxWidth = 1200, maxHeight = 1200) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          const img = new Image()
          img.onload = () => {
            let width = img.width
            let height = img.height

            // Calculate new dimensions while maintaining aspect ratio
            if (width > maxWidth || height > maxHeight) {
              const ratio = Math.min(maxWidth / width, maxHeight / height)
              width = width * ratio
              height = height * ratio
            }

            // Create canvas and resize
            const canvas = document.createElement('canvas')
            canvas.width = width
            canvas.height = height
            const ctx = canvas.getContext('2d')
            ctx.drawImage(img, 0, 0, width, height)

            // Try different quality levels until under 2MB
            let quality = 0.9
            let dataUrl = canvas.toDataURL('image/jpeg', quality)
            
            while (dataUrl.length > 2 * 1024 * 1024 * 1.37 && quality > 0.1) {
              quality -= 0.1
              dataUrl = canvas.toDataURL('image/jpeg', quality)
            }

            console.log('Resized image:', width, 'x', height, 'quality:', quality.toFixed(1))
            resolve(dataUrl)
          }
          img.onerror = reject
          img.src = e.target.result
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
    }

    const processImageForRecipe = async (file, recipeId) => {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file')
        return
      }

      // If image is too large, resize it
      if (file.size > 2 * 1024 * 1024) {
        console.log('Image too large, resizing...')
        try {
          const resizedDataUrl = await resizeImage(file)
          await axios.put(`/api/recipes/${recipeId}/image`, {
            image: resizedDataUrl
          })
          await loadRecipes()
          dragRecipeId.value = null
          console.log('Resized image uploaded successfully')
          return
        } catch (error) {
          console.error('Error resizing image:', error)
          alert('Error resizing image. Please try a smaller file.')
          return
        }
      }

      const reader = new FileReader()
      reader.onload = async (e) => {
        try {
          await axios.put(`/api/recipes/${recipeId}/image`, {
            image: e.target.result
          })
          await loadRecipes()
          dragRecipeId.value = null
        } catch (error) {
          alert(`Error uploading image: ${error.message}`)
        }
      }
      reader.readAsDataURL(file)
    }

    const handleImageUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      await processImageForRecipe(file, currentRecipeId.value)
      // Reset file input
      event.target.value = ''
    }

    const handleDragOverRecipe = (event, recipeId) => {
      event.preventDefault()
      dragRecipeId.value = recipeId
    }

    const handleDragLeaveRecipe = (event) => {
      event.preventDefault()
      dragRecipeId.value = null
    }

    const handleDropOnRecipe = async (event, recipeId) => {
      event.preventDefault()
      dragRecipeId.value = null
      const file = event.dataTransfer?.files[0]
      if (file) {
        await processImageForRecipe(file, recipeId)
      }
    }

    const removeImage = async (recipeId) => {
      if (!confirm('Remove image from this recipe?')) {
        return
      }

      try {
        await axios.put(`/api/recipes/${recipeId}/image`, {
          image: null
        })
        await loadRecipes()
      } catch (error) {
        alert(`Error removing image: ${error.message}`)
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

    const openEditModal = (recipe) => {
      editForm.value = {
        _id: recipe._id,
        title: recipe.title,
        ingredients: recipe.ingredients.map(ing => {
          // If ingredient is an object, get the original or format it
          if (typeof ing === 'object') {
            return ing.original || formatIngredient(ing)
          }
          return ing
        })
      }
      editModalOpen.value = true
    }

    const closeEditModal = () => {
      editModalOpen.value = false
      editForm.value = {
        _id: null,
        title: '',
        ingredients: []
      }
    }

    const addIngredient = () => {
      editForm.value.ingredients.push('')
    }

    const removeIngredient = (index) => {
      editForm.value.ingredients.splice(index, 1)
    }

    const saveEdit = async () => {
      if (!editForm.value.title || editForm.value.title.trim() === '') {
        alert('Recipe name is required')
        return
      }

      // Filter out empty ingredients
      const ingredients = editForm.value.ingredients
        .filter(ing => ing && ing.trim() !== '')

      if (ingredients.length === 0) {
        alert('At least one ingredient is required')
        return
      }

      try {
        await axios.put(`/api/recipes/${editForm.value._id}`, {
          title: editForm.value.title,
          ingredients: ingredients
        })
        await loadRecipes()
        closeEditModal()
      } catch (error) {
        alert(`Error updating recipe: ${error.message}`)
      }
    }

    const setPlaceholderRef = (el, recipeId) => {
      if (el) {
        placeholderRefs.value[recipeId] = el
      }
    }

    const focusPlaceholder = (event, recipeId) => {
      console.log('Placeholder clicked, recipe:', recipeId)
      currentRecipeId.value = recipeId
      event.target.focus()
    }

    const handlePaste = async (event) => {
      console.log('PASTE EVENT in RecipesList, recipe:', currentRecipeId.value)
      event.preventDefault()
      
      if (!currentRecipeId.value) {
        console.log('No recipe selected for paste')
        return
      }

      const items = event.clipboardData?.items
      if (!items) {
        console.log('No clipboard items')
        return
      }

      console.log('Clipboard items count:', items.length)
      
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        console.log(`Item ${i}:`, item.type, item.kind)
        
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile()
          if (file) {
            console.log('Pasted image file:', file.name, file.type, file.size)
            await processImageForRecipe(file, currentRecipeId.value)
            return
          }
        }
      }
      
      console.log('No image found in clipboard')
    }

    onMounted(() => {
      loadRecipes()
      
      // Add global paste listener
      document.addEventListener('paste', handlePaste)
    })

    onBeforeUnmount(() => {
      document.removeEventListener('paste', handlePaste)
    })

    return {
      recipes,
      loading,
      imageInput,
      dragRecipeId,
      editModalOpen,
      editForm,
      deleteRecipe,
      openImageUpload,
      handleImageUpload,
      handleDragOverRecipe,
      handleDragLeaveRecipe,
      handleDropOnRecipe,
      removeImage,
      formatIngredient,
      openEditModal,
      closeEditModal,
      addIngredient,
      removeIngredient,
      saveEdit,
      setPlaceholderRef,
      focusPlaceholder
    }
  }
}
</script>
<style scoped>
.image-placeholder {
  width: 100%;
  height: 250px;
  background: #f8f9fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  border: 2px dashed #dee2e6;
  transition: all 0.2s;
  cursor: pointer;
}

.image-placeholder:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.image-placeholder.dragging {
  border-color: #667eea;
  background: #e6f2ff;
  border-style: solid;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}
</style>