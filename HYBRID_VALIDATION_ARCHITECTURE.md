# Hybrid Validation Architecture
## Combining Vision with Coordinate Systems for Robust UI Automation

---

## Overview

This document describes a comprehensive architecture for validating OS-to-DOM coordinate transformations using a hybrid approach that combines:
- Traditional coordinate system mathematics
- Computer vision validation
- AI-powered semantic understanding
- Real-time verification

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinate Action Request                 │
│              (Click at OS coords: x=500, y=300)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Coordinate Transformation Layer                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │OS Coordinates│→ │Browser Coords│→ │DOM Coordinates│      │
│  │  (x, y)      │  │  (bx, by)    │  │  (dx, dy)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         Account for:                                         │
│         - Display scaling (DPI)                              │
│         - Browser window position                            │
│         - Browser chrome height                              │
│         - Scroll position                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Pre-Action Validation Layer                     │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Vision-Based   │  │  AI Semantic   │  │  Coordinate  │  │
│  │  Validation    │  │   Validation   │  │  Math Check  │  │
│  └────────┬───────┘  └───────┬────────┘  └──────┬───────┘  │
│           │                   │                   │          │
│           └───────────────────┴───────────────────┘          │
│                              │                               │
│                       Confidence Aggregator                  │
│                              │                               │
│                    ┌─────────▼─────────┐                    │
│                    │  Confidence > 0.8? │                   │
│                    └─────────┬─────────┘                    │
│                              │                               │
└──────────────────────────────┼───────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │ NO                          │ YES
                ▼                             ▼
        ┌───────────────┐           ┌─────────────────┐
        │  Retry with   │           │  Execute Action │
        │  Alternative  │           │   (Click, Type) │
        │   Strategy    │           └────────┬────────┘
        └───────────────┘                    │
                                             ▼
                                ┌─────────────────────────┐
                                │ Post-Action Validation  │
                                │  - State change check   │
                                │  - Visual verification  │
                                │  - Outcome validation   │
                                └─────────┬───────────────┘
                                          │
                                          ▼
                                ┌──────────────────┐
                                │  Result Report   │
                                │  with Confidence │
                                └──────────────────┘
```

---

## 2. Detailed Component Design

### 2.1 Coordinate Transformation Layer

```python
import platform
import ctypes
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class DisplayInfo:
    """Display/screen information"""
    width: int
    height: int
    scale_factor: float
    dpi: int

@dataclass
class BrowserInfo:
    """Browser window information"""
    x: int  # Window position
    y: int
    width: int
    height: int
    chrome_height: int  # Browser UI height
    scroll_x: int  # Scroll position
    scroll_y: int

class CoordinateTransformationEngine:
    """
    Handles all coordinate transformations with platform-specific logic
    """

    def __init__(self):
        self.platform = platform.system()
        self.display_info = self._get_display_info()

    def _get_display_info(self) -> DisplayInfo:
        """Get platform-specific display information"""
        if self.platform == "Windows":
            return self._get_windows_display_info()
        elif self.platform == "Darwin":  # macOS
            return self._get_macos_display_info()
        elif self.platform == "Linux":
            return self._get_linux_display_info()
        else:
            raise NotImplementedError(f"Platform {self.platform} not supported")

    def _get_windows_display_info(self) -> DisplayInfo:
        """Get Windows display information including DPI scaling"""
        user32 = ctypes.windll.user32

        # Get DPI awareness
        user32.SetProcessDPIAware()

        # Get screen dimensions
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)

        # Get DPI
        hdc = user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        user32.ReleaseDC(0, hdc)

        scale_factor = dpi / 96.0  # 96 DPI is 100% scaling

        return DisplayInfo(
            width=width,
            height=height,
            scale_factor=scale_factor,
            dpi=dpi
        )

    def _get_macos_display_info(self) -> DisplayInfo:
        """Get macOS display information including Retina scaling"""
        try:
            from AppKit import NSScreen
            screen = NSScreen.mainScreen()
            frame = screen.frame()
            scale = screen.backingScaleFactor()

            return DisplayInfo(
                width=int(frame.size.width),
                height=int(frame.size.height),
                scale_factor=float(scale),
                dpi=int(96 * scale)  # macOS base DPI
            )
        except ImportError:
            # Fallback if AppKit not available
            import subprocess
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True,
                text=True
            )
            # Parse output for display info
            return DisplayInfo(width=1920, height=1080, scale_factor=2.0, dpi=192)

    def _get_linux_display_info(self) -> DisplayInfo:
        """Get Linux display information"""
        try:
            import Xlib.display
            display = Xlib.display.Display()
            screen = display.screen()

            width = screen.width_in_pixels
            height = screen.height_in_pixels

            # Get DPI from Xresources or use default
            dpi = 96  # Default
            try:
                xrdb = subprocess.run(
                    ['xrdb', '-query'],
                    capture_output=True,
                    text=True
                )
                for line in xrdb.stdout.split('\n'):
                    if 'Xft.dpi' in line:
                        dpi = int(line.split(':')[1].strip())
            except:
                pass

            return DisplayInfo(
                width=width,
                height=height,
                scale_factor=dpi / 96.0,
                dpi=dpi
            )
        except ImportError:
            # Fallback
            return DisplayInfo(width=1920, height=1080, scale_factor=1.0, dpi=96)

    def os_to_browser(
        self,
        os_x: int,
        os_y: int,
        browser_info: BrowserInfo
    ) -> Tuple[int, int]:
        """
        Transform OS coordinates to browser viewport coordinates

        Args:
            os_x, os_y: OS/screen coordinates
            browser_info: Browser window information

        Returns:
            Browser viewport coordinates (x, y)
        """
        # Account for browser window position
        browser_x = os_x - browser_info.x

        # Account for browser chrome (address bar, tabs, etc.)
        browser_y = os_y - browser_info.y - browser_info.chrome_height

        # Account for display scaling
        browser_x = int(browser_x / self.display_info.scale_factor)
        browser_y = int(browser_y / self.display_info.scale_factor)

        return (browser_x, browser_y)

    def browser_to_dom(
        self,
        browser_x: int,
        browser_y: int,
        browser_info: BrowserInfo
    ) -> Tuple[int, int]:
        """
        Transform browser viewport coordinates to DOM coordinates

        Args:
            browser_x, browser_y: Browser viewport coordinates
            browser_info: Browser information including scroll

        Returns:
            DOM coordinates (x, y)
        """
        dom_x = browser_x + browser_info.scroll_x
        dom_y = browser_y + browser_info.scroll_y

        return (dom_x, dom_y)

    def os_to_dom(
        self,
        os_x: int,
        os_y: int,
        browser_info: BrowserInfo
    ) -> Tuple[int, int]:
        """
        Direct OS to DOM transformation

        Args:
            os_x, os_y: OS coordinates
            browser_info: Browser information

        Returns:
            DOM coordinates (x, y)
        """
        browser_x, browser_y = self.os_to_browser(os_x, os_y, browser_info)
        dom_x, dom_y = self.browser_to_dom(browser_x, browser_y, browser_info)

        return (dom_x, dom_y)

    def calculate_transformation_error(
        self,
        os_coords: Tuple[int, int],
        expected_dom_coords: Tuple[int, int],
        browser_info: BrowserInfo
    ) -> float:
        """
        Calculate error in coordinate transformation

        Returns:
            Euclidean distance between calculated and expected coords
        """
        calculated_dom = self.os_to_dom(os_coords[0], os_coords[1], browser_info)

        error = (
            (calculated_dom[0] - expected_dom_coords[0]) ** 2 +
            (calculated_dom[1] - expected_dom_coords[1]) ** 2
        ) ** 0.5

        return error
```

### 2.2 Vision Validation Layer

```python
import cv2
import numpy as np
from typing import Dict, List
from enum import Enum

class ValidationStrategy(Enum):
    """Validation strategies based on confidence levels"""
    FAST = "fast"  # Template matching only
    BALANCED = "balanced"  # Template + OCR
    THOROUGH = "thorough"  # All methods including AI
    CRITICAL = "critical"  # AI + human verification

class VisionValidationLayer:
    """
    Vision-based validation with adaptive strategies
    """

    def __init__(self):
        from implementation_examples import (
            HybridCoordinateValidator,
            ScreenCapture
        )
        self.validator = HybridCoordinateValidator()
        self.screen_capture = ScreenCapture()
        self.validation_cache = {}

    def validate(
        self,
        os_coords: Tuple[int, int],
        element_info: Dict,
        strategy: ValidationStrategy = ValidationStrategy.BALANCED
    ) -> Dict:
        """
        Validate coordinates using vision-based methods

        Args:
            os_coords: OS coordinates to validate
            element_info: Expected element properties
            strategy: Validation strategy to use

        Returns:
            Validation result with confidence
        """
        # Check cache
        cache_key = f"{os_coords}_{element_info.get('id', '')}"
        if cache_key in self.validation_cache:
            cached_result = self.validation_cache[cache_key]
            if cached_result['timestamp'] > time.time() - 5:  # 5 second cache
                return cached_result

        # Capture screenshot
        bbox = self._get_capture_bbox(os_coords, element_info)
        screenshot = self.screen_capture.capture_region(bbox)

        # Select validation methods based on strategy
        methods = self._select_methods(strategy, element_info)

        # Run validations
        validation_config = self._build_validation_config(
            element_info,
            methods
        )

        results = self.validator.validate(screenshot, validation_config)

        # Calculate confidence
        confidence = self.validator.get_overall_confidence(results)

        result = {
            'valid': confidence > self._get_threshold(strategy),
            'confidence': confidence,
            'results': {k: v.to_dict() for k, v in results.items()},
            'timestamp': time.time()
        }

        # Cache result
        self.validation_cache[cache_key] = result

        return result

    def _select_methods(
        self,
        strategy: ValidationStrategy,
        element_info: Dict
    ) -> List[str]:
        """Select validation methods based on strategy"""
        if strategy == ValidationStrategy.FAST:
            return ['template_matching']

        elif strategy == ValidationStrategy.BALANCED:
            methods = ['template_matching', 'edge_detection']
            if element_info.get('text'):
                methods.append('ocr')
            return methods

        elif strategy == ValidationStrategy.THOROUGH:
            methods = ['template_matching', 'feature_matching', 'edge_detection']
            if element_info.get('text'):
                methods.append('ocr')
            if element_info.get('color'):
                methods.append('color_profile')
            return methods

        else:  # CRITICAL
            return ['template_matching', 'feature_matching', 'ocr',
                   'color_profile', 'edge_detection', 'ai_validation']

    def _get_threshold(self, strategy: ValidationStrategy) -> float:
        """Get confidence threshold for strategy"""
        thresholds = {
            ValidationStrategy.FAST: 0.7,
            ValidationStrategy.BALANCED: 0.75,
            ValidationStrategy.THOROUGH: 0.8,
            ValidationStrategy.CRITICAL: 0.9
        }
        return thresholds.get(strategy, 0.75)

    def _get_capture_bbox(self, coords, element_info):
        """Calculate bounding box for screenshot capture"""
        # Add padding around expected element
        padding = 20

        from implementation_examples import BoundingBox
        return BoundingBox(
            x=coords[0] - padding,
            y=coords[1] - padding,
            width=element_info.get('width', 100) + 2 * padding,
            height=element_info.get('height', 50) + 2 * padding
        )

    def _build_validation_config(self, element_info, methods):
        """Build configuration for validation"""
        config = {'methods': methods}

        if 'text' in element_info:
            config['expected_text'] = element_info['text']

        if 'color' in element_info:
            config['expected_color'] = element_info['color']

        if 'template' in element_info:
            config['template'] = element_info['template']

        if 'bbox' in element_info:
            config['bbox'] = element_info['bbox']

        return config
```

### 2.3 AI Semantic Validation Layer

```python
import asyncio
from typing import Optional
import base64

class AISemanticValidator:
    """
    AI-powered semantic understanding and validation
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = 'openai'):
        self.provider = provider
        self.api_key = api_key

        if provider == 'openai':
            import openai
            self.client = openai
            self.model = 'gpt-4o'
        elif provider == 'anthropic':
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = 'claude-3-5-sonnet-20241022'

    async def validate_element_semantics(
        self,
        screenshot_path: str,
        coords: Tuple[int, int],
        element_description: str
    ) -> Dict:
        """
        Validate element using AI semantic understanding

        Args:
            screenshot_path: Path to screenshot
            coords: Coordinates to validate
            element_description: Natural language description of expected element

        Returns:
            Validation result with semantic understanding
        """
        with open(screenshot_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        if self.provider == 'openai':
            return await self._validate_openai(image_data, coords, element_description)
        elif self.provider == 'anthropic':
            return await self._validate_anthropic(image_data, coords, element_description)

    async def _validate_openai(self, image_data, coords, description):
        """Validate using OpenAI GPT-4V"""
        prompt = f"""At pixel coordinates ({coords[0]}, {coords[1]}), validate:

Expected element: {description}

Analyze and return JSON:
{{
    "element_found": true/false,
    "matches_description": true/false,
    "actual_element": "description of what's actually there",
    "confidence": 0.0-1.0,
    "clickable": true/false,
    "visible": true/false,
    "state": "enabled/disabled/hidden/etc",
    "recommendation": "proceed/recalculate/abort"
}}"""

        response = await self.client.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
        )

        import json
        return json.loads(response.choices[0].message.content)

    async def _validate_anthropic(self, image_data, coords, description):
        """Validate using Anthropic Claude"""
        prompt = f"""At pixel coordinates ({coords[0]}, {coords[1]}), validate:

Expected element: {description}

Analyze and return JSON with:
- element_found (bool)
- matches_description (bool)
- actual_element (string)
- confidence (0.0-1.0)
- clickable (bool)
- visible (bool)
- state (string)
- recommendation (proceed/recalculate/abort)"""

        message = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )

        import json
        return json.loads(message.content[0].text)
```

### 2.4 Complete Validation Orchestrator

```python
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Complete validation result"""
    success: bool
    confidence: float
    transformation_accurate: bool
    vision_validated: bool
    semantic_validated: bool
    recommendation: str
    details: Dict

class HybridValidationOrchestrator:
    """
    Orchestrates all validation layers
    """

    def __init__(
        self,
        use_ai: bool = True,
        ai_provider: str = 'openai',
        api_key: Optional[str] = None
    ):
        self.transformer = CoordinateTransformationEngine()
        self.vision_validator = VisionValidationLayer()
        self.ai_validator = AISemanticValidator(
            api_key=api_key,
            provider=ai_provider
        ) if use_ai else None

    async def validate_and_execute(
        self,
        action: str,
        os_coords: Tuple[int, int],
        browser_info: BrowserInfo,
        element_info: Dict,
        strategy: ValidationStrategy = ValidationStrategy.BALANCED
    ) -> ValidationResult:
        """
        Complete validation pipeline before executing action

        Args:
            action: Action to perform ('click', 'type', etc.)
            os_coords: OS coordinates for action
            browser_info: Browser window information
            element_info: Expected element properties
            strategy: Validation strategy

        Returns:
            Complete validation result
        """
        start_time = time.time()

        # Phase 1: Coordinate Transformation Validation
        transform_result = await self._validate_transformation(
            os_coords,
            browser_info,
            element_info
        )

        # Phase 2: Vision-Based Validation
        vision_result = self.vision_validator.validate(
            os_coords,
            element_info,
            strategy
        )

        # Phase 3: AI Semantic Validation (if enabled and needed)
        semantic_result = None
        if self.ai_validator and (
            vision_result['confidence'] < 0.8 or
            strategy == ValidationStrategy.CRITICAL
        ):
            # Capture screenshot for AI
            from implementation_examples import ScreenCapture, BoundingBox
            bbox = BoundingBox(
                x=os_coords[0] - 50,
                y=os_coords[1] - 50,
                width=element_info.get('width', 100) + 100,
                height=element_info.get('height', 50) + 100
            )
            screenshot = ScreenCapture.capture_region(bbox)
            ScreenCapture.save_screenshot(screenshot, '/tmp/validation.png')

            semantic_result = await self.ai_validator.validate_element_semantics(
                '/tmp/validation.png',
                (50, 50),  # Adjusted coords in cropped image
                element_info.get('description', element_info.get('type', 'element'))
            )

        # Aggregate Results
        final_result = self._aggregate_results(
            transform_result,
            vision_result,
            semantic_result,
            strategy
        )

        final_result.details['validation_time'] = time.time() - start_time

        # Execute if validated
        if final_result.success and final_result.recommendation == 'proceed':
            execution_result = await self._execute_action(
                action,
                os_coords,
                element_info
            )
            final_result.details['execution'] = execution_result

            # Post-execution validation
            if execution_result['success']:
                post_result = await self._post_execution_validation(
                    action,
                    element_info
                )
                final_result.details['post_validation'] = post_result

        return final_result

    async def _validate_transformation(
        self,
        os_coords: Tuple[int, int],
        browser_info: BrowserInfo,
        element_info: Dict
    ) -> Dict:
        """Validate coordinate transformation accuracy"""
        # Transform coordinates
        dom_coords = self.transformer.os_to_dom(
            os_coords[0],
            os_coords[1],
            browser_info
        )

        # If we have expected DOM coords, calculate error
        error = 0.0
        if 'expected_dom_coords' in element_info:
            error = self.transformer.calculate_transformation_error(
                os_coords,
                element_info['expected_dom_coords'],
                browser_info
            )

        return {
            'transformed_coords': dom_coords,
            'error': error,
            'accurate': error < 5.0,  # Within 5 pixels
            'display_scale': self.transformer.display_info.scale_factor
        }

    def _aggregate_results(
        self,
        transform_result: Dict,
        vision_result: Dict,
        semantic_result: Optional[Dict],
        strategy: ValidationStrategy
    ) -> ValidationResult:
        """Aggregate all validation results"""

        # Calculate overall confidence
        confidences = [vision_result['confidence']]
        weights = [0.6]  # Vision weight

        if transform_result['accurate']:
            confidences.append(1.0)
            weights.append(0.2)  # Transform weight

        if semantic_result:
            confidences.append(semantic_result.get('confidence', 0.0))
            weights.append(0.2)  # AI weight

        overall_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)

        # Determine success
        threshold = {
            ValidationStrategy.FAST: 0.7,
            ValidationStrategy.BALANCED: 0.75,
            ValidationStrategy.THOROUGH: 0.8,
            ValidationStrategy.CRITICAL: 0.9
        }[strategy]

        success = overall_confidence >= threshold

        # Recommendation
        if overall_confidence >= 0.9:
            recommendation = 'proceed'
        elif overall_confidence >= 0.7:
            recommendation = 'proceed_with_caution'
        elif overall_confidence >= 0.5:
            recommendation = 'recalculate'
        else:
            recommendation = 'abort'

        return ValidationResult(
            success=success,
            confidence=overall_confidence,
            transformation_accurate=transform_result['accurate'],
            vision_validated=vision_result['valid'],
            semantic_validated=semantic_result.get('matches_description', False) if semantic_result else False,
            recommendation=recommendation,
            details={
                'transform': transform_result,
                'vision': vision_result,
                'semantic': semantic_result,
                'strategy': strategy.value
            }
        )

    async def _execute_action(
        self,
        action: str,
        coords: Tuple[int, int],
        element_info: Dict
    ) -> Dict:
        """Execute the validated action"""
        import pyautogui

        try:
            if action == 'click':
                pyautogui.click(coords[0], coords[1])
            elif action == 'double_click':
                pyautogui.doubleClick(coords[0], coords[1])
            elif action == 'right_click':
                pyautogui.rightClick(coords[0], coords[1])
            elif action == 'type':
                pyautogui.click(coords[0], coords[1])
                pyautogui.write(element_info.get('text', ''))

            return {'success': True, 'action': action}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _post_execution_validation(
        self,
        action: str,
        element_info: Dict
    ) -> Dict:
        """Validate expected outcome after execution"""
        await asyncio.sleep(0.5)  # Wait for UI update

        # Check if expected outcome occurred
        if 'expected_outcome' in element_info:
            # Could use vision/AI to verify outcome
            # For now, placeholder
            return {'outcome_verified': True}

        return {'outcome_verified': False}
```

---

## 3. Usage Examples

### Example 1: Simple Click Validation

```python
async def example_validated_click():
    """Example of validated click operation"""

    # Initialize orchestrator
    orchestrator = HybridValidationOrchestrator(
        use_ai=True,
        ai_provider='openai',
        api_key='your-api-key'
    )

    # Browser information
    browser_info = BrowserInfo(
        x=100,
        y=50,
        width=1200,
        height=800,
        chrome_height=120,
        scroll_x=0,
        scroll_y=0
    )

    # Element to click
    element_info = {
        'type': 'button',
        'text': 'Submit',
        'description': 'blue submit button',
        'width': 100,
        'height': 40,
        'expected_outcome': {
            'type': 'navigation',
            'url_contains': 'success'
        }
    }

    # Execute with validation
    result = await orchestrator.validate_and_execute(
        action='click',
        os_coords=(500, 300),
        browser_info=browser_info,
        element_info=element_info,
        strategy=ValidationStrategy.BALANCED
    )

    print(f"Validation successful: {result.success}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Recommendation: {result.recommendation}")

    if result.details.get('execution'):
        print(f"Action executed: {result.details['execution']['success']}")
```

### Example 2: Form Filling with Validation

```python
async def example_form_filling():
    """Example of validated form filling"""

    orchestrator = HybridValidationOrchestrator(use_ai=False)

    browser_info = BrowserInfo(
        x=0, y=0, width=1920, height=1080,
        chrome_height=100, scroll_x=0, scroll_y=200
    )

    # Fill username field
    username_result = await orchestrator.validate_and_execute(
        action='type',
        os_coords=(400, 300),
        browser_info=browser_info,
        element_info={
            'type': 'input',
            'placeholder': 'Username',
            'text': 'john.doe@example.com'
        },
        strategy=ValidationStrategy.FAST
    )

    # Fill password field
    password_result = await orchestrator.validate_and_execute(
        action='type',
        os_coords=(400, 350),
        browser_info=browser_info,
        element_info={
            'type': 'input',
            'placeholder': 'Password',
            'text': 'secure_password'
        },
        strategy=ValidationStrategy.FAST
    )

    # Click submit
    submit_result = await orchestrator.validate_and_execute(
        action='click',
        os_coords=(450, 420),
        browser_info=browser_info,
        element_info={
            'type': 'button',
            'text': 'Sign In'
        },
        strategy=ValidationStrategy.THOROUGH
    )

    return all([
        username_result.success,
        password_result.success,
        submit_result.success
    ])
```

---

## 4. Performance Optimization

### Caching Strategy

```python
class ValidationCache:
    """Intelligent caching for validation results"""

    def __init__(self, ttl: int = 5):
        self.cache = {}
        self.ttl = ttl  # Time to live in seconds

    def get(self, key: str) -> Optional[Dict]:
        """Get cached result if valid"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['result']
            else:
                del self.cache[key]
        return None

    def set(self, key: str, result: Dict):
        """Cache result"""
        self.cache[key] = {
            'result': result,
            'timestamp': time.time()
        }

    def invalidate(self, pattern: str = None):
        """Invalidate cache entries"""
        if pattern:
            keys_to_delete = [k for k in self.cache if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
        else:
            self.cache.clear()
```

---

## 5. Error Handling and Recovery

```python
class ValidationError(Exception):
    """Custom validation error"""
    pass

class RecoveryStrategy:
    """Handle validation failures with recovery attempts"""

    @staticmethod
    async def recover_from_failure(
        failure_result: ValidationResult,
        orchestrator: HybridValidationOrchestrator,
        original_params: Dict
    ) -> ValidationResult:
        """
        Attempt to recover from validation failure

        Strategies:
        1. Retry with higher confidence strategy
        2. Recalculate coordinates
        3. Use alternative element locator
        4. Request human intervention
        """

        if failure_result.recommendation == 'recalculate':
            # Strategy 1: Try with more thorough validation
            if original_params['strategy'] == ValidationStrategy.FAST:
                original_params['strategy'] = ValidationStrategy.BALANCED
                return await orchestrator.validate_and_execute(**original_params)

            elif original_params['strategy'] == ValidationStrategy.BALANCED:
                original_params['strategy'] = ValidationStrategy.THOROUGH
                return await orchestrator.validate_and_execute(**original_params)

        elif failure_result.recommendation == 'abort':
            # Try AI-powered location
            if orchestrator.ai_validator:
                # Use AI to find element
                pass

        return failure_result
```

---

## 6. Metrics and Monitoring

```python
class ValidationMetrics:
    """Track validation performance metrics"""

    def __init__(self):
        self.metrics = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'avg_confidence': 0.0,
            'avg_validation_time': 0.0,
            'strategy_usage': {},
            'recovery_attempts': 0,
            'recovery_success': 0
        }

    def record_validation(self, result: ValidationResult, validation_time: float):
        """Record validation metrics"""
        self.metrics['total_validations'] += 1

        if result.success:
            self.metrics['successful_validations'] += 1
        else:
            self.metrics['failed_validations'] += 1

        # Update running average
        n = self.metrics['total_validations']
        self.metrics['avg_confidence'] = (
            self.metrics['avg_confidence'] * (n - 1) + result.confidence
        ) / n

        self.metrics['avg_validation_time'] = (
            self.metrics['avg_validation_time'] * (n - 1) + validation_time
        ) / n

    def get_success_rate(self) -> float:
        """Calculate success rate"""
        total = self.metrics['total_validations']
        if total == 0:
            return 0.0
        return self.metrics['successful_validations'] / total

    def report(self) -> Dict:
        """Generate metrics report"""
        return {
            **self.metrics,
            'success_rate': self.get_success_rate()
        }
```

This hybrid validation architecture provides a robust, production-ready system for validating OS-to-DOM coordinate transformations with multiple layers of verification.
