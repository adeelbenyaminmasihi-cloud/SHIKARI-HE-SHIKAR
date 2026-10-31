# Dynamic combinatorial pools for infinite lifetime variety
WILDLIFE_BIOMES = [
    "Amazon Rainforest & Muddy Rivers", "African Serengeti & Mara River",
    "Deep Midnight & Trench Ocean", "Siberian Taiga & Frozen Tundra",
    "Australian Outback & Estuaries", "Sonoran & Sahara Deserts",
    "Southeast Asian Mangrove Swamps", "Himalayan & Andean Mountain Cliffs",
    "Pantanal Wetlands & Flooded Forests", "Coral Reefs & Kelp Forests",
    "Madagascar Spiny Forests", "Borneo Dense Tropical Canopy",
    "Congo Basin Dark Jungle", "Galapagos Volcanic Coastwaters",
    "North American Yellowstone Wilderness", "Okavango Delta Marshes"
]

REVERSAL_ANGLES = [
    "An apex predator ambushed by a smaller, fearless counter-predator",
    "A venomous hunter defeated by a predator with natural venom immunity",
    "A solitary giant predator overwhelmed by coordinated pack or mob tactics",
    "An aerial raptor stooping from the sky to hunt a ground carnivore",
    "An aquatic ambush predator dragged out of its element by a land hunter",
    "A nocturnal stealth predator outsmarted in pitch darkness",
    "Armored or massive prey turning the tables and crushing a stalking predator",
    "Arachnid, insect, or crustacean assassin paralyzing a vertebrate hunter"
]


def load_used_topics():
    """Loads the entire lifetime history of used topics without truncation."""
    if os.path.exists(USED_TOPICS_FILE):
        try:
            with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def save_used_topics(used_list):
    """Saves 100% of used topics for lifetime persistence (no [-300:] slicing)."""
    try:
        # Remove exact duplicates while preserving chronological order
        deduped = list(dict.fromkeys(used_list))
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(deduped, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [!] Could not save used topics: {e}")


def normalize_matchup_key(text):
    """Extracts sorted core words to detect duplicate animal matchups even with different titles."""
    stop_words = {
        "vs", "versus", "the", "in", "and", "of", "on", "to", "a", "an", "into",
        "its", "for", "with", "from", "by", "at", "jab", "ka", "ki", "ke", "mein",
        "par", "se", "khud", "shikar", "shikari", "ban", "jata", "hai", "he",
        "hunting", "ambushing", "turning", "fighting", "outsmarting", "stalking"
    }
    words = re.findall(r"[a-z]{3,}", text.lower())
    core = [w for w in words if w not in stop_words]
    return set(core)


def is_topic_duplicate(candidate_topic, used_topics):
    """Returns True if candidate_topic shares the same core animal matchup with any past topic."""
    cand_lower = candidate_topic.lower().strip()
    cand_prefix = cand_lower.split(":")[0].strip()
    cand_tokens = normalize_matchup_key(cand_prefix)

    for past in used_topics:
        past_lower = past.lower().strip()
        if cand_lower == past_lower:
            return True
        past_prefix = past_lower.split(":")[0].strip()
        if cand_prefix and cand_prefix == past_prefix:
            return True
        past_tokens = normalize_matchup_key(past_prefix)
        # If both topics share 2+ specific animal/species words in the matchup header, reject it
        if len(cand_tokens.intersection(past_tokens)) >= 2:
            return True
    return False


def get_fresh_wildlife_seeds(used_topics):
    """Filters out any seed whose animals were already covered, and mixes in new biome/angle prompts."""
    fresh = [idea for idea in WILDLIFE_SEED_IDEAS if not is_topic_duplicate(idea, used_topics)]
    random.shuffle(fresh)
    return fresh[:6]


def generate_script_via_gemini(used_topics):
    if not GEMINI_API_KEY:
        return None

    model_name = discover_gemini_model()
    if not model_name:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"

    # Retry up to 3 times to guarantee valid JSON and a 100% unseen animal matchup
    for attempt in range(1, 4):
        seed_ideas = get_fresh_wildlife_seeds(used_topics)
        chosen_biome = random.choice(WILDLIFE_BIOMES)
        chosen_angle = random.choice(REVERSAL_ANGLES)
        entropy_salt = random.randint(100000, 999999)

        print(f"🦁 [Attempt {attempt}/3] Generating fresh 'Shikari he Shikar' Script via {model_name} (Biome: {chosen_biome})...")

        prompt = f"""You are a National Geographic & BBC Earth style wildlife documentary producer creating a thrilling 2-minute (14-scene) Urdu documentary video on the theme: "SHIKARI HE SHIKAR" (The Hunter Becomes the Hunted / Predator vs. Predator / When Prey Turns the Tables on the Predator).

Random Generation Salt: #{entropy_salt}
Suggested Biome Focus: {chosen_biome}
Suggested Dramatic Angle: {chosen_angle}
Optional Seed Ideas (ONLY use if not already in the banned list below, or invent a completely new real-world wildlife matchup from global zoology):
{json.dumps(seed_ideas, ensure_ascii=False)}

STRICT LIFETIME BANNED LIST — DO NOT PICK ANY TOPIC OR ANIMAL MATCHUP ALREADY LISTED HERE:
{json.dumps(used_topics, ensure_ascii=False)}

CRITICAL RULES:
1. Pick ONE specific, real-world wildlife encounter where a deadly predator becomes the hunted (or gets defeated/eaten by another animal).
2. The animal pair MUST NOT overlap with any matchup in the BANNED LIST above. Explore diverse species across mammals, reptiles, raptors, marine predators, amphibians, and deadly arthropods!
3. Return ONLY a raw, valid JSON object with NO markdown formatting and NO code fences, matching this EXACT schema:
{{
  "topic": "Unique concise English matchup title formatted as 'Animal A vs Animal B: Short Subtitle'",
  "title": "🦁 Catchy Roman Urdu Title | Shikari He Shikar",
  "tagline": "Thrilling 1-line Roman Urdu hook with wildlife emojis",
  "description": "2-3 sentence Roman Urdu summary of this wildlife battle and how the hunter becomes the hunted.",
  "hashtags": "#ShikariHeShikar #WildlifeDocumentary #UrduDocumentary #AnimalBattles #JungleLife #PredatorVsPrey #Viral",
  "category_badge": "SHIKARI HE SHIKAR",
  "scenes": [
    {{
      "tts_urdu": "Must be written in REAL URDU SCRIPT (اردو رسم الخط) around 22 to 28 words in dramatic National Geographic documentary style so TTS speaks naturally for ~8.5 seconds.",
      "caption_part1": "SHORT UPPERCASE ROMAN URDU LINE 1 (MAX 24 CHARS)",
      "caption_part2": "SHORT UPPERCASE ROMAN URDU LINE 2 (MAX 24 CHARS)",
      "search_query_1": "2-4 word English visual description of the animal in bright daylight for AI image generation",
      "search_query_2": "2-4 word English visual description of the second animal shot in bright daylight",
      "video_query": "1-2 word simple English animal name for stock video search"
    }}
  ]
}}
Ensure the `scenes` array has EXACTLY 14 scenes so the total video duration is 2 minutes (~120 seconds)."""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.95,
                "responseMimeType": "application/json"
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code != 200:
                del payload["generationConfig"]["responseMimeType"]
                resp = requests.post(url, json=payload, timeout=60)

            if resp.status_code == 200:
                candidates = resp.json().get("candidates", [])
                if candidates:
                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                    script_data = json.loads(raw_text.strip())
                    scenes = script_data.get("scenes", [])
                    topic = script_data.get("topic", "").strip()

                    if topic and len(scenes) >= 10:
                        if is_topic_duplicate(topic, used_topics):
                            print(f"  [!] Gemini suggested a duplicate matchup ('{topic}'). Retrying with new salt...")
                            used_topics.append(topic)
                            continue
                        print(f"  [✓] Gemini generated 100% fresh script ({len(scenes)} scenes): {topic}")
                        return script_data
            else:
                print(f"  [!] Gemini API status {resp.status_code}: {resp.text[:160]}")
        except Exception as e:
            print(f"  [!] Gemini generation attempt {attempt} error: {e}")

    return None


def generate_script_data():
    used = load_used_topics()

    ai_script = generate_script_via_gemini(used)
    if ai_script:
        used.append(ai_script["topic"])
        save_used_topics(used)
        return ai_script

    # Only filter fallback topics that have NEVER been used
    available = [t for t in FALLBACK_WILDLIFE_TOPICS if not is_topic_duplicate(t["topic"], used)]
    if not available:
        raise RuntimeError(
            "All fallback topics have been used and Gemini API failed to generate a new script. "
            "Aborting run to strictly prevent repeating an old topic!"
        )

    chosen = random.choice(available)
    used.append(chosen["topic"])
    save_used_topics(used)
    print(f"🔥 Building 2-Minute (14-Scene) Wildlife Script for: {chosen['topic']}")
    return build_fourteen_scenes_from_template(chosen)
