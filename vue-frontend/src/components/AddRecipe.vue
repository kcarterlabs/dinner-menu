<template>
  <div>
    <h2>➕ Add New Recipe</h2>

    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>

    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
    </div>

    <!-- Ingredients Section (structured format) -->
    <div class="ingredient-input-section">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h3 style="margin: 0;">Ingredients</h3>
        <div class="tab-buttons">
          <button
            @click="inputMode = 'single'"
            :class="['tab-btn', { active: inputMode === 'single' }]"
            type="button"
          >
            ✏️ Single Entry
          </button>
          <button
            @click="inputMode = 'bulk'"
            :class="['tab-btn', { active: inputMode === 'bulk' }]"
            type="button"
          >
            📋 Bulk Paste
          </button>
        </div>
      </div>

      <!-- Bulk Import Mode -->
      <div v-if="inputMode === 'bulk'" class="bulk-import-section">
        <div class="form-group">
          <label>Paste ingredient list (one per line)</label>
          <textarea
            v-model="bulkIngredientText"
            rows="10"
            placeholder="Paste ingredients here, e.g.:
1 yellow onion ($0.70)
▢ 2 cloves garlic ($0.08)
1 Tbsp olive oil ($0.22)
1 lb. ground beef ($4.98)"
            class="form-control"
            style="font-family: monospace; font-size: 14px;"
          ></textarea>
        </div>
        
        <button
          @click="parseBulkIngredients"
          :disabled="!bulkIngredientText.trim() || parsing"
          class="btn btn-primary"
          type="button"
        >
          {{ parsing ? '⏳ Parsing...' : '🔍 Parse Ingredients' }}
        </button>

        <!-- Preview parsed ingredients -->
        <div v-if="parsedIngredients.length > 0" style="margin-top: 20px;">
          <h4>Preview ({{ parsedIngredients.length }} ingredients)</h4>
          <div class="parsed-preview">
            <table style="width: 100%; border-collapse: collapse;">
              <thead>
                <tr style="background: #f5f5f5; text-align: left;">
                  <th style="padding: 8px; border: 1px solid #ddd;">Qty</th>
                  <th style="padding: 8px; border: 1px solid #ddd;">Unit</th>
                  <th style="padding: 8px; border: 1px solid #ddd;">Item</th>
                  <th style="padding: 8px; border: 1px solid #ddd;">Original</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(ing, idx) in parsedIngredients" :key="idx">
                  <td style="padding: 8px; border: 1px solid #ddd;">{{ ing.quantity || '—' }}</td>
                  <td style="padding: 8px; border: 1px solid #ddd;">{{ ing.unit || '—' }}</td>
                  <td style="padding: 8px; border: 1px solid #ddd;">{{ ing.item }}</td>
                  <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px; color: #666;">{{ ing.original }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div style="margin-top: 15px; display: flex; gap: 10px;">
            <button
              @click="confirmBulkImport"
              class="btn btn-success"
              type="button"
            >
              ✅ Add All {{ parsedIngredients.length }} Ingredients
            </button>
            <button
              @click="cancelBulkImport"
              class="btn"
              type="button"
              style="background: #e0e0e0;"
            >
              ❌ Cancel
            </button>
          </div>
        </div>
      </div>

      <!-- Single Entry Mode -->
      <div v-else class="ingredient-form">
        <div class="ingredient-fields">
          <div class="form-group-inline">
            <label>Quantity</label>
            <input
              v-model="currentIngredient.quantity"
              type="text"
              placeholder="1, 1/2, 2"
              class="form-control-small"
            />
          </div>
          
          <div class="form-group-inline">
            <label>Unit</label>
            <input
              v-model="currentIngredient.unit"
              type="text"
              placeholder="cup, tsp, lb"
              class="form-control-small"
              @input="onIngredientInput"
            />
          </div>
          
          <div class="form-group-inline flex-grow">
            <label>Item *</label>
            <input
              v-model="currentIngredient.item"
              type="text"
              placeholder="yellow onion, garlic"
              class="form-control"
              @input="onIngredientInput"
              required
            />
          </div>

          <button
            @click="addIngredient"
            :disabled="!currentIngredient.item.trim()"
            class="btn btn-success btn-small"
            style="align-self: flex-end;"
          >
            ➕ Add
          </button>
        </div>

        <div class="form-group" style="margin-top: 10px;">
          <label>Original (optional)</label>
          <input
            v-model="currentIngredient.original"
            type="text"
            placeholder="Full description: 1 cup diced yellow onion"
            class="form-control"
          />
        </div>
      </div>

      <!-- Fuzzy Matches -->
      <div v-if="fuzzyMatches.length > 0" class="fuzzy-matches">
        <small>Similar ingredients:</small>
        <button
          v-for="(match, index) in fuzzyMatches"
          :key="index"
          @click="addIngredientFromMatch(match)"
          class="fuzzy-match-btn"
        >
          {{ match }}
        </button>
      </div>

      <!-- Current Ingredients List -->
      <div v-if="ingredients.length > 0">
        <h4 style="margin-top: 20px; margin-bottom: 10px;">Added Ingredients:</h4>
        <ul class="ingredients-list">
          <li v-for="(ingredient, index) in ingredients" :key="index">
            <span>{{ index + 1 }}. {{ formatIngredient(ingredient) }}</span>
            <button @click="removeIngredient(index)" class="btn btn-danger btn-small">
              🗑️ Remove
            </button>
          </li>
        </ul>
      </div>
      <div v-else class="alert alert-info" style="margin-top: 15px;">
        No ingredients added yet. Fill in the fields above to add ingredients.
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

      <!-- Image Upload Section -->
      <div class="form-group">
        <label>Recipe Image (optional)</label>
        <div
          ref="dropZone"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @dragenter="handleDragOver"
          @dragleave="handleDragLeave"
          @click="focusDropZone"
          :class="['image-drop-zone', { 'dragging': isDragging }]"
          tabindex="0"
        >
          <input
            type="file"
            accept="image/*"
            @change="handleImageUpload"
            ref="imageInput"
            style="display: none;"
          />
          <div v-if="imagePreview" style="margin-top: 10px;">
            <img
              :src="imagePreview"
              alt="Recipe preview"
              style="max-width: 300px; max-height: 300px; border-radius: 8px; object-fit: cover;"
            />
            <button
              @click="removeImage"
              type="button"
              class="btn btn-small"
              style="display: block; margin-top: 10px; background: #ff6b6b; color: white;"
            >
              🗑️ Remove Image
            </button>
          </div>
          <div v-else class="drop-zone-content">
            <div style="font-size: 48px; margin-bottom: 10px;">📷</div>
            <button
              @click.stop="imageInput.click()"
              type="button"
              class="btn btn-small"
              style="background: #667eea; color: white; margin-bottom: 10px;"
            >
              📁 Choose File
            </button>
            <p style="margin: 0; color: #666; font-size: 14px;">
              or drag & drop an image here<br/>
              or click here and press Ctrl+V to paste
            </p>
            <p style="margin-top: 8px; color: #999; font-size: 12px;">Max 2MB</p>
          </div>
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
    const currentIngredient = ref({
      quantity: '',
      unit: '',
      item: '',
      original: ''
    })
    const allIngredients = ref([])
    const fuzzyMatches = ref([])
    const loading = ref(false)
    const successMessage = ref('')
    const errorMessage = ref('')
    
    // Image upload state
    const imagePreview = ref(null)
    const imageData = ref(null)
    const imageInput = ref(null)
    const isDragging = ref(false)
    const dropZone = ref(null)
    
    // Bulk import state
    const inputMode = ref('single')
    const bulkIngredientText = ref('')
    const parsedIngredients = ref([])
    const parsing = ref(false)

    const loadAllIngredients = async () => {
      try {
        const response = await axios.get('/api/recipes')
        const recipes = response.data.recipes || []
        
        const ingredientsSet = new Set()
        recipes.forEach(r => {
          if (r.ingredients) {
            r.ingredients.forEach(ing => {
              // Handle both structured and string formats
              const item = typeof ing === 'string' ? ing : (ing.item || ing.original || '')
              if (item) {
                ingredientsSet.add(item.toLowerCase().trim())
              }
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
      const input = currentIngredient.value.item.trim()
      
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

    const formatIngredient = (ing) => {
      if (typeof ing === 'string') return ing
      
      const parts = []
      if (ing.quantity) parts.push(ing.quantity)
      if (ing.unit) parts.push(ing.unit)
      if (ing.item) parts.push(ing.item)
      
      return parts.length > 0 ? parts.join(' ') : ing.original || 'Unknown'
    }

    const addIngredient = () => {
      const item = currentIngredient.value.item.trim()
      if (!item) return

      // Check for duplicates (case-insensitive comparison on item)
      const isDuplicate = ingredients.value.some(ing => 
        ing.item.toLowerCase() === item.toLowerCase()
      )
      
      if (isDuplicate) {
        return // Don't add duplicate
      }

      const newIng = {
        quantity: currentIngredient.value.quantity.trim(),
        unit: currentIngredient.value.unit.trim(),
        item: item,
        original: currentIngredient.value.original.trim() || 
                 `${currentIngredient.value.quantity} ${currentIngredient.value.unit} ${item}`.trim()
      }

      ingredients.value.push(newIng)
      
      // Reset form
      currentIngredient.value = {
        quantity: '',
        unit: '',
        item: '',
        original: ''
      }
      fuzzyMatches.value = []
    }

    const addIngredientFromMatch = (match) => {
      currentIngredient.value.item = match
      fuzzyMatches.value = []
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
          portions: String(recipe.value.portions),
          image: imageData.value  // Include base64 image data
        }

        console.log('Submitting recipe with image:', imageData.value ? `${imageData.value.substring(0, 50)}... (${imageData.value.length} chars)` : 'null')

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
        currentIngredient.value = {
          quantity: '',
          unit: '',
          item: '',
          original: ''
        }
        fuzzyMatches.value = []
        imagePreview.value = null
        imageData.value = null
        if (imageInput.value) {
          imageInput.value.value = ''
        }
        
        // Reload ingredients for future searches
        await loadAllIngredients()
        
      } catch (error) {
        errorMessage.value = `Error: ${error.response?.data?.error || error.message}`
      } finally {
        loading.value = false
      }
    }

    const parseBulkIngredients = async () => {
      parsing.value = true
      errorMessage.value = ''
      
      try {
        const lines = bulkIngredientText.value
          .split('\n')
          .map(line => line.trim())
          .filter(line => line.length > 0)
        
        const response = await axios.post('/api/parse-ingredients', {
          ingredients: lines
        })
        
        parsedIngredients.value = response.data.parsed_ingredients || []
        
      } catch (error) {
        errorMessage.value = `Parsing error: ${error.response?.data?.error || error.message}`
      } finally {
        parsing.value = false
      }
    }

    const confirmBulkImport = () => {
      const count = parsedIngredients.value.length
      
      // Add all parsed ingredients to the main list
      parsedIngredients.value.forEach(ing => {
        ingredients.value.push({
          quantity: ing.quantity || '',
          unit: ing.unit || '',
          item: ing.item || '',
          original: ing.original || ''
        })
      })
      
      // Reset bulk import state
      bulkIngredientText.value = ''
      parsedIngredients.value = []
      inputMode.value = 'single'
      successMessage.value = `✅ Added ${count} ingredients!`
    }

    const cancelBulkImport = () => {
      parsedIngredients.value = []
      bulkIngredientText.value = ''
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

    const processImageFile = async (file) => {
      console.log('Processing image file:', file.name, file.type, file.size)
      // Validate file type
      if (!file.type.startsWith('image/')) {
        errorMessage.value = 'Please select an image file'
        return
      }

      // If image is too large, resize it
      if (file.size > 2 * 1024 * 1024) {
        console.log('Image too large, resizing...')
        errorMessage.value = 'Resizing large image...'
        try {
          const resizedDataUrl = await resizeImage(file)
          imagePreview.value = resizedDataUrl
          imageData.value = resizedDataUrl
          errorMessage.value = ''
          isDragging.value = false
          console.log('Image resized successfully')
          return
        } catch (error) {
          console.error('Error resizing image:', error)
          errorMessage.value = 'Error resizing image. Please try a smaller file.'
          return
        }
      }

      const reader = new FileReader()
      reader.onload = (e) => {
        imagePreview.value = e.target.result
        imageData.value = e.target.result
        console.log('Image loaded, data length:', e.target.result?.length)
        errorMessage.value = ''
        isDragging.value = false
      }
      reader.readAsDataURL(file)
    }

    const handleImageUpload = (event) => {
      const file = event.target.files[0]
      if (!file) return
      processImageFile(file)
    }

    const handleDragOver = (event) => {
      event.preventDefault()
      event.stopPropagation()
      console.log('DRAGOVER EVENT')
      isDragging.value = true
    }

    const handleDragLeave = (event) => {
      event.preventDefault()
      event.stopPropagation()
      console.log('DRAGLEAVE EVENT')
      isDragging.value = false
    }

    const handleDrop = (event) => {
      event.preventDefault()
      event.stopPropagation()
      console.log('DROP EVENT:', event.dataTransfer?.files)
      isDragging.value = false
      const file = event.dataTransfer?.files[0]
      if (file) {
        console.log('File dropped:', file.name, file.type, file.size)
        processImageFile(file)
      } else {
        console.log('No file in drop event')
      }
    }

    const focusDropZone = () => {
      if (dropZone.value && !imagePreview.value) {
        dropZone.value.focus()
        console.log('Drop zone focused - you can now paste with Ctrl+V')
      }
    }

    const handlePaste = (event) => {
      event.preventDefault()
      console.log('PASTE EVENT triggered!', event.clipboardData)
      const items = event.clipboardData?.items
      if (!items) {
        console.log('No clipboard items')
        return
      }

      console.log('Clipboard items count:', items.length)
      for (let i = 0; i < items.length; i++) {
        console.log('Item', i, ':', items[i].type, items[i].kind)
        if (items[i].type.startsWith('image/')) {
          const file = items[i].getAsFile()
          if (file) {
            console.log('Pasted image file:', file.name, file.type, file.size)
            processImageFile(file)
            return
          }
        }
      }
      console.log('No image found in clipboard')
    }

    const removeImage = () => {
      imagePreview.value = null
      imageData.value = null
      if (imageInput.value) {
        imageInput.value.value = ''
      }
    }

    const fetchImageFromUrl = async (url) => {
      try {
        console.log('Fetching image from URL:', url)
        errorMessage.value = ''
        
        // Fetch the image as a blob
        const response = await fetch(url)
        if (!response.ok) throw new Error('Failed to fetch image')
        
        const blob = await response.blob()
        console.log('Fetched blob:', blob.type, blob.size)
        
        // Convert blob to File
        const file = new File([blob], 'dropped-image.jpg', { type: blob.type })
        processImageFile(file)
      } catch (error) {
        console.error('Error fetching image from URL:', error)
        errorMessage.value = 'Could not load image from URL. Try downloading it first or use a different image.'
      }
    }

    onMounted(() => {
      console.log('=== AddRecipe component mounted ===')
      console.log('dropZone ref:', dropZone.value)
      
      loadAllIngredients()
      
      // Handle drag and drop at document level
      const handleDocumentDragOver = (e) => {
        e.preventDefault()
        // Check if dragging over the drop zone
        if (dropZone.value && dropZone.value.contains(e.target)) {
          isDragging.value = true
        }
      }
      
      const handleDocumentDrop = (e) => {
        e.preventDefault()
        console.log('Document drop detected', e.target)
        
        // Check if dropped on the drop zone
        if (dropZone.value && dropZone.value.contains(e.target)) {
          console.log('Dropped on drop zone!')
          
          // Try to get file first
          const file = e.dataTransfer?.files[0]
          if (file) {
            console.log('File dropped:', file.name, file.type, file.size)
            processImageFile(file)
          } else {
            // Check for image URL (dragged from browser)
            const url = e.dataTransfer?.getData('text/html')
            const urlText = e.dataTransfer?.getData('text/uri-list') || e.dataTransfer?.getData('text/plain')
            
            console.log('No file, checking for URL:', { url: url?.substring(0, 100), urlText })
            
            if (urlText && (urlText.startsWith('http://') || urlText.startsWith('https://'))) {
              console.log('Loading image from URL:', urlText)
              fetchImageFromUrl(urlText)
            } else if (url) {
              // Extract img src from HTML
              const match = url.match(/<img[^>]+src="([^">]+)"/)
              if (match && match[1]) {
                console.log('Loading image from extracted URL:', match[1])
                fetchImageFromUrl(match[1])
              }
            }
          }
        }
        isDragging.value = false
      }
      
      const handleDocumentDragLeave = (e) => {
        // Only reset if leaving the drop zone
        if (dropZone.value && !dropZone.value.contains(e.target)) {
          isDragging.value = false
        }
      }
      
      document.addEventListener('dragover', handleDocumentDragOver)
      document.addEventListener('drop', handleDocumentDrop)
      document.addEventListener('dragleave', handleDocumentDragLeave)
      
      // Add paste listener to drop zone
      if (dropZone.value) {
        console.log('Attaching paste event listener to drop zone')
        dropZone.value.addEventListener('paste', handlePaste)
        
        // Also try keydown to debug
        dropZone.value.addEventListener('keydown', (e) => {
          console.log('Key pressed in drop zone:', e.key, e.ctrlKey, e.metaKey)
        })
      } else {
        console.error('Drop zone ref not found!')
      }
    })

    return {
      recipe,
      ingredients,
      currentIngredient,
      fuzzyMatches,
      loading,
      successMessage,
      errorMessage,
      inputMode,
      bulkIngredientText,
      parsedIngredients,
      parsing,
      imagePreview,
      imageData,
      imageInput,
      dropZone,
      onIngredientInput,
      formatIngredient,
      addIngredient,
      addIngredientFromMatch,
      removeIngredient,
      submitRecipe,
      parseBulkIngredients,
      confirmBulkImport,
      cancelBulkImport,
      handleImageUpload,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      focusDropZone,
      handlePaste,
      removeImage,
      isDragging
    }
  }
}
</script>

<style scoped>
.ingredient-form {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
}

.ingredient-fields {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group-inline {
  display: flex;
  flex-direction: column;
  min-width: 100px;
}

.form-group-inline.flex-grow {
  flex: 1;
  min-width: 200px;
}

.form-group-inline label {
  font-size: 0.9em;
  margin-bottom: 5px;
  font-weight: 600;
  color: #495057;
}

.form-control-small {
  padding: 8px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.fuzzy-matches {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.fuzzy-matches small {
  color: #6c757d;
  font-weight: 600;
  margin-right: 5px;
}

.fuzzy-match-btn {
  background: #e9ecef;
  border: 1px solid #dee2e6;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.fuzzy-match-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.ingredients-list {
  list-style: none;
  padding: 0;
}

.ingredients-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.ingredients-list li span {
  flex: 1;
}

.btn-small {
  padding: 6px 12px;
  font-size: 14px;
}

.tab-buttons {
  display: flex;
  gap: 5px;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  border-bottom: none;
}

.tab-btn:hover {
  background: #f8f9fa;
}

.tab-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.bulk-import-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 15px;
}

.parsed-preview {
  background: white;
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;
  overflow-x: auto;
}

.image-drop-zone {
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  background: #f8f9fa;
  transition: all 0.2s;
  cursor: pointer;
  margin-top: 8px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.image-drop-zone:hover,
.image-drop-zone:focus {
  border-color: #667eea;
  background: #f0f4ff;
  outline: none;
}

.image-drop-zone.dragging {
  border-color: #667eea;
  background: #e6f2ff;
  border-style: solid;
}

.drop-zone-content {
  padding: 10px;
  width: 100%;
}
</style>
