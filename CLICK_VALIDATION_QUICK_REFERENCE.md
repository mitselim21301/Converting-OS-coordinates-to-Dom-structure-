# Click Validation Quick Reference Guide

Fast lookup for implementing robust click automation.

---

## Essential Checklist

Before clicking any element, verify:

- [ ] **Attached** - Element is in DOM
- [ ] **Visible** - Non-zero size, not hidden, opacity > 0
- [ ] **In Viewport** - At least partially visible on screen
- [ ] **Stable** - Not animating or moving
- [ ] **Interactable** - Not disabled, pointer-events enabled
- [ ] **Hit Target** - Element would receive the click (not obscured)

---

## Common Patterns

### Basic Robust Click (JavaScript)

```javascript
async function robustClick(selector) {
    const element = document.querySelector(selector);

    // 1. Scroll into view
    element.scrollIntoView({ block: 'center' });
    await delay(300);

    // 2. Wait for stability
    await waitForStability(element);

    // 3. Check hit target
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const hitEl = document.elementFromPoint(centerX, centerY);

    if (hitEl !== element && !element.contains(hitEl)) {
        // Obscured - try to dismiss overlay
        await dismissOverlay(hitEl);
    }

    // 4. Click
    element.click();
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForStability(element, frames = 3) {
    let lastRect = element.getBoundingClientRect();

    for (let i = 0; i < frames; i++) {
        await new Promise(resolve => requestAnimationFrame(resolve));
        const rect = element.getBoundingClientRect();

        if (rect.x !== lastRect.x || rect.y !== lastRect.y) {
            return false; // Not stable
        }

        lastRect = rect;
    }

    return true;
}
```

### Retry with Exponential Backoff

```javascript
async function clickWithRetry(selector, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            await robustClick(selector);
            return { success: true, attempts: i + 1 };
        } catch (error) {
            if (i === maxRetries - 1) throw error;

            const delay = 1000 * Math.pow(2, i);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}
```

### Playwright

```javascript
// Auto-waits for actionability
await page.click(selector);

// Custom timeout
await page.click(selector, { timeout: 10000 });

// Force click (skip checks) - use sparingly
await page.click(selector, { force: true });

// Click with offset
await page.click(selector, { position: { x: 10, y: 10 } });
```

### Selenium (Python)

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Wait until clickable
wait = WebDriverWait(driver, 10)
element = wait.until(EC.element_to_be_clickable((By.ID, "button")))
element.click()

# Click with offset
from selenium.webdriver.common.action_chains import ActionChains
actions = ActionChains(driver)
actions.move_to_element_with_offset(element, 10, 10).click().perform()

# JavaScript click (last resort)
driver.execute_script("arguments[0].click();", element)
```

---

## Confidence Score (Quick Calculation)

```javascript
function quickConfidence(element) {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);

    // Basic checks (0 or 1)
    if (rect.width === 0 || rect.height === 0) return 0;
    if (style.display === 'none') return 0;
    if (style.visibility === 'hidden') return 0;
    if (element.disabled) return 0;
    if (style.pointerEvents === 'none') return 0;

    let score = 100;

    // Opacity
    score *= parseFloat(style.opacity) || 1;

    // Viewport visibility
    const inViewport = (
        rect.top < window.innerHeight &&
        rect.bottom > 0 &&
        rect.left < window.innerWidth &&
        rect.right > 0
    );
    if (!inViewport) score *= 0.5;

    // Hit target
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const hitEl = document.elementFromPoint(centerX, centerY);
    if (hitEl !== element && !element.contains(hitEl)) {
        score *= 0.6; // Obscured
    }

    return Math.round(score);
}
```

**Thresholds:**
- `>= 90%` - Safe to click
- `70-89%` - Probably safe, monitor
- `50-69%` - Risky, improve conditions first
- `< 50%` - Don't click, use alternative method

---

## Common Issues and Solutions

### Issue: Element Click Intercepted

**Cause:** Another element is covering the target element.

**Solutions:**
```javascript
// 1. Wait for overlay to disappear
await page.waitForSelector('.overlay', { state: 'hidden' });

// 2. Dismiss overlay first
await page.click('.modal .close-button');

// 3. Temporarily disable overlay
document.querySelector('.overlay').style.pointerEvents = 'none';

// 4. JavaScript click (bypass)
await page.evaluate(() => document.querySelector(selector).click());
```

### Issue: Stale Element Reference

**Cause:** Element was removed/re-added to DOM between find and click.

**Solutions:**
```javascript
// Re-locate element each time
function click() {
    const element = document.querySelector(selector); // Fresh lookup
    element.click();
}

// Retry on stale element
try {
    element.click();
} catch (StaleElementReferenceException e) {
    element = driver.find_element(By.ID, "button"); // Re-find
    element.click();
}
```

### Issue: Element Not Interactable

**Cause:** Element is disabled, has pointer-events:none, or is outside viewport.

**Solutions:**
```javascript
// 1. Scroll into view
element.scrollIntoView({ block: 'center' });

// 2. Wait for element to be enabled
await waitUntil(() => !element.disabled);

// 3. Check CSS
if (getComputedStyle(element).pointerEvents === 'none') {
    element.style.pointerEvents = 'auto';
}
```

### Issue: Race Condition / Timing

**Cause:** Page is still loading or updating when click is attempted.

**Solutions:**
```javascript
// 1. Wait for network idle
await page.waitForLoadState('networkidle');

// 2. Wait for specific element
await page.waitForSelector(selector, { state: 'visible' });

// 3. Wait for stability
await waitForStability(element);

// 4. Wait for AJAX completion
await waitForAjaxComplete();
```

---

## API Quick Reference

### Document APIs

```javascript
// Find element at coordinates
document.elementFromPoint(x, y)

// Find all elements at coordinates (z-order)
document.elementsFromPoint(x, y) // [0] = topmost

// Get element position
element.getBoundingClientRect()
// Returns: { x, y, width, height, top, right, bottom, left }

// Check visibility (modern browsers)
element.checkVisibility({
    checkOpacity: true,
    checkVisibilityCSS: true
})

// Scroll into view
element.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
    inline: 'center'
})
```

### Wait Strategies

```javascript
// Selenium (Python)
from selenium.webdriver.support import expected_conditions as EC

EC.element_to_be_clickable(locator)
EC.visibility_of_element_located(locator)
EC.presence_of_element_located(locator)
EC.invisibility_of_element_located(locator)

// Playwright (JavaScript)
await page.waitForSelector(selector, { state: 'visible' })
await page.waitForSelector(selector, { state: 'attached' })
await page.waitForLoadState('networkidle')
await page.waitForTimeout(ms) // Use sparingly

// Custom wait
async function waitUntil(condition, timeout = 5000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        if (await condition()) return true;
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error('Timeout waiting for condition');
}
```

---

## Testing Snippets

### Test Visibility

```javascript
function testVisibility(selector) {
    const el = document.querySelector(selector);
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);

    console.log({
        exists: !!el,
        inDom: document.body.contains(el),
        displayed: style.display !== 'none',
        visible: style.visibility !== 'hidden',
        opacity: style.opacity,
        size: { width: rect.width, height: rect.height },
        inViewport: (
            rect.top < window.innerHeight &&
            rect.bottom > 0 &&
            rect.left < window.innerWidth &&
            rect.right > 0
        )
    });
}
```

### Test Hit Target

```javascript
function testHitTarget(selector) {
    const el = document.querySelector(selector);
    const rect = el.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const hitEl = document.elementFromPoint(centerX, centerY);

    console.log({
        target: el.tagName + (el.id ? `#${el.id}` : ''),
        hitElement: hitEl.tagName + (hitEl.id ? `#${hitEl.id}` : ''),
        isTarget: hitEl === el || el.contains(hitEl),
        obscuredBy: hitEl !== el ? hitEl : null
    });
}
```

### Test Click Path

```javascript
function testClickPath(selector) {
    const el = document.querySelector(selector);
    const rect = el.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const allElements = document.elementsFromPoint(centerX, centerY);

    console.log('Elements in click path (top to bottom):');
    allElements.forEach((el, index) => {
        const style = getComputedStyle(el);
        console.log(`  ${index}. ${el.tagName}${el.id ? '#' + el.id : ''} (z-index: ${style.zIndex})`);
    });

    const targetIndex = allElements.indexOf(el);
    console.log(`\nTarget element is at index: ${targetIndex}`);
    console.log(`Click will hit: ${targetIndex === 0 ? 'TARGET ✓' : 'WRONG ELEMENT ✗'}`);
}
```

---

## Performance Tips

1. **Cache selectors** when clicking multiple times:
   ```javascript
   const button = document.querySelector('#button');
   button.click(); // Fast
   ```

2. **Use ID selectors** when possible:
   ```javascript
   // Fast
   document.getElementById('button')

   // Slower
   document.querySelector('.container .button')
   ```

3. **Batch DOM reads** before writes:
   ```javascript
   // Good: Read, then write
   const rect = element.getBoundingClientRect();
   element.style.left = rect.left + 10 + 'px';

   // Bad: Read-write-read-write causes reflow
   element.style.left = element.getBoundingClientRect().left + 10 + 'px';
   element.style.top = element.getBoundingClientRect().top + 10 + 'px';
   ```

4. **Minimize stability checks** for static content:
   ```javascript
   // For static elements, 2 frames is enough
   await waitForStability(element, 2);

   // For animated elements, use more
   await waitForStability(element, 5);
   ```

5. **Use force click sparingly** - It bypasses important validations:
   ```javascript
   // Only use when you're CERTAIN it's safe
   await page.click(selector, { force: true });
   ```

---

## Error Messages Decoder

| Error | Meaning | Solution |
|-------|---------|----------|
| `ElementClickInterceptedException` | Another element is on top | Dismiss overlay, scroll, or wait |
| `ElementNotInteractableException` | Element can't receive events | Check disabled, pointer-events, visibility |
| `StaleElementReferenceException` | Element was removed from DOM | Re-locate element before click |
| `TimeoutException` | Element didn't appear in time | Increase timeout or check selector |
| `NoSuchElementException` | Element doesn't exist | Check selector or wait for element |
| `ElementNotVisibleException` | Element is hidden | Scroll or wait for element to appear |

---

## Decision Tree

```
Should I click this element?
│
├─ Is element in DOM? ─NO→ Wait or find error
│  └─ YES
│
├─ Is element visible? ─NO→ Scroll into view or wait
│  └─ YES
│
├─ Is element stable? ─NO→ Wait for animation to finish
│  └─ YES
│
├─ Would element receive click? ─NO→ Dismiss overlay
│  └─ YES
│
├─ Is confidence >= threshold? ─NO→ Improve conditions or use alternative
│  └─ YES
│
└─ SAFE TO CLICK ✓
```

---

## Emergency Fallbacks

When all else fails, try in order:

1. **JavaScript Click** (bypasses visual layer):
   ```javascript
   element.click();
   // or
   element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
   ```

2. **Dispatch Events Manually**:
   ```javascript
   element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
   element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
   element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
   ```

3. **Trigger Form Submission** (for submit buttons):
   ```javascript
   element.form.submit();
   ```

4. **Navigate Directly** (for links):
   ```javascript
   window.location.href = element.href;
   ```

5. **Manual Intervention Required** - Log error and alert developer

---

## Further Reading

- **Full Research**: See `CLICK_VALIDATION_RESEARCH.md`
- **Code Examples**: See `IMPLEMENTATION_EXAMPLES.md`
- **Playwright Docs**: https://playwright.dev/docs/actionability
- **Selenium Waits**: https://www.selenium.dev/documentation/webdriver/waits/
- **MDN elementFromPoint**: https://developer.mozilla.org/en-US/docs/Web/API/Document/elementFromPoint
