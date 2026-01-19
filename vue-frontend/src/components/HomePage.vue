<template>
  <div>
    <h2>Welcome to Dinner Menu! 🍽️</h2>
    <p style="margin-top: 20px; font-size: 18px; color: #666;">
      This is the Vue.js frontend with smart ingredient autocomplete and fuzzy matching.
    </p>
    
    <div style="margin-top: 30px; padding: 20px; background: #f7fafc; border-radius: 8px;">
      <h3>✨ Features:</h3>
      <ul style="margin-top: 15px; margin-left: 20px; line-height: 2;">
        <li>📋 Manage your recipe collection</li>
        <li>🔍 Smart ingredient fuzzy search (no more duplicates!)</li>
        <li>🍲 Generate dinner menus based on weather</li>
        <li>⚡ Real-time autocomplete as you type</li>
        <li>🎯 Click-to-add ingredient suggestions</li>
      </ul>
    </div>
    
    <div style="margin-top: 20px; padding: 15px; background: #e6f2ff; border-radius: 8px; border-left: 4px solid #667eea;">
      <strong>💡 Pro Tip:</strong> When adding recipes, start typing an ingredient name and watch the magic happen - 
      similar ingredients from your existing recipes will appear instantly!
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomePage'
}
</script>
