# Dinner Menu - Vue.js Frontend

Modern, interactive Vue.js frontend with real-time ingredient fuzzy matching.

## Features

✨ **Smart Ingredient Autocomplete**
- Real-time fuzzy matching as you type
- Shows similar ingredients from existing recipes
- Click-to-add suggested ingredients
- Prevents duplicate ingredients with different formatting

🎯 **Interactive UI**
- Responsive design with smooth animations
- Live updates without page reloads
- Ingredient list management (add/remove)
- Recipe re-roll feature

🚀 **Performance**
- Built with Vite for fast development
- Optimized production build
- Nginx static file serving

## Development

### Local Development

```bash
cd vue-frontend
npm install
npm run dev
```

Access at: http://localhost:5173

### Build for Production

```bash
npm run build
```

### Docker Build

```bash
docker build -t dinner-menu-vue .
```

## Project Structure

```
vue-frontend/
├── src/
│   ├── components/
│   │   ├── HomePage.vue       # Landing page
│   │   ├── AddRecipe.vue      # Recipe form with fuzzy matching
│   │   ├── RecipesList.vue    # Recipe management
│   │   └── DinnerMenu.vue     # Menu generation
│   ├── App.vue                # Main app component
│   ├── main.js                # App entry point
│   └── style.css              # Global styles
├── index.html                 # HTML template
├── vite.config.js             # Vite configuration
├── Dockerfile                 # Production build
└── package.json               # Dependencies
```

## API Integration

Connects to Flask backend via `/api/*` proxy:
- GET `/api/recipes` - List all recipes
- POST `/api/recipes` - Add new recipe
- DELETE `/api/recipes/{index}` - Delete recipe
- POST `/api/dinner-menu` - Generate menu

## Fuzzy Matching Algorithm

Uses Levenshtein distance with:
- **Threshold**: 0.4 (configurable)
- **Substring priority**: Exact matches ranked highest
- **Top results**: Shows 8 best matches
- **Minimum input**: 2 characters

## Deployment

Deployed alongside Streamlit frontend:

- **Streamlit**: https://dinner-menu.kcarterlabs.tech
- **Vue.js**: https://vue.dinner-menu.kcarterlabs.tech

Both use the same Flask API backend.

## Technologies

- **Vue 3** - Composition API
- **Vite** - Build tool
- **Axios** - HTTP client
- **Nginx** - Production server
- **Docker** - Containerization
