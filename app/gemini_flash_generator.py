"""Gemini Flash Nutrition and Recovery Tip Generator.

Provides concise, practical, and science-backed nutritional and recovery protocols
tailored to the user's specific fitness goal and training intensity.
"""

import logging
from typing import Tuple
from app.config import settings

logger = logging.getLogger(__name__)


def _build_nutrition_prompt(goal: str, age: int, weight: float, intensity: str) -> str:
    """Creates a concise prompt for Gemini Flash."""
    return f"""
Provide a concise, practical, and science-based Nutrition and Recovery Tip for a trainee with:
- Fitness Goal: {goal}
- Intensity: {intensity}
- Weight: {weight} kg
- Age: {age} years

Topics to incorporate succinctly:
1. Target Daily Protein Intake (give specific grams based on {weight} kg)
2. Hydration Target (liters per day + workout replenishment)
3. Pre/Post-Workout Nutrition (timing and nutrient balance)
4. Sleep & Physical Recovery (actionable advice for muscle repair)

KEEP THE RESPONSE CONCISE, BULLET-POINTED, AND PRACTICAL (around 150-250 words total).
"""


def _generate_mock_nutrition_tip(goal: str, age: int, weight: float, intensity: str) -> str:
    """Mock nutrition & recovery guidance when Gemini API is not configured."""
    protein_target = round(weight * (1.8 if goal == "Muscle Gain" else 1.4), 1)
    water_target = round(weight * 0.04, 1)

    if goal == "Muscle Gain":
        return f"""
* **Target Daily Protein:** Aim for approximately **{protein_target}g of protein daily** (1.8g – 2.0g per kg of bodyweight) divided across 3–4 meals with quality sources (eggs, chicken, fish, tofu, whey/plant protein).
* **Post-Workout Nutrition:** Consume a fast-digesting meal or shake within 45–60 minutes post-training containing 30g protein + 40-50g complex carbohydrates to kickstart muscle protein synthesis and glycogen replenishment.
* **Hydration Rule:** Drink at least **{water_target} Liters of water daily**, adding 500ml per hour of intense resistance training.
* **Sleep & Anabolic Recovery:** Prioritize 7.5 to 8.5 hours of uninterrupted sleep; growth hormone release peaks during deep slow-wave sleep. Consider 300mg magnesium glycinate before bed to enhance muscular relaxation.
"""
    elif goal == "Weight Loss":
        return f"""
* **Target Protein for Satiety:** Aim for **{protein_target}g of protein daily** (approx. 1.4g – 1.6g per kg) to preserve lean muscle tissue while maintaining a modest caloric deficit.
* **Plate Balance:** Construct meals using the 50/25/25 rule: 50% non-starchy fibrous vegetables, 25% lean protein, and 25% complex slow-digesting carbs (quinoa, sweet potatoes, oats).
* **Hydration & Metabolic Support:** Drink **{water_target} Liters of pure water daily**. Drinking 500ml 20 minutes before meals naturally promotes fullness and optimal digestion.
* **Sleep & Cortisol Control:** Ensure 7–8 hours of quality sleep. Elevated chronic cortisol from sleep deprivation increases cravings for refined carbohydrates and impairs fat oxidation.
"""
    elif goal == "Flexibility":
        return f"""
* **Connective Tissue Support:** Consume adequate collagen-rich foods, bone broth, or Vitamin C (citrus, bell peppers) to support collagen synthesis for tendons and ligaments.
* **Optimal Hydration for Fascia:** Drink **{water_target} Liters of mineralized water daily**. Dehydrated fascial tissue becomes stiff and prone to adhesions; proper electrolyte balance (sodium, potassium, magnesium) maintains tissue glide.
* **Anti-Inflammatory Nutrition:** Incorporate Omega-3 fatty acids (salmon, walnuts, chia seeds) and turmeric/curcumin to accelerate joint mobility recovery.
* **Restorative Practices:** Pair nightly yin stretching or light foam rolling with 8 hours of sleep in a cool, dark environment to allow central nervous system decompression.
"""
    else:  # General Wellness
        return f"""
* **Balanced Whole-Food Nutrition:** Prioritize nutrient density with colourful vegetables, lean proteins (~{protein_target}g daily), healthy monounsaturated fats (extra virgin olive oil, avocados), and high-fiber grains.
* **Consistent Hydration:** Target **{water_target} Liters of fluids daily**. Keep a reusable water bottle near your workspace and sip steadily throughout the day.
* **Pre & Post Movement Fuel:** Eat a light piece of fruit (banana or apple with a spoonful of almond butter) 30–45 minutes before exercise for steady sustained energy.
* **Circadian Rhythm & Recovery:** Aim for 7 to 8 hours of consistent sleep each night. Expose your eyes to natural morning sunlight within 30 minutes of waking to anchor your energy rhythm.
"""


def generate_nutrition_tip_with_flash(
    goal: str,
    age: int,
    weight: float,
    intensity: str,
) -> Tuple[str, bool]:
    """Generates a concise nutrition or recovery tip using Gemini Flash.

    Returns:
        Tuple[str, bool]: (nutrition_tip_text, is_mock_mode)
    """
    if not settings.is_gemini_configured:
        logger.info("Gemini API key is not configured. Utilizing mock nutrition tip.")
        return _generate_mock_nutrition_tip(goal, age, weight, intensity), True

    prompt = _build_nutrition_prompt(goal, age, weight, intensity)
    system_instruction = (
        "You are a sports nutritionist and recovery specialist. "
        "Deliver clear, crisp, science-backed nutrition and recovery advice. "
        "Keep your response concise, actionable, and formatted with bullet points."
    )

    try:
        from google import genai
        from google.genai import types

        logger.info("Invoking Gemini Flash model %s for nutrition tip", settings.GEMINI_FLASH_MODEL)
        client = genai.Client(api_key=settings.effective_api_key)

        response = client.models.generate_content(
            model=settings.GEMINI_FLASH_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
                max_output_tokens=1000,
                system_instruction=system_instruction,
            ),
        )

        tip_text = response.text if response and response.text else ""
        if not tip_text.strip():
            raise ValueError("Gemini Flash returned an empty response.")

        return tip_text, False

    except Exception as exc:
        logger.error("Gemini Flash error during nutrition tip generation: %s", exc, exc_info=True)
        if settings.ENABLE_MOCK_FALLBACK:
            fallback_note = (
                f"> *Note: Live AI service unavailable ({str(exc)}). Showing sports science recommendations below:*\n\n"
            )
            mock_tip = _generate_mock_nutrition_tip(goal, age, weight, intensity)
            return fallback_note + mock_tip, True
        raise RuntimeError(f"Failed to generate nutrition tip from Gemini Flash: {exc}") from exc
