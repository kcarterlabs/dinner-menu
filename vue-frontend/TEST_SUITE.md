# Vue Frontend Test Suite

Comprehensive test coverage for the Dinner Menu Vue.js frontend.

## Test Stack

- **Vitest** - Unit & integration test runner
- **@vue/test-utils** - Vue component testing utilities
- **happy-dom** - Lightweight DOM implementation
- **Coverage reporting** - V8 coverage provider

## Running Tests

```bash
cd vue-frontend

# Install dependencies (if not already installed)
npm install

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

## Test Files

### Component Tests

1. **App.test.js** - Main app navigation and routing
2. **HomePage.test.js** - Welcome page content
3. **AddRecipe.test.js** - Recipe form with fuzzy ingredient matching
4. **RecipesList.test.js** - Recipe display and deletion
5. **DinnerMenu.test.js** - Menu generation and re-roll functionality

## Test Coverage

### AddRecipe Component (17 tests)
- ✅ Form rendering
- ✅ Loading existing ingredients
- ✅ Fuzzy matching algorithm
- ✅ Ingredient add/remove
- ✅ Duplicate prevention
- ✅ Form submission
- ✅ Validation errors
- ✅ API error handling

### RecipesList Component (8 tests)
- ✅ Loading state
- ✅ Recipe display
- ✅ Badge rendering
- ✅ Empty state
- ✅ Delete with confirmation
- ✅ Cancel delete
- ✅ API errors

### DinnerMenu Component (11 tests)
- ✅ Form rendering
- ✅ Menu generation
- ✅ Recipe display
- ✅ Individual recipe re-roll
- ✅ Error handling
- ✅ Loading states
- ✅ Re-roll button display

### App Component (7 tests)
- ✅ Header rendering
- ✅ Navigation buttons
- ✅ Page switching
- ✅ Active page highlighting
- ✅ Component routing

### HomePage Component (3 tests)
- ✅ Welcome message
- ✅ Feature list
- ✅ Pro tip section

**Total: 46 tests**

## Key Test Scenarios

### Fuzzy Matching
Tests verify the Levenshtein distance algorithm:
- Exact substring matches (score: 1.0)
- Typo tolerance ("tomat" → "tomato")
- Threshold filtering (default: 0.4)
- Top 8 results displayed

### API Integration
All API calls are mocked with axios:
- GET /api/recipes
- POST /api/recipes
- DELETE /api/recipes/:id
- POST /api/dinner-menu

### User Interactions
- Form inputs and validation
- Button clicks
- Navigation
- Confirmation dialogs
- Error message display

## CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Test Vue Frontend
  run: |
    cd vue-frontend
    npm ci
    npm test -- --run
    npm run test:coverage
```

## Coverage Goals

Current coverage targets:
- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

## Debugging Tests

```bash
# Run specific test file
npm test AddRecipe.test.js

# Run tests matching pattern
npm test -- --grep="fuzzy"

# Run with verbose output
npm test -- --reporter=verbose

# Debug with UI
npm run test:ui
```

## Known Issues & Fixes

### Issue: Tests timing out
**Fix**: Increase timeout in vite.config.js:
```js
test: {
  testTimeout: 10000
}
```

### Issue: Axios mocks not working
**Fix**: Ensure `vi.mock('axios')` is at top of file, clear mocks in `beforeEach`

### Issue: Component not mounting
**Fix**: Check that all dependencies are properly mocked

## Adding New Tests

Template for new component test:

```js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import YourComponent from '../src/components/YourComponent.vue'

describe('YourComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders correctly', () => {
    const wrapper = mount(YourComponent)
    expect(wrapper.exists()).toBe(true)
  })
})
```
