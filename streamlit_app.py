import streamlit as st
import requests
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Logging configuration
if not os.path.exists('logs'):
    try:
        os.makedirs('logs')
    except (OSError, PermissionError):
        pass  # Will fall back to console logging only

# Try to set up file logging, fall back to console only if there are permission issues
handlers = [logging.StreamHandler()]
try:
    file_handler = RotatingFileHandler('logs/streamlit.log', maxBytes=10240000, backupCount=10)
    handlers.insert(0, file_handler)
except (OSError, PermissionError):
    pass  # Continue with console logging only

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)
logger.info('Streamlit app starting')

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api')
logger.info(f'Using API base URL: {API_BASE_URL}')

st.set_page_config(
    page_title="Dinner Menu Planner",
    page_icon="🍽️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .recipe-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .weather-card {
        padding: 15px;
        border-radius: 8px;
        background-color: #e8f4f8;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'recipes' not in st.session_state:
    st.session_state.recipes = []

# Helper functions
def get_recipes():
    """Fetch all recipes from API"""
    try:
        logger.info('Fetching recipes from API')
        response = requests.get(f"{API_BASE_URL}/recipes")
        if response.status_code == 200:
            data = response.json()
            logger.info(f'Successfully fetched {len(data.get("recipes", []))} recipes')
            return data.get('recipes', [])
        logger.warning(f'Failed to fetch recipes: Status {response.status_code}')
        return []
    except Exception as e:
        logger.error(f'Error fetching recipes: {e}')
        st.error(f"Error fetching recipes: {e}")
        return []

def add_recipe_api(recipe_data):
    """Add a recipe via API"""
    try:
        logger.info(f'Adding recipe: {recipe_data.get("title", "Unknown")}')
        response = requests.post(f"{API_BASE_URL}/recipes", json=recipe_data)
        result = response.json()
        if result.get('success'):
            logger.info(f'Recipe "{recipe_data.get("title")}" added successfully')
        else:
            logger.warning(f'Failed to add recipe: {result.get("error")}')
        return result
    except Exception as e:
        logger.error(f'Error adding recipe: {e}')
        return {"success": False, "error": str(e)}

def delete_recipe_api(index):
    """Delete a recipe via API"""
    try:
        logger.info(f'Deleting recipe at index {index}')
        response = requests.delete(f"{API_BASE_URL}/recipes/{index}")
        result = response.json()
        if result.get('success'):
            logger.info(f'Recipe deleted successfully')
        else:
            logger.warning(f'Failed to delete recipe: {result.get("error")}')
        return result
    except Exception as e:
        logger.error(f'Error deleting recipe: {e}')
        return {"success": False, "error": str(e)}

def get_dinner_menu(days):
    """Get dinner menu with weather"""
    try:
        logger.info(f'Getting dinner menu for {days} days with weather')
        response = requests.get(f"{API_BASE_URL}/dinner-menu", params={"days": days})
        result = response.json()
        if result.get('success'):
            logger.info(f'Dinner menu retrieved successfully')
        else:
            logger.warning(f'Failed to get dinner menu: {result.get("error")}')
        return result
    except Exception as e:
        logger.error(f'Error getting dinner menu: {e}')
        return {"success": False, "error": str(e)}

def reroll_dinner_menu(days, weather_data, keep_indices=None):
    """Re-roll dinner menu using cached weather data
    
    Args:
        days: Number of days to plan for
        weather_data: Cached weather data
        keep_indices: List of recipe indices to keep (others will be re-rolled)
    """
    try:
        if keep_indices:
            logger.info(f'Re-rolling single recipe for {days} days, keeping indices: {keep_indices}')
        else:
            logger.info(f'Re-rolling dinner menu for {days} days with cached weather')
        
        payload = {"weather": weather_data}
        if keep_indices:
            payload["exclude_indices"] = keep_indices
        
        response = requests.post(
            f"{API_BASE_URL}/dinner-menu",
            params={"days": days},
            json=payload
        )
        result = response.json()
        if result.get('success'):
            logger.info(f'Dinner menu re-rolled successfully')
        else:
            logger.warning(f'Failed to re-roll dinner menu: {result.get("error")}')
        return result
    except Exception as e:
        logger.error(f'Error re-rolling dinner menu: {e}')
        return {"success": False, "error": str(e)}

def get_quick_dinner_menu(days):
    """Get dinner menu without weather"""
    try:
        logger.info(f'Getting quick dinner menu for {days} days')
        response = requests.get(f"{API_BASE_URL}/dinner-menu/quick", params={"days": days})
        result = response.json()
        if result.get('success'):
            logger.info(f'Quick menu retrieved successfully')
        else:
            logger.warning(f'Failed to get quick menu: {result.get("error")}')
        return result
    except Exception as e:
        logger.error(f'Error getting quick menu: {e}')
        return {"success": False, "error": str(e)}

def get_weather(days):
    """Get weather forecast"""
    try:
        logger.info(f'Getting weather forecast for {days} days')
        response = requests.get(f"{API_BASE_URL}/weather", params={"days": days})
        result = response.json()
        if result.get('success'):
            logger.info(f'Weather forecast retrieved successfully')
        else:
            logger.warning(f'Failed to get weather: {result.get("error")}')
        return result
    except Exception as e:
        logger.error(f'Error getting weather: {e}')
        return {"success": False, "error": str(e)}

# Main app
st.title("🍽️ Dinner Menu Planner")
st.markdown("---")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigate",
    ["🏠 Home", "📋 View Recipes", "➕ Add Recipe", "🌤️ Weather", "🍲 Dinner Menu"]
)

# HOME PAGE
if page == "🏠 Home":
    st.header("Welcome to Dinner Menu Planner!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Recipes", len(get_recipes()))
    
    with col2:
        if st.button("🍲 Quick Menu (7 days)", use_container_width=True):
            with st.spinner("Generating menu..."):
                result = get_quick_dinner_menu(7)
                if result.get('success'):
                    st.session_state.quick_menu = result
                    st.rerun()
    
    with col3:
        if st.button("🌤️ Check Weather", use_container_width=True):
            with st.spinner("Fetching weather..."):
                result = get_weather(7)
                if result.get('success'):
                    st.session_state.weather_data = result
                    st.rerun()
    
    st.markdown("---")
    
    # Display quick menu if available
    if 'quick_menu' in st.session_state:
        st.subheader("Quick Menu Plan")
        dinner_plan = st.session_state.quick_menu.get('dinner_plan', {})
        selected = dinner_plan.get('selected_recipes', [])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info(f"📊 Total portions: {dinner_plan.get('total_portions')} for {dinner_plan.get('days_requested')} days")
            
            for idx, recipe in enumerate(selected, 1):
                with st.expander(f"{idx}. {recipe['title']} - {recipe['portions']} portions"):
                    st.write(f"**Date Added:** {recipe.get('date', 'N/A')}")
                    st.write(f"**Oven:** {'✅ Yes' if recipe.get('oven') else '❌ No'}")
                    st.write(f"**Stove:** {'✅ Yes' if recipe.get('stove') else '❌ No'}")
                    st.write("**Ingredients:**")
                    for ing in recipe.get('ingredients', []):
                        st.write(f"  • {ing}")
        
        with col2:
            st.success("🛒 Grocery List")
            grocery_list = dinner_plan.get('grocery_list', [])
            if grocery_list:
                # Create downloadable text
                grocery_text = "GROCERY LIST\n" + "="*30 + "\n\n"
                for item in grocery_list:
                    if item['count'] > 1:
                        grocery_text += f"☐ {item['ingredient']} (×{item['count']})\n"
                        st.write(f"☐ {item['ingredient']} (×{item['count']})")
                    else:
                        grocery_text += f"☐ {item['ingredient']}\n"
                        st.write(f"☐ {item['ingredient']}")
                
                st.download_button(
                    label="📥 Download List",
                    data=grocery_text,
                    file_name="grocery_list.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.write("No ingredients found")
    
    # Display weather if available
    if 'weather_data' in st.session_state:
        st.subheader("Weather Forecast")
        weather = st.session_state.weather_data.get('weather', {})
        st.write(f"📍 **Location:** {weather.get('location')}")
        
        cols = st.columns(min(len(weather.get('forecast', [])), 4))
        for idx, day_data in enumerate(weather.get('forecast', [])):
            with cols[idx % 4]:
                st.metric(
                    day_data['day'],
                    f"{day_data['temp']}°F",
                    delta=None
                )

# VIEW RECIPES PAGE
elif page == "📋 View Recipes":
    st.header("📋 Recipe Collection")
    
    recipes = get_recipes()
    
    if not recipes:
        st.info("No recipes found. Add some recipes to get started!")
    else:
        st.write(f"**Total Recipes:** {len(recipes)}")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_oven = st.checkbox("Show only non-oven recipes")
        with col2:
            filter_stove = st.checkbox("Show only stove recipes")
        with col3:
            search = st.text_input("🔍 Search recipes", "")
        
        # Apply filters
        filtered_recipes = recipes
        if filter_oven:
            filtered_recipes = [r for r in filtered_recipes if not r.get('oven')]
        if filter_stove:
            filtered_recipes = [r for r in filtered_recipes if r.get('stove')]
        if search:
            filtered_recipes = [r for r in filtered_recipes if search.lower() in r.get('title', '').lower()]
        
        st.markdown("---")
        
        # Display recipes
        for idx, recipe in enumerate(filtered_recipes):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                with st.expander(f"🍽️ {recipe['title']} ({recipe.get('portions', '1')} portions)"):
                    st.write(f"**Date Added:** {recipe.get('date', 'N/A')}")
                    st.write(f"**Oven:** {'✅ Yes' if recipe.get('oven') else '❌ No'}")
                    st.write(f"**Stove:** {'✅ Yes' if recipe.get('stove') else '❌ No'}")
                    st.write("**Ingredients:**")
                    for ing in recipe.get('ingredients', []):
                        st.write(f"  • {ing}")
            
            with col2:
                # Find original index
                original_idx = recipes.index(recipe)
                if st.button("🗑️ Delete", key=f"delete_{original_idx}"):
                    result = delete_recipe_api(original_idx)
                    if result.get('success'):
                        st.success("Recipe deleted!")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error')}")

# ADD RECIPE PAGE
elif page == "➕ Add Recipe":
    st.header("➕ Add New Recipe")
    
    with st.form("add_recipe_form"):
        title = st.text_input("Recipe Title*", placeholder="e.g., Spaghetti Carbonara")
        
        col1, col2 = st.columns(2)
        with col1:
            oven = st.checkbox("Requires Oven")
            portions = st.number_input("Portions", min_value=1, max_value=20, value=4)
        with col2:
            stove = st.checkbox("Requires Stove")
            date = st.date_input("Date", datetime.now())
        
        ingredients_text = st.text_area(
            "Ingredients* (one per line or comma-separated)",
            placeholder="pasta\neggs\nbacon\nparmesan cheese"
        )
        
        submitted = st.form_submit_button("Add Recipe", use_container_width=True)
        
        if submitted:
            if not title or not ingredients_text:
                st.error("Please fill in all required fields (marked with *)")
            else:
                # Parse ingredients
                if '\n' in ingredients_text:
                    ingredients = [i.strip() for i in ingredients_text.split('\n') if i.strip()]
                else:
                    ingredients = [i.strip() for i in ingredients_text.split(',') if i.strip()]
                
                recipe_data = {
                    "title": title,
                    "date": date.strftime('%Y-%m-%d'),
                    "ingredients": ingredients,
                    "oven": oven,
                    "stove": stove,
                    "portions": str(portions)
                }
                
                with st.spinner("Adding recipe..."):
                    result = add_recipe_api(recipe_data)
                
                if result.get('success'):
                    st.success(f"✅ Recipe '{title}' added successfully!")
                    st.balloons()
                else:
                    st.error(f"❌ Error: {result.get('error')}")

# WEATHER PAGE
elif page == "🌤️ Weather":
    st.header("🌤️ Weather Forecast")
    
    days = st.slider("Number of days", min_value=1, max_value=14, value=7)
    
    if st.button("Get Weather Forecast", use_container_width=True):
        with st.spinner("Fetching weather..."):
            result = get_weather(days)
        
        if result.get('success'):
            weather = result.get('weather', {})
            st.success(f"📍 Location: {weather.get('location')}")
            
            st.markdown("---")
            
            forecast = weather.get('forecast', [])
            cols = st.columns(min(len(forecast), 4))
            
            for idx, day_data in enumerate(forecast):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div class="weather-card">
                        <h3>{day_data['day']}</h3>
                        <p>{day_data['date']}</p>
                        <h2>{day_data['temp']}°F</h2>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Check if too hot
            temps = [day['temp'] for day in forecast]
            if any(temp > 90 for temp in temps):
                st.warning("🔥 Some days exceed 90°F - oven recipes will be excluded from dinner menu!")
        else:
            st.error(f"❌ Error: {result.get('error')}")

# DINNER MENU PAGE
elif page == "🍲 Dinner Menu":
    st.header("🍲 Generate Dinner Menu")
    
    tab1, tab2 = st.tabs(["🌤️ Weather-Based Menu", "⚡ Quick Menu"])
    
    with tab1:
        st.write("Generate a dinner menu that considers weather conditions")
        
        days = st.slider("Number of days", min_value=1, max_value=14, value=7, key="weather_days")
        
        if st.button("Generate Weather-Based Menu", use_container_width=True, type="primary"):
            with st.spinner("Analyzing weather and selecting recipes..."):
                result = get_dinner_menu(days)
            
            if result.get('success'):
                st.session_state.weather_menu_result = result
                st.session_state.weather_menu_days = days
                # Track original recipe indices from recipes.json for exclusion
                all_recipes = get_recipes()
                recipe_indices = []
                for recipe in result.get('dinner_plan', {}).get('selected_recipes', []):
                    for orig_idx, orig_recipe in enumerate(all_recipes):
                        if orig_recipe['title'] == recipe['title']:
                            recipe_indices.append(orig_idx)
                            break
                st.session_state.recipe_indices = recipe_indices
                st.rerun()
        
        # Display results from session state
        if 'weather_menu_result' in st.session_state:
            result = st.session_state.weather_menu_result
            
            if result.get('success'):
                # Display weather
                weather = result.get('weather', {})
                st.success(f"📍 Location: {weather.get('location')}")
                
                forecast = weather.get('forecast', [])
                cols = st.columns(min(len(forecast), 4))
                for idx, day_data in enumerate(forecast):
                    with cols[idx % 4]:
                        st.metric(day_data['day'], f"{day_data['temp']}°F")
                
                st.markdown("---")
                
                # Display menu
                dinner_plan = result.get('dinner_plan', {})
                selected = dinner_plan.get('selected_recipes', [])
                
                if dinner_plan.get('too_hot_for_oven'):
                    st.warning("🔥 Oven recipes excluded due to high temperatures!")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.info(f"📊 Total portions: {dinner_plan.get('total_portions')} for {dinner_plan.get('days_requested')} days")
                    
                    for idx, recipe in enumerate(selected):
                        with st.expander(f"Day {idx + 1}: {recipe['title']} - {recipe['portions']} portions"):
                            col_recipe, col_reroll = st.columns([4, 1])
                            
                            with col_recipe:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**Oven:** {'✅ Yes' if recipe.get('oven') else '❌ No'}")
                                    st.write(f"**Stove:** {'✅ Yes' if recipe.get('stove') else '❌ No'}")
                                with col_b:
                                    st.write(f"**Date Added:** {recipe.get('date', 'N/A')}")
                                    st.write(f"**Portions:** {recipe['portions']}")
                                
                                st.write("**Ingredients:**")
                                for ing in recipe.get('ingredients', []):
                                    st.write(f"  • {ing}")
                            
                            with col_reroll:
                                # Re-roll button for this specific recipe
                                if st.button("🔄", key=f"reroll_{idx}", help="Re-roll this recipe only"):
                                    with st.spinner(f"Re-rolling {recipe['title']}..."):
                                        # Get indices of all OTHER recipes to keep
                                        keep_indices = [st.session_state.recipe_indices[i] for i in range(len(selected)) if i != idx]
                                        cached_weather = st.session_state.weather_menu_result.get('weather', {})
                                        result = reroll_dinner_menu(days, cached_weather, keep_indices)
                                    
                                    if result.get('success'):
                                        st.session_state.weather_menu_result = result
                                        # Update recipe indices
                                        all_recipes = get_recipes()
                                        recipe_indices = []
                                        for r in result.get('dinner_plan', {}).get('selected_recipes', []):
                                            for orig_idx, orig_recipe in enumerate(all_recipes):
                                                if orig_recipe['title'] == r['title']:
                                                    recipe_indices.append(orig_idx)
                                                    break
                                        st.session_state.recipe_indices = recipe_indices
                                        st.rerun()
                
                with col2:
                    st.success("🛒 Grocery List")
                    grocery_list = dinner_plan.get('grocery_list', [])
                    if grocery_list:
                        # Create downloadable text
                        grocery_text = "GROCERY LIST\n" + "="*30 + "\n\n"
                        for item in grocery_list:
                            if item['count'] > 1:
                                grocery_text += f"☐ {item['ingredient']} (×{item['count']})\n"
                                st.write(f"☐ {item['ingredient']} (×{item['count']})")
                            else:
                                grocery_text += f"☐ {item['ingredient']}\n"
                                st.write(f"☐ {item['ingredient']}")
                        
                        st.download_button(
                            label="📥 Download List",
                            data=grocery_text,
                            file_name="grocery_list.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    else:
                        st.write("No ingredients found")
            else:
                st.error(f"❌ Error: {result.get('error')}")
    
    with tab2:
        st.write("Generate a quick menu without weather consideration")
        
        days_quick = st.slider("Number of days", min_value=1, max_value=14, value=7, key="quick_days")
        
        if st.button("Generate Quick Menu", use_container_width=True):
            with st.spinner("Selecting recipes..."):
                result = get_quick_dinner_menu(days_quick)
            
            if result.get('success'):
                dinner_plan = result.get('dinner_plan', {})
                selected = dinner_plan.get('selected_recipes', [])
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.info(f"📊 Total portions: {dinner_plan.get('total_portions')} for {dinner_plan.get('days_requested')} days")
                    
                    for idx, recipe in enumerate(selected, 1):
                        with st.expander(f"Day {idx}: {recipe['title']} - {recipe['portions']} portions"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.write(f"**Oven:** {'✅ Yes' if recipe.get('oven') else '❌ No'}")
                                st.write(f"**Stove:** {'✅ Yes' if recipe.get('stove') else '❌ No'}")
                            with col_b:
                                st.write(f"**Date Added:** {recipe.get('date', 'N/A')}")
                                st.write(f"**Portions:** {recipe['portions']}")
                            
                            st.write("**Ingredients:**")
                            for ing in recipe.get('ingredients', []):
                                st.write(f"  • {ing}")
                
                with col2:
                    st.success("🛒 Grocery List")
                    grocery_list = dinner_plan.get('grocery_list', [])
                    if grocery_list:
                        # Create downloadable text
                        grocery_text = "GROCERY LIST\n" + "="*30 + "\n\n"
                        for item in grocery_list:
                            if item['count'] > 1:
                                grocery_text += f"☐ {item['ingredient']} (×{item['count']})\n"
                                st.write(f"☐ {item['ingredient']} (×{item['count']})")
                            else:
                                grocery_text += f"☐ {item['ingredient']}\n"
                                st.write(f"☐ {item['ingredient']}")
                        
                        st.download_button(
                            label="📥 Download List",
                            data=grocery_text,
                            file_name="grocery_list.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    else:
                        st.write("No ingredients found")
            else:
                st.error(f"❌ Error: {result.get('error')}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "Dinner Menu Planner helps you plan meals based on weather conditions. "
    "Add your recipes and let the app suggest what to cook!"
)
