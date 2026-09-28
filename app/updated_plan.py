"""Feedback-Based Workout Plan Regeneration Module.

Integrates user feedback into existing workout plans while preserving
the user's core goals, physical context, and foundational structure.
"""

import logging
from typing import Tuple
from app.config import settings

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "\n\n---\n"
    "**Medical & Safety Disclaimer**: *This revised AI-generated fitness plan provides general exercise guidance. "
    "Consult with a licensed medical professional before undertaking new or modified physical routines.*"
)


def _build_revision_prompt(
    original_plan: str,
    feedback: str,
    username: str,
    goal: str,
    intensity: str,
    age: int,
    weight: float,
) -> str:
    """Creates a targeted prompt to revise the workout plan according to user feedback."""
    return f"""
You are FitBuddy AI. You are revising an existing 7-day workout plan based on user feedback.

USER PROFILE:
- Name: {username}
- Age: {age} years | Weight: {weight} kg
- Goal: {goal} | Intensity: {intensity}

USER FEEDBACK / MODIFICATION REQUEST:
"{feedback}"

ORIGINAL 7-DAY PLAN:
{original_plan}

CRITICAL REVISION INSTRUCTIONS:
1. PRESERVE THE FOUNDATION: Maintain the user's primary fitness goal ({goal}) and context. Do NOT replace with unrelated content.
2. APPLY THE FEEDBACK: Directly incorporate the user's request (e.g., adding cardio intervals, scheduling an additional rest/recovery day, weaving in yoga/mobility flows, scaling down intensity, or emphasizing core work).
3. SUMMARY SECTION: Begin your response with a concise section:
   ### 🔄 Modifications Applied Based on Feedback
   - Bullet points outlining specifically what was modified in response to "{feedback}".
4. COMPLETE 7-DAY REVISION: Provide the full, revised Day 1 through Day 7 schedule with:
   - Day Title & Focus
   - Warm-Up
   - Main Exercises (Sets, Reps/Duration, Rest)
   - Cool-Down & Recovery
5. Formatting: Use structured Markdown headers (### Day X: ...) for readability.
"""


def _generate_mock_revised_plan(
    original_plan: str,
    feedback: str,
    username: str,
    goal: str,
    intensity: str,
) -> str:
    """Generates a contextual revised plan for mock/testing mode based on user feedback keywords."""
    banner = (
        "> [!NOTE]\n"
        "> **Notice: Development / Mock Revision Mode**\n"
        "> *Google Gemini API key is not configured in `.env`. "
        "The plan below is an intelligent simulation of the revised plan incorporating your feedback for testing purposes.*\n\n"
    )

    fb_lower = feedback.lower()
    changes = []
    
    if "cardio" in fb_lower:
        changes.append("Integrated 15-20 minutes of Zone 2 cardio and metabolic finishers on Days 1, 3, and 5.")
        changes.append("Added a dedicated 35-minute aerobic endurance session on Day 4.")
    if "rest" in fb_lower or "recovery" in fb_lower or "tired" in fb_lower:
        changes.append("Converted Day 4 from active lifting into full neurological restoration and gentle mobility.")
        changes.append("Increased inter-set rest intervals by 30 seconds across all heavy compound exercises.")
    if "yoga" in fb_lower or "stretch" in fb_lower or "mobility" in fb_lower:
        changes.append("Substituted high-impact conditioning on Day 6 with a 40-minute Vinyasa & Fascial Release Yoga flow.")
        changes.append("Extended daily warm-ups and cool-downs by 5 minutes to prioritize joint mobility.")
    if "intensity" in fb_lower or "reduce" in fb_lower or "lower" in fb_lower or "easier" in fb_lower:
        changes.append("Reduced working sets per exercise from 4 to 3 and adjusted repetitions to a comfortable RPE 6-7.")
        changes.append("Replaced high-load spinal exercises with joint-friendly dumbbell and bodyweight alternatives.")
    if "core" in fb_lower or "abs" in fb_lower:
        changes.append("Appended a dedicated 8-minute core strengthening tri-set (Hanging knee raises, Planks, Bird-dogs) to Days 2, 4, and 6.")
        changes.append("Emphasized rotational and anti-rotational stability work to protect the lower spine.")
    
    if not changes:
        changes.append(f"Carefully tailored exercise selection, volume, and pacing to directly accommodate: '{feedback}'.")
        changes.append("Preserved your core training split while re-balancing movement patterns for optimal progression.")

    summary_block = "### 🔄 Modifications Applied Based on Feedback\n"
    for c in changes:
        summary_block += f"- {c}\n"
    summary_block += f"- **User Request:** *\"{feedback}\"*\n\n"

    # Now create modified plan text
    revised_body = (
        f"### Revised 7-Day Fitness Blueprint for {username}\n"
        f"**Goal:** {goal} | **Adjusted Intensity:** {intensity} (Refined per feedback)\n\n"
        "### Day 1: Strength Foundation & Tailored Movement\n"
        "- **Focus:** Primary compound mechanics with custom pacing\n"
        "- **Warm-Up:** 8 mins dynamic mobility and light joint rotations\n"
        "- **Main Exercises:**\n"
        "  * **Goblet Squat or Leg Press**: 3 sets × 10-12 reps | Rest: 75 seconds\n"
        "  * **Dumbbell Chest Press**: 3 sets × 10 reps | Rest: 60 seconds\n"
        "  * **Lat Pulldown or Seated Cable Row**: 3 sets × 12 reps | Rest: 60 seconds\n"
        "  * **Core Plank / Stability Hold**: 3 sets × 45 seconds | Rest: 45 seconds\n"
        "- **Cool-Down & Mobility:** 7 mins static stretches focused on chest, hips, and calves\n\n"
        "### Day 2: Functional Conditioning & Feedback Emphasis\n"
        "- **Focus:** Aerobic capacity and core stability\n"
        "- **Warm-Up:** 5 mins brisk walk and dynamic leg swings\n"
        "- **Main Exercises:**\n"
        "  * **Low-Impact Incline Walking or Cycling**: 1 set × 30 mins | Rest: Continuous\n"
        "  * **Bodyweight Lunges**: 3 sets × 10 reps per leg | Rest: 60 seconds\n"
        "  * **Bird-Dog & Deadbug Superset**: 3 sets × 10 reps per side | Rest: 45 seconds\n"
        "  * **Dumbbell Lateral Raises**: 3 sets × 12-15 reps | Rest: 45 seconds\n"
        "- **Cool-Down & Mobility:** 8 mins full-body yoga stretch\n\n"
        "### Day 3: Balanced Upper & Posterior Chain\n"
        "- **Focus:** Postural endurance and muscular balance\n"
        "- **Warm-Up:** Resistance band pull-aparts and arm circles (6 mins)\n"
        "- **Main Exercises:**\n"
        "  * **Romanian Deadlifts**: 3 sets × 10 reps | Rest: 90 seconds\n"
        "  * **Dumbbell Overhead Shoulder Press**: 3 sets × 10-12 reps | Rest: 60 seconds\n"
        "  * **Single-Arm Dumbbell Row**: 3 sets × 12 reps | Rest: 60 seconds\n"
        "  * **Bicep Curls / Tricep Pushdown**: 3 sets × 12 reps | Rest: 45 seconds\n"
        "- **Cool-Down & Mobility:** Doorframe pectoral stretch & child's pose (6 mins)\n\n"
        "### Day 4: Dedicated Active Recovery / Mindful Restoration\n"
        "- **Focus:** Central nervous system regeneration per user preference\n"
        "- **Warm-Up:** Gentle breathing and spinal cat-cow flow\n"
        "- **Main Exercises:**\n"
        "  * **Nature Walk or Light Movement**: 1 set × 35 mins | Rest: Continuous, relaxing pace\n"
        "  * **Fascial Foam Rolling**: Quads, IT-band, and thoracic spine (15 mins)\n"
        "- **Cool-Down & Mobility:** 10 mins deep diaphragmatic breathing and gentle yoga holds\n\n"
        "### Day 5: Total Body Athleticism & Core Integration\n"
        "- **Focus:** Full body coordination with feedback-adjusted intensity\n"
        "- **Warm-Up:** Hip openers, bodyweight air squats, arm sweeps (7 mins)\n"
        "- **Main Exercises:**\n"
        "  * **Kettlebell or Dumbbell Deadlift**: 3 sets × 10 reps | Rest: 75 seconds\n"
        "  * **Incline Push-ups or Dumbbell Bench**: 3 sets × 12 reps | Rest: 60 seconds\n"
        "  * **Seated Cable or Band Row**: 3 sets × 12 reps | Rest: 60 seconds\n"
        "  * **Bicycle Crunches & Russian Twists**: 3 sets × 20 reps total | Rest: 45 seconds\n"
        "- **Cool-Down & Mobility:** Hamstring wall stretch & glute figure-four stretch (7 mins)\n\n"
        "### Day 6: Agility, Cardio & Restorative Yoga\n"
        "- **Focus:** Dynamic movement and fascial elasticity\n"
        "- **Warm-Up:** Joint rolls, sun salutations (5 mins)\n"
        "- **Main Exercises:**\n"
        "  * **Interval Cardio (Elliptical / Rower / Jog)**: 20-25 mins moderate tempo\n"
        "  * **Yoga Flow (Warrior Sequence & Pigeon Pose)**: 20 mins fluid movement\n"
        "  * **Side Planks**: 3 sets × 30 seconds per side | Rest: 30 seconds\n"
        "- **Cool-Down & Mobility:** Savasana and guided mindful relaxation (8 mins)\n\n"
        "### Day 7: Complete Rest & Weekly Reset\n"
        "- **Focus:** Full muscular replenishment and mental recharge\n"
        "- **Recovery Actions:**\n"
        "  * Hydration: 3+ Liters with balanced electrolytes\n"
        "  * Sleep: 8+ hours quality sleep\n"
        "  * Nutrition: Nutrient-dense meals supporting muscle protein repair\n"
        "- **Cool-Down & Mobility:** 10-minute relaxing evening walk\n"
    )

    return banner + summary_block + revised_body + DISCLAIMER_TEXT


def regenerate_workout_with_feedback(
    original_plan: str,
    feedback: str,
    username: str,
    goal: str,
    intensity: str,
    age: int,
    weight: float,
) -> Tuple[str, bool]:
    """Regenerates a workout plan by blending original plan context with user feedback.

    Returns:
        Tuple[str, bool]: (revised_plan_text, is_mock_mode)
    """
    if not settings.is_gemini_configured:
        logger.info("Gemini API key is not configured. Generating mock revised workout plan.")
        return _generate_mock_revised_plan(original_plan, feedback, username, goal, intensity), True

    prompt = _build_revision_prompt(
        original_plan=original_plan,
        feedback=feedback,
        username=username,
        goal=goal,
        intensity=intensity,
        age=age,
        weight=weight,
    )

    system_instruction = (
        "You are FitBuddy AI, an expert fitness programming consultant. "
        "Your task is to refine an existing workout plan based on the user's specific feedback. "
        "Keep their primary goal intact, highlight adjustments in an introductory section, "
        "and provide the full revised 7-day schedule with safe, realistic instructions."
    )

    try:
        from google import genai
        from google.genai import types

        logger.info("Invoking Gemini model %s for plan revision with feedback", settings.GEMINI_MODEL)
        client = genai.Client(api_key=settings.effective_api_key)

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.6,
                max_output_tokens=4000,
                system_instruction=system_instruction,
            ),
        )

        revised_text = response.text if response and response.text else ""
        if not revised_text.strip():
            raise ValueError("Gemini returned an empty revision response.")

        if "disclaimer" not in revised_text.lower():
            revised_text += DISCLAIMER_TEXT

        return revised_text, False

    except Exception as exc:
        logger.error("Gemini API error during plan revision: %s", exc, exc_info=True)
        if settings.ENABLE_MOCK_FALLBACK:
            warning_header = (
                f"> [!WARNING]\n"
                f"> **Gemini API Error Notice**: Revision encountered an error: `{str(exc)}`.\n"
                f"> FitBuddy applied your feedback using our built-in rules engine to keep your workout on schedule.\n\n"
            )
            mock_revision = _generate_mock_revised_plan(original_plan, feedback, username, goal, intensity)
            return warning_header + mock_revision, True
        raise RuntimeError(f"Failed to revise workout plan with Gemini: {exc}") from exc
