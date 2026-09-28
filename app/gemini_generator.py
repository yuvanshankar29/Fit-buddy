"""Gemini Workout Plan Generator.

Isolated module responsible for generating structured 7-day fitness plans
using the modern official Google GenAI SDK (`google-genai`).
"""

import logging
from typing import Tuple
from app.config import settings

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "\n\n---\n"
    "**Medical & Safety Disclaimer**: *This AI-generated fitness plan provides general wellness and exercise recommendations. "
    "Prior to commencing any new training regimen, consult a physician or certified healthcare provider, especially if you have "
    "pre-existing medical conditions, injuries, or cardiovascular risks.*"
)


def _build_workout_prompt(username: str, user_id: str, age: int, weight: float, goal: str, intensity: str) -> str:
    """Constructs a deterministic, structured prompt for Gemini."""
    return f"""
Generate a comprehensive, scientifically sound, and safe 7-day personalized workout plan for:
- Trainee Name: {username} (ID: {user_id})
- Age: {age} years
- Weight: {weight} kg
- Primary Fitness Goal: {goal}
- Requested Intensity: {intensity}

REQUIRED STRUCTURE AND CONSTRAINTS:
1. Clearly structure each day from Day 1 to Day 7.
2. For every single day, provide:
   - **Day Title & Workout Focus** (e.g., Upper Body Strength, Active Recovery, HIIT & Core)
   - **Warm-Up**: 5-10 minutes specific preparatory movements.
   - **Main Exercises**: 4 to 6 exercises formatted cleanly with exact:
     * Sets
     * Repetitions or Duration
     * Rest Intervals between sets
   - **Cool-Down & Mobility**: 5-10 minutes stretching/recovery.
3. If active recovery or rest is scheduled for a day, clearly describe light mobility, walking, and restoration activities.
4. Scale volume and exercise selection strictly to the user's age ({age}), weight ({weight}kg), and intensity ({intensity}).
5. Tone: Motivating, professional, and safety-focused. Do NOT suggest dangerous, extreme, or contraindicated movements.
6. Use clean Markdown headings (### Day 1: ..., ### Day 2: ...) with bullet points and bold headers for predictability.
"""


def _generate_mock_workout_plan(username: str, user_id: str, age: int, weight: float, goal: str, intensity: str) -> str:
    """Generates a high-quality, realistic 7-day workout plan for development/testing when Gemini API is not configured.
    
    Clearly flags the plan as a mock simulation rather than claiming it came from live Gemini API.
    """
    banner = (
        "> [!NOTE]\n"
        "> **Notice: Development / Mock Mode Active**\n"
        "> *The Google Gemini API key (`GOOGLE_API_KEY`) is not configured in `.env`. "
        "The plan below is a structured simulation generated locally for development and UI testing. "
        "To activate live Gemini generation, configure your API key in `.env`.*\n\n"
    )

    if goal == "Muscle Gain":
        split = [
            ("Day 1: Chest & Triceps (Hypertrophy)", "Push Focus", "Arm circles, light push-ups, dynamic chest openers (7 mins)", [
                ("Barbell or Dumbbell Bench Press", "4", "8-10 reps", "90 seconds"),
                ("Incline Dumbbell Press", "3", "10-12 reps", "75 seconds"),
                ("Dips or Cable Chest Flyes", "3", "12 reps", "60 seconds"),
                ("Overhead Tricep Extension", "3", "12-15 reps", "60 seconds"),
                ("Cable Tricep Pushdowns", "3", "15 reps", "45 seconds"),
            ], "Chest doorway stretch, overhead tricep stretch (5 mins)"),
            ("Day 2: Back & Biceps (Pull Hypertrophy)", "Pull Focus", "Band pull-aparts, cat-cow stretch, bodyweight dead hangs (7 mins)", [
                ("Barbell Bent-Over Row or Lat Pulldown", "4", "8-10 reps", "90 seconds"),
                ("Single-Arm Dumbbell Rows", "3", "10 reps each", "75 seconds"),
                ("Seated Cable Row", "3", "12 reps", "60 seconds"),
                ("Standing Incline Dumbbell Curls", "3", "10-12 reps", "60 seconds"),
                ("Hammer Curls", "3", "12-15 reps", "45 seconds"),
            ], "Lat hangs, child's pose, bicep wall stretches (5 mins)"),
            ("Day 3: Lower Body (Quads & Calves)", "Leg Power", "Bodyweight squats, walking lunges, leg swings (8 mins)", [
                ("Barbell Back Squats or Goblet Squats", "4", "8-10 reps", "120 seconds"),
                ("Romanian Deadlifts (RDLs)", "3", "10-12 reps", "90 seconds"),
                ("Leg Press or Bulgarian Split Squats", "3", "10-12 reps each", "75 seconds"),
                ("Leg Curl Machine", "3", "12-15 reps", "60 seconds"),
                ("Standing Calf Raises", "4", "15-20 reps", "45 seconds"),
            ], "Quad stretches, pigeon pose, foam rolling calves (6 mins)"),
            ("Day 4: Active Recovery & Core", "Recovery & Mobility", "5-minute gentle joint mobility flow", [
                ("Brisk Outdoor Incline Walk", "1", "30-40 mins", "Continuous"),
                ("Plank Holds", "3", "45-60 seconds", "60 seconds"),
                ("Hanging Leg or Knee Raises", "3", "12-15 reps", "60 seconds"),
                ("Bird-Dog & Deadbugs", "3", "10 reps per side", "45 seconds"),
            ], "Full body yoga flow, deep diaphragmatic breathing (10 mins)"),
            ("Day 5: Shoulders & Upper Back", "Shoulder Sculpting", "Shoulder dislocations with resistance band, arm swings (6 mins)", [
                ("Overhead Barbell or Dumbbell Press", "4", "8-10 reps", "90 seconds"),
                ("Dumbbell Lateral Raises", "4", "12-15 reps", "60 seconds"),
                ("Face Pulls with Rope Cable", "3", "15 reps", "60 seconds"),
                ("Dumbbell Rear Delt Flyes", "3", "12-15 reps", "45 seconds"),
                ("Dumbbell Shrugs", "3", "12-15 reps", "60 seconds"),
            ], "Cross-body shoulder stretch, neck release stretches (5 mins)"),
            ("Day 6: Lower Body (Hamstrings & Glutes)", "Posterior Chain", "Glute bridges, band lateral walks, high knees (7 mins)", [
                ("Deadlifts or Trap Bar Deadlifts", "4", "6-8 reps", "120 seconds"),
                ("Walking Dumbbell Lunges", "3", "12 steps per leg", "75 seconds"),
                ("Glute Ham Raises or Lying Leg Curls", "3", "10-12 reps", "60 seconds"),
                ("Barbell Hip Thrusts", "3", "10-12 reps", "90 seconds"),
                ("Seated Calf Raises", "3", "15 reps", "45 seconds"),
            ], "Hamstring stretch, seated figure-4 stretch, foam rolling (6 mins)"),
            ("Day 7: Full Rest & Restoration", "Complete Nervous System Recovery", "Optional 10-minute light morning walk", [
                ("Hydration & Nutrition Focus", "N/A", "Hit protein & water targets", "All day"),
                ("Gentle Full-Body Stretching", "1", "15-20 mins", "Relaxed pacing"),
            ], "Sauna, Epsom salt bath, or 8+ hours quality sleep"),
        ]
    elif goal == "Weight Loss":
        split = [
            ("Day 1: Full-Body Metabolic Resistance", "Metabolic Circuit", "Jumping jacks, arm swings, bodyweight squats (6 mins)", [
                ("Goblet Squats", "4", "12-15 reps", "45 seconds"),
                ("Dumbbell Push Press", "3", "12 reps", "45 seconds"),
                ("Bent-Over Dumbbell Rows", "3", "12 reps", "45 seconds"),
                ("Mountain Climbers", "3", "30 seconds", "30 seconds"),
                ("Kettlebell Swings or Dumbbell Swings", "3", "15 reps", "45 seconds"),
            ], "Hamstring and hip flexor stretches, deep breathing (5 mins)"),
            ("Day 2: Steady-State Cardio & Core", "Fat Oxidation & Midsection", "5 mins brisk treadmill or outdoor warm-up walk", [
                ("Incline Treadmill or Cycling (Zone 2)", "1", "35-45 mins", "Continuous (65-75% max HR)"),
                ("Bicycle Crunches", "3", "20 reps (10/side)", "30 seconds"),
                ("Forearm Plank", "3", "45 seconds", "45 seconds"),
                ("Russian Twists with light weight", "3", "20 total reps", "30 seconds"),
            ], "Full lower-body stretch routine (6 mins)"),
            ("Day 3: Upper Body Strength & Conditioning", "Upper Tone & Calorie Burn", "Band pull-aparts, arm rotations (6 mins)", [
                ("Dumbbell Chest Press", "3", "12 reps", "60 seconds"),
                ("Lat Pulldown or Assisted Pull-ups", "3", "12 reps", "60 seconds"),
                ("Seated Dumbbell Shoulder Press", "3", "12 reps", "60 seconds"),
                ("Cable Tricep Extensions", "3", "15 reps", "45 seconds"),
                ("Dumbbell Bicep Curls", "3", "12 reps", "45 seconds"),
            ], "Chest opener, lat stretch, shoulder rolls (5 mins)"),
            ("Day 4: Active Recovery & Gentle Walk", "Recovery", "Dynamic ankle, hip, and neck circles (5 mins)", [
                ("Brisk Outdoor Leisure Walk", "1", "45-60 mins", "Continuous, relaxed"),
                ("Cat-Cow & Child's Pose Flow", "3", "10 cycles", "Slow breathing"),
            ], "Full-body passive stretching (8 mins)"),
            ("Day 5: Lower Body & Glutes Sculpting", "Leg Stamina & Tone", "Leg swings, bodyweight lunges, glute bridges (7 mins)", [
                ("Dumbbell Romanian Deadlifts", "4", "12 reps", "60 seconds"),
                ("Step-Ups on Bench", "3", "12 reps per leg", "60 seconds"),
                ("Bodyweight or Goblet Squats", "3", "15 reps", "45 seconds"),
                ("Lying Leg Curls or Sliders", "3", "12-15 reps", "45 seconds"),
                ("Calf Raises", "3", "20 reps", "30 seconds"),
            ], "Quad stretches, seated forward fold, foam rolling (6 mins)"),
            ("Day 6: HIIT (High-Intensity Interval Training) & Core", "Anaerobic Conditioning", "Dynamic joint warm-up, light jog (6 mins)", [
                ("Sprint/Row Intervals (30s sprint / 60s walk)", "8", "8 rounds total", "60 seconds active rest"),
                ("Bodyweight Jump Squats (or speed squats)", "3", "12 reps", "45 seconds"),
                ("Push-ups (standard or knees)", "3", "10-15 reps", "45 seconds"),
                ("Plank Shoulder Taps", "3", "20 total reps", "30 seconds"),
            ], "Gradual walking cool-down (5 mins) and yoga cooldown (5 mins)"),
            ("Day 7: Rest & Restoration", "Regeneration", "Gentle breathing exercises", [
                ("Mindful Walking / Hydration", "N/A", "Aim for 3+ liters water", "Day-long"),
                ("Mobility & Foam Rolling", "1", "20 mins", "Gentle"),
            ], "Sleep optimization, meal preparation for the week ahead"),
        ]
    elif goal == "Flexibility":
        split = [
            ("Day 1: Dynamic Mobility & Spine Health", "Spinal Articulation & Hips", "Gentle arm and torso twists, cat-cow flow (6 mins)", [
                ("World's Greatest Stretch", "3", "5 reps per side", "30 seconds"),
                ("Thoracic Spine Rotations", "3", "10 reps per side", "30 seconds"),
                ("Cat-Cow Spinal Articulation", "3", "12 reps", "30 seconds"),
                ("Puppy Pose Lat Stretch", "3", "45 seconds hold", "30 seconds"),
            ], "Child's pose, corpse pose with deep diaphragmatic breathing (6 mins)"),
            ("Day 2: Lower Body Hip Openers & Hamstrings", "Hip & Posterior Chain Flexibility", "Ankle circles, standing knee hugs (5 mins)", [
                ("Pigeon Pose or 90/90 Hip Stretch", "3", "60 seconds per leg", "30 seconds"),
                ("Lying Hamstring Stretch with Strap", "3", "45 seconds per leg", "30 seconds"),
                ("Butterfly Adductor Stretch", "3", "60 seconds hold", "30 seconds"),
                ("Frog Pose / Deep Squat Hold", "3", "45 seconds hold", "45 seconds"),
            ], "Seated wide-legged forward fold (5 mins)"),
            ("Day 3: Core Stability & Gentle Yoga Flow", "Isometric Core & Flow", "Sun Salutation A (3 rounds)", [
                ("Sun Salutation B Sequence", "4", "Full flow cycles", "Smooth transitions"),
                ("Warrior I to Warrior II Flow", "3", "5 breaths per posture", "30 seconds"),
                ("Bird-Dog Balance Holds", "3", "10 reps per side", "30 seconds"),
                ("Side Plank on Forearm", "3", "30 seconds per side", "45 seconds"),
            ], "Bridge pose and supine spinal twists (6 mins)"),
            ("Day 4: Active Rest & Walking Meditation", "Restoration", "Gentle joint rolls (5 mins)", [
                ("Mindful Nature Walk", "1", "30-40 mins", "Relaxed pace"),
                ("Gentle Standing Neck & Shoulder Rolls", "2", "10 reps each", "Continuous"),
            ], "Meditation and restorative breathing (10 mins)"),
            ("Day 5: Upper Body, Chest & Shoulder Mobility", "Postural Restoration", "Arm crosses, wrist circles, doorframe stretches (5 mins)", [
                ("Doorway Pectoral Stretch", "3", "45 seconds per angle", "30 seconds"),
                ("Prone Cobra / Y-T-W Raises", "3", "10 reps each", "45 seconds"),
                ("Eagle Arm Shoulder Stretch", "3", "30 seconds per side", "30 seconds"),
                ("Overhead Tricep & Lat Stretch", "3", "40 seconds per side", "30 seconds"),
            ], "Seated meditation posture with upright spine breathing (5 mins)"),
            ("Day 6: Full-Body Vinyasa & Deep Tissue Recovery", "Full Body Flexibility", "Joint warm-up, downward dog pedals (6 mins)", [
                ("Vinyasa Flow (Crescent Lunge to Triangle)", "4", "5 cycles per side", "Smooth flow"),
                ("Couch Stretch (Hip Flexor / Quad)", "3", "45 seconds per side", "30 seconds"),
                ("Deep Seated Forward Bend", "3", "60 seconds hold", "30 seconds"),
                ("Foam Rolling (IT Band, Quads, Upper Back)", "1", "15 mins", "Self-paced"),
            ], "Savasana (Corpse Pose) with progressive muscle relaxation (8 mins)"),
            ("Day 7: Rest & Mindful Restoration", "Full Recovery", "Gentle breathing", [
                ("Hydration & Gentle Walking", "1", "20 mins", "Continuous"),
                ("Legs-Up-The-Wall Restorative Pose", "1", "10-15 mins hold", "Continuous"),
            ], "Sound sleep and mental rejuvenation"),
        ]
    else:  # General Wellness
        split = [
            ("Day 1: Full-Body Functional Strength", "Functional Balance", "Dynamic arm swings, torso twists, bodyweight squats (6 mins)", [
                ("Goblet Squats or Chair Squats", "3", "10-12 reps", "60 seconds"),
                ("Incline Push-ups or Floor Push-ups", "3", "10-12 reps", "60 seconds"),
                ("Dumbbell or Resistance Band Rows", "3", "12 reps", "60 seconds"),
                ("Glute Bridges", "3", "15 reps", "45 seconds"),
                ("Deadbug Core Exercise", "3", "10 reps per side", "45 seconds"),
            ], "Hamstring stretch, chest stretch, deep diaphragmatic breathing (5 mins)"),
            ("Day 2: Cardiovascular Health & Brisk Walk/Jog", "Cardiorespiratory Fitness", "5 mins gentle warm-up walk", [
                ("Brisk Walking, Jogging, or Elliptical", "1", "30-40 mins", "Target 60-70% max HR"),
                ("Standing Calf Raises", "3", "15 reps", "30 seconds"),
                ("Bodyweight Step-ups", "3", "10 reps per leg", "45 seconds"),
            ], "Calf and hamstring stretches (5 mins)"),
            ("Day 3: Mobility, Core & Posture", "Spine & Core Health", "Cat-cow, bird-dog, shoulder circles (6 mins)", [
                ("Forearm Plank", "3", "30-45 seconds", "45 seconds"),
                ("Bird-Dog Balance", "3", "10 reps per side", "30 seconds"),
                ("Side Plank", "3", "20-30 seconds per side", "45 seconds"),
                ("Superman Posture Holds", "3", "10 reps (3s hold)", "30 seconds"),
            ], "Child's pose, cobra stretch, seated neck stretches (6 mins)"),
            ("Day 4: Active Rest & Outdoor Movement", "Gentle Activity", "Light ankle and knee rotations", [
                ("Outdoor Nature Walk or Leisure Bike Ride", "1", "30-45 mins", "Easy conversational pace"),
                ("Gentle Full-Body Stretching", "1", "10 mins", "Relaxed"),
            ], "Hydration and mindful breathing"),
            ("Day 5: Total Body Tone & Stamina", "Muscular Endurance", "Arm swings, high knees, hip openers (6 mins)", [
                ("Dumbbell Romanian Deadlifts", "3", "10-12 reps", "60 seconds"),
                ("Dumbbell Overhead Shoulder Press", "3", "10-12 reps", "60 seconds"),
                ("Bodyweight Walking Lunges", "3", "10 steps per leg", "60 seconds"),
                ("Lat Pulldown or Band Pulls", "3", "12-15 reps", "60 seconds"),
                ("Farmer's Carry with Dumbbells", "3", "40 steps", "60 seconds"),
            ], "Quad stretch, shoulder stretches, seated twist (5 mins)"),
            ("Day 6: Aerobic Play & Fun Movement", "Endurance & Agility", "Dynamic stretches (5 mins)", [
                ("Swimming, Cycling, Tennis, or Dance Cardio", "1", "30-45 mins", "Moderate effort"),
                ("Bodyweight Squats to Toes", "2", "15 reps", "30 seconds"),
            ], "Leg stretches, side body stretches (5 mins)"),
            ("Day 7: Deep Rest & Rejuvenation", "Weekly Restoration", "Gentle morning movement", [
                ("Relaxing Walk", "1", "20 mins", "Casual"),
                ("Full Body Restorative Stretching", "1", "15 mins", "Self-paced"),
            ], "Quality sleep, meal prep, mental decompression"),
        ]

    plan_parts = [banner]
    plan_parts.append(f"### Personalized 7-Day Fitness Blueprint for {username}\n")
    plan_parts.append(f"**Target Goal:** {goal} | **Intensity Level:** {intensity} | **Parameters:** {age} years, {weight} kg\n\n")

    for day_title, focus, warmup, exercises, cooldown in split:
        plan_parts.append(f"### {day_title}")
        plan_parts.append(f"- **Focus:** {focus}")
        plan_parts.append(f"- **Warm-Up:** {warmup}")
        plan_parts.append("- **Main Exercises:**")
        for name, sets, reps, rest in exercises:
            plan_parts.append(f"  * **{name}**: {sets} sets × {reps} | Rest: {rest}")
        plan_parts.append(f"- **Cool-Down & Mobility:** {cooldown}\n")

    plan_parts.append(DISCLAIMER_TEXT)
    return "\n".join(plan_parts)


def generate_workout_gemini(
    username: str,
    user_id: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
) -> Tuple[str, bool]:
    """Generates a structured 7-day fitness plan using Google Gemini API.

    Returns:
        Tuple[str, bool]: (generated_plan_text, is_mock_mode)
    """
    # Check if Gemini API key is configured
    if not settings.is_gemini_configured:
        logger.info("Gemini API key is not configured. Utilizing high-quality mock workout plan.")
        return _generate_mock_workout_plan(username, user_id, age, weight, goal, intensity), True

    prompt = _build_workout_prompt(username, user_id, age, weight, goal, intensity)
    system_instruction = (
        "You are FitBuddy AI, an elite certified exercise physiologist and strength & conditioning specialist. "
        "Produce detailed, safe, structured, and realistic 7-day workout programs formatted cleanly with Markdown headers and bullet points. "
        "Explicitly detail Day 1 through Day 7 with Warm-up, Exercises (sets, reps/duration, rest), and Cool-down. "
        "Always append a standard medical and safety disclaimer."
    )

    try:
        from google import genai
        from google.genai import types

        logger.info("Invoking Google Gemini model %s for user %s", settings.GEMINI_MODEL, user_id)
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

        plan_text = response.text if response and response.text else ""
        if not plan_text.strip():
            raise ValueError("Gemini returned an empty response.")

        # Ensure disclaimer is present
        if "disclaimer" not in plan_text.lower():
            plan_text += DISCLAIMER_TEXT

        return plan_text, False

    except Exception as exc:
        logger.error("Gemini API error during workout plan generation: %s", exc, exc_info=True)
        if settings.ENABLE_MOCK_FALLBACK:
            warning_header = (
                f"> [!WARNING]\n"
                f"> **Gemini API Error Notice**: Live generation encountered an error: `{str(exc)}`.\n"
                f"> FitBuddy safely transitioned to the local plan generator so your workout is ready without interruption.\n\n"
            )
            mock_plan = _generate_mock_workout_plan(username, user_id, age, weight, goal, intensity)
            return warning_header + mock_plan, True
        raise RuntimeError(f"Failed to generate workout plan from Gemini: {exc}") from exc
