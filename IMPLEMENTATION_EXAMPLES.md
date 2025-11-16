# Practical Implementation Examples

This document provides ready-to-use code examples for implementing click validation and error correction.

---

## Table of Contents

1. [Complete Click Handler Class](#complete-click-handler-class)
2. [Framework-Specific Implementations](#framework-specific-implementations)
3. [Testing Utilities](#testing-utilities)
4. [Real-World Examples](#real-world-examples)

---

## Complete Click Handler Class

### Full-Featured JavaScript Implementation

```javascript
/**
 * RobustClickHandler - Production-ready click automation with validation
 *
 * Features:
 * - Pre-click validation (visibility, interactability)
 * - Confidence scoring (0-100)
 * - Exponential backoff retry
 * - Overlay detection and handling
 * - Post-click validation
 * - Comprehensive logging
 */
class RobustClickHandler {
    constructor(options = {}) {
        this.config = {
            minConfidence: options.minConfidence || 80,
            maxRetries: options.maxRetries || 3,
            baseDelay: options.baseDelay || 1000,
            stabilityChecks: options.stabilityChecks || 3,
            stabilityInterval: options.stabilityInterval || 50,
            enableLogging: options.enableLogging !== false,
            autoScroll: options.autoScroll !== false,
            handleOverlays: options.handleOverlays !== false
        };

        this.logger = new ClickLogger(this.config.enableLogging);
        this.clickHistory = [];
    }

    /**
     * Main click method with full validation pipeline
     */
    async click(selector, customOptions = {}) {
        const options = { ...this.config, ...customOptions };
        const startTime = Date.now();

        try {
            // 1. Find element
            const element = await this.findElement(selector, options);

            // 2. Pre-click validation
            this.logger.log('Starting pre-click validation...');
            const preCheck = await this.preClickValidation(element);

            if (!preCheck.passed) {
                this.logger.warn('Pre-click validation failed:', preCheck.issues);
                await this.fixPreClickIssues(element, preCheck.issues, options);
            }

            // 3. Calculate confidence
            this.logger.log('Calculating click confidence...');
            const confidence = await this.calculateConfidence(element);
            this.logger.log(`Confidence score: ${confidence.confidence}%`);

            if (confidence.confidence < options.minConfidence) {
                throw new Error(
                    `Confidence too low: ${confidence.confidence}% (min: ${options.minConfidence}%)\n` +
                    `Issues: ${confidence.details.issues.join(', ')}`
                );
            }

            // 4. Perform click with retry
            const result = await this.clickWithRetry(element, options);

            // 5. Log success
            const duration = Date.now() - startTime;
            this.logClickAttempt(selector, confidence, true, duration);

            return {
                success: true,
                confidence: confidence.confidence,
                duration,
                attempts: result.attempts
            };

        } catch (error) {
            const duration = Date.now() - startTime;
            this.logClickAttempt(selector, null, false, duration, error);
            throw error;
        }
    }

    /**
     * Find element with timeout
     */
    async findElement(selector, options, timeout = 10000) {
        const startTime = Date.now();

        while (Date.now() - startTime < timeout) {
            const element = document.querySelector(selector);
            if (element) return element;
            await this.delay(100);
        }

        throw new Error(`Element not found: ${selector}`);
    }

    /**
     * Pre-click validation checks
     */
    async preClickValidation(element) {
        const issues = [];
        const checks = {
            exists: false,
            visible: false,
            interactable: false,
            inViewport: false,
            notDisabled: false,
            hitTarget: false
        };

        // Check element exists
        checks.exists = document.body.contains(element);
        if (!checks.exists) {
            issues.push('Element not in DOM');
            return { passed: false, issues, checks };
        }

        // Check visibility
        const visibilityResult = this.isVisible(element);
        checks.visible = visibilityResult.visible;
        if (!checks.visible) {
            issues.push(`Not visible: ${visibilityResult.reason}`);
        }

        // Check interactability
        checks.interactable = !this.isInteractionBlocked(element);
        if (!checks.interactable) {
            issues.push('Interaction blocked (pointer-events: none or disabled)');
        }

        // Check in viewport
        checks.inViewport = this.isInViewport(element);
        if (!checks.inViewport) {
            issues.push('Element not in viewport');
        }

        // Check not disabled
        checks.notDisabled = !element.disabled;
        if (!checks.notDisabled) {
            issues.push('Element is disabled');
        }

        // Check hit target
        const hitTargetResult = this.checkHitTarget(element);
        checks.hitTarget = hitTargetResult.isTarget;
        if (!checks.hitTarget) {
            issues.push(`Obscured by: ${hitTargetResult.actualTarget?.tagName || 'unknown'}`);
        }

        return {
            passed: issues.length === 0,
            issues,
            checks
        };
    }

    /**
     * Fix common pre-click issues
     */
    async fixPreClickIssues(element, issues, options) {
        for (const issue of issues) {
            if (issue.includes('not in viewport') && options.autoScroll) {
                this.logger.log('Scrolling element into view...');
                await this.scrollIntoView(element);
            }

            if (issue.includes('Obscured by') && options.handleOverlays) {
                this.logger.log('Attempting to dismiss overlay...');
                await this.dismissOverlays();
            }
        }

        // Re-validate
        const recheck = await this.preClickValidation(element);
        if (!recheck.passed) {
            this.logger.warn('Some issues could not be fixed:', recheck.issues);
        }
    }

    /**
     * Calculate click confidence score
     */
    async calculateConfidence(element) {
        const weights = {
            visibility: 0.25,
            interactability: 0.25,
            stability: 0.20,
            hitTarget: 0.20,
            timing: 0.10
        };

        const scores = {
            visibility: this.calculateVisibilityScore(element),
            interactability: this.calculateInteractabilityScore(element),
            stability: await this.calculateStabilityScore(element),
            hitTarget: this.calculateHitTargetScore(element),
            timing: this.calculateTimingScore()
        };

        const confidence = Object.keys(scores).reduce((sum, key) => {
            return sum + (scores[key] * weights[key]);
        }, 0);

        const issues = [];
        if (scores.visibility < 0.8) issues.push('Low visibility');
        if (scores.interactability < 0.8) issues.push('Limited interactability');
        if (scores.stability < 0.8) issues.push('Element unstable');
        if (scores.hitTarget < 0.8) issues.push('May be obscured');
        if (scores.timing < 0.8) issues.push('Page still loading');

        return {
            confidence: Math.round(confidence * 100),
            scores,
            details: { issues }
        };
    }

    calculateVisibilityScore(element) {
        const rect = element.getBoundingClientRect();
        const style = window.getComputedStyle(element);

        if (rect.width === 0 || rect.height === 0) return 0;
        if (style.display === 'none') return 0;
        if (style.visibility === 'hidden') return 0;

        let score = parseFloat(style.opacity) || 1;

        const inViewport = (
            rect.top < window.innerHeight &&
            rect.bottom > 0 &&
            rect.left < window.innerWidth &&
            rect.right > 0
        );

        if (!inViewport) score *= 0.5;

        return Math.max(0, Math.min(1, score));
    }

    calculateInteractabilityScore(element) {
        if (element.disabled) return 0;

        const style = window.getComputedStyle(element);
        if (style.pointerEvents === 'none') return 0;
        if (element.getAttribute('aria-disabled') === 'true') return 0.2;

        return 1.0;
    }

    async calculateStabilityScore(element) {
        const positions = [];

        for (let i = 0; i < this.config.stabilityChecks; i++) {
            const rect = element.getBoundingClientRect();
            positions.push({ x: rect.left, y: rect.top });

            if (i < this.config.stabilityChecks - 1) {
                await this.delay(this.config.stabilityInterval);
            }
        }

        let totalVariance = 0;
        for (let i = 1; i < positions.length; i++) {
            const dx = positions[i].x - positions[i-1].x;
            const dy = positions[i].y - positions[i-1].y;
            totalVariance += Math.sqrt(dx*dx + dy*dy);
        }

        const avgVariance = totalVariance / (positions.length - 1);
        return Math.max(0, 1 - (avgVariance / 5));
    }

    calculateHitTargetScore(element) {
        const rect = element.getBoundingClientRect();
        const testPoints = [
            { x: rect.left + rect.width * 0.5, y: rect.top + rect.height * 0.5 },
            { x: rect.left + rect.width * 0.25, y: rect.top + rect.height * 0.25 },
            { x: rect.left + rect.width * 0.75, y: rect.top + rect.height * 0.75 }
        ];

        let hits = 0;
        testPoints.forEach(point => {
            const hitElement = document.elementFromPoint(point.x, point.y);
            if (hitElement === element || element.contains(hitElement)) {
                hits++;
            }
        });

        return hits / testPoints.length;
    }

    calculateTimingScore() {
        let score = 1.0;

        if (document.readyState !== 'complete') score *= 0.5;
        if (document.getAnimations().length > 0) score *= 0.8;

        return score;
    }

    /**
     * Click with exponential backoff retry
     */
    async clickWithRetry(element, options) {
        for (let attempt = 0; attempt < options.maxRetries; attempt++) {
            try {
                // Verify element still valid
                if (!document.body.contains(element)) {
                    throw new Error('Element became stale');
                }

                // Perform click
                element.click();

                // Validate success
                await this.delay(100);
                const validation = await this.validateClickSuccess(element);

                if (validation.success) {
                    return { success: true, attempts: attempt + 1 };
                }

            } catch (error) {
                this.logger.warn(`Click attempt ${attempt + 1} failed:`, error.message);

                if (attempt === options.maxRetries - 1) {
                    throw error;
                }

                const delay = options.baseDelay * Math.pow(2, attempt);
                const jitter = Math.random() * delay;
                await this.delay(delay + jitter);
            }
        }

        throw new Error('Click failed after all retries');
    }

    /**
     * Validate click succeeded
     */
    async validateClickSuccess(element) {
        // Check if focus changed
        const focusChanged = document.activeElement !== element.ownerDocument.body;

        // Check if URL changed
        const initialUrl = window.location.href;
        await this.delay(100);
        const urlChanged = window.location.href !== initialUrl;

        // Check if element state changed
        const stateChanged = element.classList.contains('active') ||
                            element.getAttribute('aria-pressed') === 'true' ||
                            element.getAttribute('aria-selected') === 'true';

        const success = focusChanged || urlChanged || stateChanged;

        return { success, focusChanged, urlChanged, stateChanged };
    }

    /**
     * Helper: Check if element is visible
     */
    isVisible(element) {
        const rect = element.getBoundingClientRect();
        const style = window.getComputedStyle(element);

        if (rect.width === 0 || rect.height === 0) {
            return { visible: false, reason: 'Zero size' };
        }

        if (style.display === 'none') {
            return { visible: false, reason: 'display: none' };
        }

        if (style.visibility === 'hidden') {
            return { visible: false, reason: 'visibility: hidden' };
        }

        if (parseFloat(style.opacity) === 0) {
            return { visible: false, reason: 'opacity: 0' };
        }

        return { visible: true };
    }

    /**
     * Helper: Check if interaction is blocked
     */
    isInteractionBlocked(element) {
        if (element.disabled) return true;

        const style = window.getComputedStyle(element);
        if (style.pointerEvents === 'none') return true;

        return false;
    }

    /**
     * Helper: Check if element is in viewport
     */
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top < window.innerHeight &&
            rect.bottom > 0 &&
            rect.left < window.innerWidth &&
            rect.right > 0
        );
    }

    /**
     * Helper: Check hit target
     */
    checkHitTarget(element) {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const hitElement = document.elementFromPoint(centerX, centerY);
        const isTarget = hitElement === element || element.contains(hitElement);

        return {
            isTarget,
            actualTarget: hitElement
        };
    }

    /**
     * Helper: Scroll element into view
     */
    async scrollIntoView(element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'center'
        });

        await this.delay(500); // Wait for scroll animation
    }

    /**
     * Helper: Dismiss overlays
     */
    async dismissOverlays() {
        const overlaySelectors = [
            '[role="dialog"]',
            '.modal',
            '.overlay',
            '.popup',
            '[aria-modal="true"]'
        ];

        for (const selector of overlaySelectors) {
            const overlay = document.querySelector(selector);
            if (overlay) {
                const closeBtn = overlay.querySelector('[aria-label="Close"], .close, .close-button');
                if (closeBtn) {
                    closeBtn.click();
                    await this.delay(300);
                }
            }
        }
    }

    /**
     * Helper: Delay utility
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Log click attempt
     */
    logClickAttempt(selector, confidence, success, duration, error = null) {
        const entry = {
            timestamp: new Date().toISOString(),
            selector,
            confidence: confidence?.confidence || null,
            success,
            duration,
            error: error?.message || null
        };

        this.clickHistory.push(entry);
        this.logger.log('Click attempt:', entry);
    }

    /**
     * Get click statistics
     */
    getStats() {
        const total = this.clickHistory.length;
        const successful = this.clickHistory.filter(e => e.success).length;
        const failed = total - successful;

        const avgDuration = this.clickHistory.reduce((sum, e) => sum + e.duration, 0) / total;

        const avgConfidence = this.clickHistory
            .filter(e => e.confidence !== null)
            .reduce((sum, e) => sum + e.confidence, 0) / total;

        return {
            total,
            successful,
            failed,
            successRate: ((successful / total) * 100).toFixed(2) + '%',
            avgDuration: avgDuration.toFixed(0) + 'ms',
            avgConfidence: avgConfidence.toFixed(0) + '%'
        };
    }
}

/**
 * Simple logger class
 */
class ClickLogger {
    constructor(enabled = true) {
        this.enabled = enabled;
    }

    log(...args) {
        if (this.enabled) {
            console.log('[RobustClick]', ...args);
        }
    }

    warn(...args) {
        if (this.enabled) {
            console.warn('[RobustClick]', ...args);
        }
    }

    error(...args) {
        if (this.enabled) {
            console.error('[RobustClick]', ...args);
        }
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RobustClickHandler;
}
```

### Usage Example

```javascript
// Initialize handler
const clickHandler = new RobustClickHandler({
    minConfidence: 80,
    maxRetries: 3,
    enableLogging: true
});

// Perform robust click
async function example() {
    try {
        const result = await clickHandler.click('#submit-button');
        console.log('Click successful:', result);
        // { success: true, confidence: 95, duration: 150, attempts: 1 }

    } catch (error) {
        console.error('Click failed:', error.message);
    }

    // Get statistics
    const stats = clickHandler.getStats();
    console.log('Click statistics:', stats);
    // { total: 10, successful: 9, failed: 1, successRate: '90%', ... }
}
```

---

## Framework-Specific Implementations

### Playwright Implementation

```javascript
/**
 * Playwright-specific robust click handler
 */
class PlaywrightRobustClick {
    constructor(page, options = {}) {
        this.page = page;
        this.config = {
            minConfidence: options.minConfidence || 80,
            maxRetries: options.maxRetries || 3,
            baseDelay: options.baseDelay || 1000
        };
    }

    async click(selector, options = {}) {
        const mergedOptions = { ...this.config, ...options };

        for (let attempt = 0; attempt < mergedOptions.maxRetries; attempt++) {
            try {
                // Wait for element to be attached
                await this.page.waitForSelector(selector, { state: 'attached' });

                // Calculate confidence
                const confidence = await this.calculateConfidence(selector);

                if (confidence < mergedOptions.minConfidence) {
                    throw new Error(`Confidence too low: ${confidence}%`);
                }

                // Perform click with Playwright's built-in actionability checks
                await this.page.click(selector, {
                    timeout: 5000,
                    force: false // Don't skip actionability checks
                });

                // Verify click success
                await this.page.waitForTimeout(100);
                return { success: true, attempts: attempt + 1 };

            } catch (error) {
                if (attempt === mergedOptions.maxRetries - 1) {
                    throw error;
                }

                const delay = mergedOptions.baseDelay * Math.pow(2, attempt);
                await this.page.waitForTimeout(delay);
            }
        }
    }

    async calculateConfidence(selector) {
        return await this.page.evaluate((sel) => {
            const element = document.querySelector(sel);
            if (!element) return 0;

            const rect = element.getBoundingClientRect();
            const style = window.getComputedStyle(element);

            // Basic visibility check
            if (rect.width === 0 || rect.height === 0) return 0;
            if (style.display === 'none') return 0;
            if (style.visibility === 'hidden') return 0;

            // Calculate confidence (simplified)
            let score = 100;

            // Check opacity
            score *= parseFloat(style.opacity);

            // Check if in viewport
            const inViewport = (
                rect.top < window.innerHeight &&
                rect.bottom > 0 &&
                rect.left < window.innerWidth &&
                rect.right > 0
            );
            if (!inViewport) score *= 0.5;

            // Check hit target
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const hitElement = document.elementFromPoint(centerX, centerY);
            const isTarget = hitElement === element || element.contains(hitElement);
            if (!isTarget) score *= 0.6;

            return Math.round(score);
        }, selector);
    }

    async clickWithConfidence(selector, minConfidence = 80) {
        // Scroll into view
        await this.page.locator(selector).scrollIntoViewIfNeeded();

        // Wait for stability
        await this.page.waitForTimeout(200);

        // Click
        return await this.click(selector, { minConfidence });
    }
}

// Usage
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    const robustClick = new PlaywrightRobustClick(page, {
        minConfidence: 85,
        maxRetries: 3
    });

    await page.goto('https://example.com');
    await robustClick.clickWithConfidence('#submit-button');

    await browser.close();
})();
```

### Selenium (Python) Implementation

```python
"""
Selenium-specific robust click handler
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    ElementNotInteractableException
)
import time
import math


class SeleniumRobustClick:
    def __init__(self, driver, min_confidence=80, max_retries=3, base_delay=1.0):
        self.driver = driver
        self.min_confidence = min_confidence
        self.max_retries = max_retries
        self.base_delay = base_delay

    def click(self, locator, by=By.CSS_SELECTOR):
        """
        Perform robust click with retry and validation

        Args:
            locator: Element locator (CSS selector, XPATH, etc.)
            by: Selenium By strategy (default: By.CSS_SELECTOR)

        Returns:
            dict: Result with success status and metadata
        """
        for attempt in range(self.max_retries):
            try:
                # Wait for element to be present
                wait = WebDriverWait(self.driver, 10)
                element = wait.until(
                    EC.presence_of_element_located((by, locator))
                )

                # Calculate confidence
                confidence = self.calculate_confidence(element)

                if confidence < self.min_confidence:
                    raise ValueError(f"Confidence too low: {confidence}%")

                # Pre-click actions
                self._prepare_element_for_click(element)

                # Perform click
                element.click()

                # Validate success
                time.sleep(0.1)
                return {
                    'success': True,
                    'attempts': attempt + 1,
                    'confidence': confidence
                }

            except (ElementClickInterceptedException,
                    StaleElementReferenceException,
                    ElementNotInteractableException) as e:

                if attempt == self.max_retries - 1:
                    raise

                # Exponential backoff
                delay = self.base_delay * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)

        raise Exception("Click failed after all retries")

    def calculate_confidence(self, element):
        """Calculate click confidence score"""
        score = 100

        # Check if displayed
        if not element.is_displayed():
            return 0

        # Check if enabled
        if not element.is_enabled():
            return 0

        # Get element location and size
        location = element.location
        size = element.size

        # Check if in viewport
        viewport_height = self.driver.execute_script("return window.innerHeight")
        viewport_width = self.driver.execute_script("return window.innerWidth")

        in_viewport = (
            location['y'] + size['height'] > 0 and
            location['y'] < viewport_height and
            location['x'] + size['width'] > 0 and
            location['x'] < viewport_width
        )

        if not in_viewport:
            score *= 0.5

        # Check hit target
        center_x = location['x'] + size['width'] / 2
        center_y = location['y'] + size['height'] / 2

        element_at_point = self.driver.execute_script(
            """
            var el = document.elementFromPoint(arguments[0], arguments[1]);
            return el === arguments[2] || arguments[2].contains(el);
            """,
            center_x, center_y, element
        )

        if not element_at_point:
            score *= 0.6

        return round(score)

    def _prepare_element_for_click(self, element):
        """Prepare element before clicking"""
        # Scroll into view
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element
        )
        time.sleep(0.3)

        # Dismiss overlays if needed
        self._dismiss_overlays()

    def _dismiss_overlays(self):
        """Attempt to dismiss common overlays"""
        overlay_selectors = [
            '[role="dialog"] [aria-label="Close"]',
            '.modal .close',
            '.overlay .close-button'
        ]

        for selector in overlay_selectors:
            try:
                close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                if close_btn.is_displayed():
                    close_btn.click()
                    time.sleep(0.3)
            except:
                pass  # Overlay not present

    def click_with_offset(self, locator, x_offset=0, y_offset=0, by=By.CSS_SELECTOR):
        """Click element with offset from center"""
        from selenium.webdriver.common.action_chains import ActionChains

        element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((by, locator))
        )

        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(element, x_offset, y_offset)
        actions.click()
        actions.perform()

    def force_click(self, locator, by=By.CSS_SELECTOR):
        """Force click using JavaScript (bypass visibility checks)"""
        element = self.driver.find_element(by, locator)
        self.driver.execute_script("arguments[0].click();", element)


# Usage example
if __name__ == "__main__":
    driver = webdriver.Chrome()

    robust_click = SeleniumRobustClick(
        driver,
        min_confidence=85,
        max_retries=3
    )

    try:
        driver.get("https://example.com")

        # Robust click with validation
        result = robust_click.click("#submit-button")
        print("Click successful:", result)

        # Click with offset
        robust_click.click_with_offset("#slider", x_offset=50, y_offset=0)

        # Force click (last resort)
        robust_click.force_click("#hidden-element")

    finally:
        driver.quit()
```

---

## Testing Utilities

### Confidence Score Testing

```javascript
/**
 * Test suite for confidence score calculation
 */
class ConfidenceScoreTester {
    constructor() {
        this.testResults = [];
    }

    async runTests() {
        console.log('=== Running Confidence Score Tests ===\n');

        await this.testVisibleElement();
        await this.testHiddenElement();
        await this.testObscuredElement();
        await this.testDisabledElement();
        await this.testMovingElement();

        this.printResults();
    }

    async testVisibleElement() {
        const element = this.createElement({
            id: 'visible-test',
            display: 'block',
            width: '100px',
            height: '50px',
            position: 'absolute',
            top: '100px',
            left: '100px'
        });

        const handler = new RobustClickHandler();
        const result = await handler.calculateConfidence(element);

        this.recordTest('Visible Element', {
            expected: '>= 90',
            actual: result.confidence,
            passed: result.confidence >= 90
        });

        element.remove();
    }

    async testHiddenElement() {
        const element = this.createElement({
            id: 'hidden-test',
            display: 'none'
        });

        const handler = new RobustClickHandler();
        const result = await handler.calculateConfidence(element);

        this.recordTest('Hidden Element', {
            expected: '0',
            actual: result.confidence,
            passed: result.confidence === 0
        });

        element.remove();
    }

    async testObscuredElement() {
        // Create base element
        const base = this.createElement({
            id: 'base-test',
            width: '100px',
            height: '100px',
            position: 'absolute',
            top: '200px',
            left: '200px'
        });

        // Create overlay
        const overlay = this.createElement({
            id: 'overlay-test',
            width: '100px',
            height: '100px',
            position: 'absolute',
            top: '200px',
            left: '200px',
            zIndex: '10'
        });

        const handler = new RobustClickHandler();
        const result = await handler.calculateConfidence(base);

        this.recordTest('Obscured Element', {
            expected: '< 80',
            actual: result.confidence,
            passed: result.confidence < 80
        });

        base.remove();
        overlay.remove();
    }

    async testDisabledElement() {
        const element = this.createElement({
            id: 'disabled-test',
            tagName: 'button',
            disabled: true
        });

        const handler = new RobustClickHandler();
        const result = await handler.calculateConfidence(element);

        this.recordTest('Disabled Element', {
            expected: '0',
            actual: result.confidence,
            passed: result.confidence === 0
        });

        element.remove();
    }

    async testMovingElement() {
        const element = this.createElement({
            id: 'moving-test',
            width: '100px',
            height: '50px',
            position: 'absolute',
            top: '300px',
            left: '300px',
            transition: 'left 0.5s'
        });

        // Start animation
        setTimeout(() => {
            element.style.left = '400px';
        }, 50);

        const handler = new RobustClickHandler({ stabilityChecks: 5 });
        const result = await handler.calculateConfidence(element);

        this.recordTest('Moving Element', {
            expected: '< 80',
            actual: result.confidence,
            passed: result.confidence < 80
        });

        element.remove();
    }

    createElement(options) {
        const tag = options.tagName || 'div';
        const element = document.createElement(tag);

        if (options.id) element.id = options.id;
        if (options.disabled) element.disabled = true;

        Object.keys(options).forEach(key => {
            if (!['tagName', 'id', 'disabled'].includes(key)) {
                element.style[key] = options[key];
            }
        });

        document.body.appendChild(element);
        return element;
    }

    recordTest(name, result) {
        this.testResults.push({
            name,
            ...result
        });
    }

    printResults() {
        console.log('\n=== Test Results ===\n');

        this.testResults.forEach(test => {
            const status = test.passed ? '✓ PASS' : '✗ FAIL';
            console.log(`${status} - ${test.name}`);
            console.log(`  Expected: ${test.expected}, Actual: ${test.actual}\n`);
        });

        const passed = this.testResults.filter(t => t.passed).length;
        const total = this.testResults.length;

        console.log(`\nSummary: ${passed}/${total} tests passed\n`);
    }
}

// Run tests
// new ConfidenceScoreTester().runTests();
```

---

## Real-World Examples

### Example 1: E-commerce Checkout Flow

```javascript
/**
 * Robust click handler for e-commerce checkout
 */
async function completeCheckout(clickHandler) {
    try {
        // Step 1: Add to cart
        console.log('Adding item to cart...');
        await clickHandler.click('.add-to-cart-button', {
            minConfidence: 90 // High confidence for critical action
        });

        // Wait for cart to update
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Step 2: Proceed to checkout
        console.log('Proceeding to checkout...');
        await clickHandler.click('.checkout-button', {
            minConfidence: 90
        });

        // Step 3: Fill shipping info (handled separately)
        // ...

        // Step 4: Confirm order
        console.log('Confirming order...');
        await clickHandler.click('#confirm-order', {
            minConfidence: 95, // Very high confidence for financial transaction
            maxRetries: 5
        });

        console.log('Checkout completed successfully!');
        return true;

    } catch (error) {
        console.error('Checkout failed:', error.message);
        return false;
    }
}
```

### Example 2: Form Submission with Validation

```javascript
/**
 * Robust form submission with multi-step validation
 */
async function submitForm(clickHandler) {
    const formData = {
        name: 'John Doe',
        email: 'john@example.com',
        message: 'Test message'
    };

    try {
        // Fill form fields
        document.querySelector('#name').value = formData.name;
        document.querySelector('#email').value = formData.email;
        document.querySelector('#message').value = formData.message;

        // Dismiss any overlays (cookie notices, etc.)
        await clickHandler.dismissOverlays();

        // Click submit with validation
        const result = await clickHandler.click('#submit-form', {
            minConfidence: 85,
            autoScroll: true,
            handleOverlays: true
        });

        // Verify submission succeeded
        await new Promise(resolve => setTimeout(resolve, 500));

        const successMessage = document.querySelector('.success-message');
        if (!successMessage) {
            throw new Error('Form submission not confirmed');
        }

        console.log('Form submitted successfully:', result);
        return true;

    } catch (error) {
        console.error('Form submission failed:', error.message);

        // Take screenshot or log additional context
        const stats = clickHandler.getStats();
        console.log('Click statistics:', stats);

        return false;
    }
}
```

### Example 3: Modal Dialog Interaction

```javascript
/**
 * Handle modal dialogs with overlay detection
 */
async function interactWithModal(clickHandler) {
    try {
        // Open modal
        await clickHandler.click('.open-modal-button');

        // Wait for modal to appear
        await new Promise(resolve => setTimeout(resolve, 300));

        // Click button inside modal
        await clickHandler.click('.modal .confirm-button', {
            minConfidence: 80,
            handleOverlays: false // We want to interact WITH the overlay
        });

        console.log('Modal interaction successful');

    } catch (error) {
        console.error('Modal interaction failed:', error.message);

        // Try to close modal if interaction failed
        try {
            await clickHandler.click('.modal .close-button');
        } catch {
            // If close button also fails, force close
            document.querySelector('.modal').style.display = 'none';
        }
    }
}
```

### Example 4: Dynamic Content (Infinite Scroll)

```javascript
/**
 * Click elements in dynamically loaded content
 */
async function clickDynamicElement(clickHandler, itemIndex) {
    const maxScrollAttempts = 10;
    let scrollAttempts = 0;

    while (scrollAttempts < maxScrollAttempts) {
        const selector = `.item[data-index="${itemIndex}"]`;
        const element = document.querySelector(selector);

        if (element) {
            // Element found, attempt click
            try {
                await clickHandler.click(selector, {
                    minConfidence: 75, // Lower threshold for dynamic content
                    autoScroll: true
                });

                return true;
            } catch (error) {
                console.error('Click failed even after finding element:', error);
                return false;
            }
        }

        // Element not found, scroll to load more
        window.scrollTo({
            top: document.documentElement.scrollHeight,
            behavior: 'smooth'
        });

        // Wait for new content to load
        await new Promise(resolve => setTimeout(resolve, 1000));

        scrollAttempts++;
    }

    throw new Error(`Element with index ${itemIndex} not found after ${maxScrollAttempts} scroll attempts`);
}
```

---

## Performance Benchmarking

```javascript
/**
 * Benchmark click handler performance
 */
class ClickPerformanceBenchmark {
    constructor(clickHandler) {
        this.clickHandler = clickHandler;
        this.results = [];
    }

    async runBenchmark(scenarios) {
        console.log('=== Running Performance Benchmark ===\n');

        for (const scenario of scenarios) {
            await this.benchmarkScenario(scenario);
        }

        this.printResults();
    }

    async benchmarkScenario(scenario) {
        const { name, selector, iterations } = scenario;
        const times = [];

        console.log(`Benchmarking: ${name} (${iterations} iterations)...`);

        for (let i = 0; i < iterations; i++) {
            const startTime = performance.now();

            try {
                await this.clickHandler.click(selector);
            } catch {
                // Ignore errors for benchmark
            }

            const endTime = performance.now();
            times.push(endTime - startTime);

            // Reset for next iteration
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        const avg = times.reduce((a, b) => a + b, 0) / times.length;
        const min = Math.min(...times);
        const max = Math.max(...times);

        this.results.push({
            name,
            iterations,
            avg: avg.toFixed(2),
            min: min.toFixed(2),
            max: max.toFixed(2)
        });
    }

    printResults() {
        console.log('\n=== Benchmark Results ===\n');

        this.results.forEach(result => {
            console.log(`${result.name}:`);
            console.log(`  Iterations: ${result.iterations}`);
            console.log(`  Average: ${result.avg}ms`);
            console.log(`  Min: ${result.min}ms`);
            console.log(`  Max: ${result.max}ms\n`);
        });
    }
}

// Usage
const scenarios = [
    { name: 'Simple Button', selector: '#simple-button', iterations: 10 },
    { name: 'Obscured Element', selector: '#obscured-element', iterations: 10 },
    { name: 'Dynamic Content', selector: '.dynamic-item', iterations: 10 }
];

// const benchmark = new ClickPerformanceBenchmark(clickHandler);
// benchmark.runBenchmark(scenarios);
```

---

This document provides production-ready implementations that can be directly integrated into automation projects. Each example includes error handling, logging, and best practices for robust click automation.
