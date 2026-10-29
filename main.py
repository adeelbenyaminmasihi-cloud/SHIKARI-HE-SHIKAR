import os
import re
import json
import random
import asyncio
import subprocess
import urllib.parse
import textwrap
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Optional YouTube & Facebook Credentials
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()

FB_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
FB_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "").strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

USED_TOPICS_FILE = "used_topics.json"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
USED_MEDIA_URLS = set()

# Seed pool of diverse "Shikari he Shikar" wildlife matchups to inspire endless unique AI scripts
WILDLIFE_SEED_IDEAS = [
    "Jaguar hunting Caiman crocodile in the Amazon river",
    "Orca Killer Whale pod hunting Great White Shark in open ocean",
    "Honey Badger turning venomous King Cobra into its meal",
    "Giant River Otters ambushing a Caiman in South America",
    "Secretary Bird stomping venomous Black Mamba snake in African savanna",
    "Indian Mongoose outsmarting and hunting a deadly Spectacled Cobra",
    "Golden Eagle diving at 240 km/h to hunt a prowling Red Fox",
    "Siberian Tiger ambushing a Brown Bear in the Russian Taiga",
    "Leopard Seal hunting Emperor Penguins and facing Orca ambush",
    "Nile Crocodile ambushing a Lion crossing the Mara River",
    "Cape Buffalo herd turning the tables on a pride of hunting Lions",
    "Saltwater Crocodile ambushing a Bull Shark in Australian estuaries",
    "Wolverine fighting off Grey Wolves in the frozen Arctic",
    "Harpy Eagle snatching tree-dwelling predators in the rainforest canopy",
    "Electric Eel shocking a Caiman predator in muddy Amazon waters",
    "Tarantula Hawk Wasp paralyzing a giant hunting Tarantula spider",
    "Praying Mantis ambushing a venomous Hornet and small snakes",
    "Bobcat hunting a venomous Rattlesnake in the North American desert",
    "Snow Leopard ambushing mountain predators on Himalayan cliffs",
    "Spotted Hyena clan stealing prey and turning on a lone Leopard",
    "Komodo Dragon ambushing wild boar and facing rival giant lizards",
    "Great Horned Owl silently hunting a Red-tailed Hawk at night",
    "Hippopotamus defending territory and crushing an ambushing Crocodile",
    "Octopus escaping a Moray Eel and ambushing crabs and sharks",
    "Roadrunner bird outrunning and killing a Diamondback Rattlesnake",
    "Serval cat leaping high to catch birds and snakes in tall grass",
    "Goliath Birdeater spider vs Amazonian Wasp predator reversal",
    "Shoebill Stork ambushing baby crocodiles and lungfish in swamps",
    "Polar Bear stalking Arctic seals while facing Walrus counter-attack",
    "Cheetah speed hunt vs Hyena and Lion ambush on the Serengeti",
    "Green Anaconda constricting a Caiman in the Pantanal wetlands",
    "Peregrine Falcon stooping at 300 km/h on smaller birds of prey",
    "Meerkat mob uniting to drive away a deadly Puff Adder snake",
    "African Wild Dog pack outmaneuvering a lone Spotted Hyena",
    "Osprey diving into deep water while avoiding Bald Eagle piracy",
    "Giant Pacific Octopus overpowering a Dogfish Shark on the ocean floor",
    "Caracal cat leaping 10 feet in the air to hunt desert predators",
    "King Snake immune to venom swallowing a deadly Rattlesnake",
    "Sperm Whale diving deep to hunt the Giant Squid in pitch black ocean",
    "Leopard stalking a Python snake in Kruger National Park"
]

# Built-in 2-Minute Wildlife "Shikari he Shikar" Topics (14 scenes each = ~120 seconds)
FALLBACK_WILDLIFE_TOPICS = [
    {
        "topic": "Amazon Jaguar vs Caiman Crocodile: Jab Paani Ka Shikari Khud Shikar Ban Jata Hai",
        "tagline": "Magarmach paani ka badshah kehlata hai, magar Jaguar ke samne wo khud shikar ban jata hai! 🐆🐊",
        "description": "Amazon ke junglon mein Caiman magarmach har janwar ke liye maut hai, lekin jab bhooka Jaguar paani mein chhalang lagata hai to shikari khud shikar ban jata hai!",
        "badge": "SHIKARI HE SHIKAR",
        "hook_visual_1": "jaguar wild jungle",
        "hook_visual_2": "crocodile water eyes",
        "context_urdu": "ایمیزون کے گھنے اور خطرناک جنگلوں میں کیمن مگرمچھ کو پانی کا بے تاج بادشاہ مانا جاتا ہے، جو پانی کے اندر چھپ کر کنارے پر آنے والے ہر جانور کو پلک جھپکتے ہی نگل لیتا ہے۔",
        "context_cap1": "AMAZON KA KHAUFNAK SHIKARI:",
        "context_cap2": "PAANI KA BADSHAH MAGARMACH!",
        "ctx_visual_1": "alligator river swamp",
        "ctx_visual_2": "amazon rainforest river",
        "event_urdu": "مگر قدرت کا ایک ایسا خاموش شکاری بھی ہے جس کے سامنے یہ خوفناک مگرمچھ بھی بے بس ہو جاتا ہے، اور وہ ہے ایمیزون کا طاقتور ترین جیگوار!",
        "event_cap1": "MAGARMACH KA ASLI KHAUF:",
        "event_cap2": "TAQATWAR AMAZON JAGUAR!",
        "evt_visual_1": "jaguar walking forest",
        "evt_visual_2": "leopard eyes close up",
        "impact_urdu": "باقی بڑی بلیوں کے برعکس جیگوار پانی سے ڈرتا نہیں بلکہ ایک ماہر تیراک کی طرح دریا میں اتر کر مگرمچھ کو اسی کے گھر میں جا کر للکارتا ہے۔",
        "impact_cap1": "PAANI SE NA DARNE WALA:",
        "impact_cap2": "DARYA MEIN MAUT KI CHHALANG!",
        "imp_visual_1": "jaguar swimming water",
        "imp_visual_2": "crocodile swimming river",
        "response_urdu": "جیگوار کے جبڑوں کی طاقت تمام بڑی بلیوں میں سب سے زیادہ ہوتی ہے، جو شیر سے بھی دوگنی طاقت سے سیدھا مگرمچھ کی کھوپڑی اور گردن کو ایک ہی وار میں توڑ دیتا ہے۔",
        "response_cap1": "SAB SE TAQATWAR JABRAY:",
        "response_cap2": "EK WAR MEIN KHOPRI KHATAM!",
        "res_visual_1": "big cat roaring teeth",
        "res_visual_2": "crocodile jaws open",
        "future_urdu": "یوں جو مگرمچھ خود کسی شکار کے انتظار میں گھات لگائے بیٹھا تھا، چند ہی سیکنڈز میں جیگوار کے پنجوں میں آ کر خود شکار بن جاتا ہے۔",
        "future_cap1": "QUDRAT KA QANOON:",
        "future_cap2": "SHIKARI KHUD SHIKAR BAN GAYA!",
        "fut_visual_1": "jaguar resting tree",
        "fut_visual_2": "wilderness sunset jungle",
        "vid_queries": ["jaguar", "crocodile", "jungle river", "wild cat"]
    },
    {
        "topic": "Orca Killer Whale vs Great White Shark: Samandar Mein Shikari Ka Shikar",
        "tagline": "Great White Shark se poora samandar darta hai, magar Orca ko dekh kar Shark kyun bhaag jati hai? 🐋🦈",
        "description": "Samandar ke sab se khaufnak shikari Great White Shark ka jab Killer Whale (Orca) se samna hota hai, to kaise shikari khud shikar ban jata hai!",
        "badge": "OCEAN PREDATORS",
        "hook_visual_1": "great white shark underwater",
        "hook_visual_2": "orca killer whale ocean",
        "context_urdu": "لاکھوں سالوں سے گریٹ وائٹ شارک کو سمندر کا سب سے خوفناک شکاری سمجھا جاتا رہا ہے، جس کے تیز دھار دانتوں سے بچنا کسی بھی سمندری مخلوق کے لیے ناممکن ہوتا ہے۔",
        "context_cap1": "SAMANDAR KA KHAUF:",
        "context_cap2": "GREAT WHITE SHARK!",
        "ctx_visual_1": "shark teeth underwater",
        "ctx_visual_2": "deep blue ocean waves",
        "event_urdu": "لیکن جب سمندر کے اصل حکمران یعنی اورکا کلر وہیلز کا جھنڈ میدان میں آتا ہے، تو یہی خوفناک شارک اپنی جان بچانے کے لیے سینکڑوں میل دور بھاگنے پر مجبور ہو جاتی ہے۔",
        "event_cap1": "SAMANDAR KA ASLI BADSHAH:",
        "event_cap2": "ORCA KILLER WHALE!",
        "evt_visual_1": "killer whale jumping",
        "evt_visual_2": "shark swimming fast",
        "impact_urdu": "اورکا وہیلز نہ صرف شارک سے جسامت میں بہت بڑی ہوتی ہیں بلکہ ان کا دماغ انتہائی تیز ہوتا ہے اور وہ ایک منظم فوج کی طرح مل کر حملہ کرتی ہیں۔",
        "impact_cap1": "TEZ DIMAAGH AUR TEAMWORK:",
        "impact_cap2": "FOUJ KI TARAH HAMLA!",
        "imp_visual_1": "pod of whales ocean",
        "imp_visual_2": "underwater predator fish",
        "response_urdu": "اورکا وہیل شارک کو ٹکر مار کر اسے پانی میں الٹا کر دیتی ہے، جس سے شارک پر فالج جیسی کیفیت طاری ہو جاتی ہے جسے ٹونک اموبیلائزیشن کہا جاتا ہے۔",
        "response_cap1": "SHARK KO ULTA KAR DENA:",
        "response_cap2": "TONIC IMMOBILITY KA JAAL!",
        "res_visual_1": "whale underwater diving",
        "res_visual_2": "shark deep sea",
        "future_urdu": "اس کے بعد سمندر کا سب سے بڑا شکاری بے بس ہو کر خود شکار بن جاتا ہے، اور اس علاقے سے شارکس مہینوں تک غائب ہو جاتی ہیں۔",
        "future_cap1": "SAMANDAR KA FAISLA:",
        "future_cap2": "SHARK KHUD SHIKAR BAN GAYI!",
        "fut_visual_1": "ocean sunset waves",
        "fut_visual_2": "whale tail water",
        "vid_queries": ["shark", "whale", "ocean underwater", "sea predator"]
    },
    {
        "topic": "Honey Badger vs Deadly King Cobra: Zehreele Shikari Ka Be-Khauf Shikar",
        "tagline": "Zehreele King Cobra ka zehar bhi Honey Badger ka kuch nahi bigaar sakta! 🦡🐍",
        "description": "Jungle ka sab se be-khauf janwar Honey Badger kaise khatarnak aur zehreele saanpon ko apna shikar bana leta hai? Dekhiye qudrat ka hairat angez manzar!",
        "badge": "FEARLESS HUNTER",
        "hook_visual_1": "king cobra snake hood",
        "hook_visual_2": "badger wild animal",
        "context_urdu": "افریقہ اور ایشیا کے جنگلوں میں زہریلے کوبرا اور بلیک مامبا جیسے سانپ موت کی علامت سمجھے جاتے ہیں، جن کا ایک ڈنک بڑے سے بڑے جانور کو منٹوں میں ختم کر سکتا ہے۔",
        "context_cap1": "ZEHREELE SAANP KA KHAUF:",
        "context_cap2": "EK DUNK MEIN KHEL KHATAM!",
        "ctx_visual_1": "venomous snake fangs",
        "ctx_visual_2": "african savanna dry grass",
        "event_urdu": "مگر ہنی بیجر جسے اردو میں بجو کہا جاتا ہے، ان جان لیوا سانپوں سے ڈرنے کے بجائے الٹا انہیں اپنا پسندیدہ کھانا بنانے کے لیے ڈھونڈتا پھرتا ہے۔",
        "event_cap1": "JUNGLE KA BE-KHAUF BADSHAH:",
        "event_cap2": "HONEY BADGER KA HAMLA!",
        "evt_visual_1": "fierce small mammal",
        "evt_visual_2": "snake slithering sand",
        "impact_urdu": "ہنی بیجر کی چمڑی اتنی موٹی اور ڈھیلی ہوتی ہے کہ سانپ کے دانت اکثر اس کے جسم میں اتر ہی نہیں پاتے اور وہ پلٹ کر سانپ کی گردن دبوچ لیتا ہے۔",
        "impact_cap1": "MOTI CHAMRI KI DHAAL:",
        "impact_cap2": "SAANP KE DAANT BE-ASAR!",
        "imp_visual_1": "wild animal desert",
        "imp_visual_2": "cobra strike pose",
        "response_urdu": "سب سے حیرت انگیز بات یہ ہے کہ ہنی بیجر کے خون میں قدرتی طور پر زہر کے خلاف ایسی قوت مدافعت ہوتی ہے کہ اگر کوبرا اسے ڈس بھی لے، تو یہ تھوڑی دیر بے ہوش ہونے کے بعد دوبارہ اٹھ کھڑا ہوتا ہے!",
        "response_cap1": "QUDRATI IMMUNITY KA RAAZ:",
        "response_cap2": "ZEHAR BHI BE-ASAR HO JATA HAI!",
        "res_visual_1": "snake scales closeup",
        "res_visual_2": "safari wildlife nature",
        "future_urdu": "ہوش میں آتے ہی ہنی بیجر اپنا ادھورا شکار مکمل کرتا ہے اور یوں جنگل کا سب سے زہریلا شکاری خود شکار بن کر ختم ہو جاتا ہے۔",
        "future_cap1": "SHIKARI HE SHIKAR:",
        "future_cap2": "ZEHREELA COBRA HAAR GAYA!",
        "fut_visual_1": "desert sunset landscape",
        "fut_visual_2": "wild predator walking",
        "vid_queries": ["snake", "cobra", "wildlife", "desert animal"]
    },
    {
        "topic": "Golden Eagle vs Red Fox and Mountain Wolves: Aasman Se Utarti Maut",
        "tagline": "Zameen par shikar dhoondne wali Lomri aur Bheriye jab khud Uqaab ka shikar ban jate hain! 🦅🦊",
        "description": "Paharon aur barfani maidan mein jab Golden Eagle 240 km/h ki raftar se neeche aata hai, to zameen ke shikari khud shikar ban jate hain!",
        "badge": "SKY PREDATOR",
        "hook_visual_1": "golden eagle flying",
        "hook_visual_2": "red fox snow",
        "context_urdu": "برفانی پہاڑوں اور کھلے میدانوں میں لومڑی اور بھیڑیے انتہائی چالاک شکاری مانے جاتے ہیں، جو چھوٹے جانوروں اور پرندوں کا چپکے سے شکار کرتے ہیں۔",
        "context_cap1": "ZAMEEN KE CHALAK SHIKARI:",
        "context_cap2": "LOMRI AUR BHERIYE!",
        "ctx_visual_1": "fox hunting snow",
        "ctx_visual_2": "wolf pack winter",
        "event_urdu": "لیکن جب وہ اپنے شکار کے پیچھے بھاگ رہے ہوتے ہیں تو انہیں اندازہ بھی نہیں ہوتا کہ بادلوں کے اوپر سے دو تیز ترین آنکھیں خود ان کا نشانہ لے رہی ہیں۔",
        "event_cap1": "AASMAN SE DO TEZ AANKHEIN:",
        "event_cap2": "GOLDEN EAGLE KA NISHANA!",
        "evt_visual_1": "eagle eyes closeup",
        "evt_visual_2": "mountain peaks clouds",
        "impact_urdu": "گولڈن ایگل یعنی سنہری عقاب سات فٹ لمبے پروں اور دو سو چالیس کلومیٹر فی گھنٹہ کی طوفانی رفتار کے ساتھ آسمان سے میزائل کی طرح نیچے جھپٹتا ہے۔",
        "impact_cap1": "240 KM/H KI RAFTAR:",
        "impact_cap2": "MISSILE KI TARAH HAMLA!",
        "imp_visual_1": "eagle diving sky",
        "imp_visual_2": "snowy mountain valley",
        "response_urdu": "عقاب کے خنجر جیسے پنجوں کی گرفت اتنی خوفناک ہوتی ہے کہ اس کے دباؤ سے لومڑی اور یہاں تک کہ جوان بھیڑیے کی ہڈیاں بھی ٹوٹ جاتی ہیں۔",
        "response_cap1": "KHANJAR JAISE PANJAY:",
        "response_cap2": "LOHE JAISI MAZBOOT GIRAFT!",
        "res_visual_1": "hawk talons closeup",
        "res_visual_2": "fox running snow",
        "future_urdu": "جو شکاری زمین پر کسی دوسرے کا شکار کرنے نکلا تھا، عقاب کے پنجوں میں جکڑ کر ہواؤں میں اڑتا ہوا خود شکار بن جاتا ہے۔",
        "future_cap1": "AASMAN KA FAISLA:",
        "future_cap2": "SHIKARI KHUD SHIKAR BANA!",
        "fut_visual_1": "eagle perched rock",
        "fut_visual_2": "winter mountains sunset",
        "vid_queries": ["eagle", "fox", "wolf", "mountain wildlife"]
    },
    {
        "topic": "Mongoose vs Black Mamba: Maut Ke Saudagar Ka Sab Se Bara Dushman",
        "tagline": "Duniya ke sab se tez aur zehreele saanp Black Mamba ko Mongoose kaise shikar karta hai? 🐍⚡",
        "description": "Black Mamba aur Cobra ki bijli jaisi raftar ke samne har janwar haar jata hai, magar Nevla (Mongoose) apni phurti se shikari ko shikar bana deta hai!",
        "badge": "DEADLY DUEL",
        "hook_visual_1": "mongoose wild animal",
        "hook_visual_2": "black snake dangerous",
        "context_urdu": "افریقہ کے جنگلوں میں بلیک مامبا اور کنگ کوبرا ایسے شکاری ہیں جن کے سایے سے بھی شیر اور ہاتھی جیسے بڑے جانور راستہ بدل لیتے ہیں۔",
        "context_cap1": "JUNGLE KA SAB SE BADA KHAUF:",
        "context_cap2": "ZEHREELA BLACK MAMBA!",
        "ctx_visual_1": "snake open mouth fangs",
        "ctx_visual_2": "wild savanna bushes",
        "event_urdu": "مگر ایک چھوٹا سا نیولا یعنی مونگوز وہ واحد شکاری ہے جو سانپ کو دیکھ کر بھاگتا نہیں بلکہ سیدھا اس کی آنکھوں میں آنکھیں ڈال کر مقابلہ شروع کر دیتا ہے۔",
        "event_cap1": "CHOTA JISM MAGAR BADA JIGAR:",
        "event_cap2": "NEVLE KA KHULA CHALLENGE!",
        "evt_visual_1": "meerkat mongoose standing",
        "evt_visual_2": "cobra raised hood",
        "impact_urdu": "سانپ بار بار بجلی کی تیزی سے وار کرتا ہے، لیکن نیولے کے ریفلیکسز اتنے تیز ہوتے ہیں کہ وہ ملی سیکنڈز کے فرق سے ہر وار کو ہوا میں ہی چکما دے دیتا ہے۔",
        "impact_cap1": "BIJLI JAISE REFLEXES:",
        "impact_cap2": "HAR WAR KO CHAKMA!",
        "imp_visual_1": "fast animal jumping",
        "imp_visual_2": "snake striking sand",
        "response_urdu": "لگاتار حملے کر کے جب زہریلا سانپ تھک کر چور ہو جاتا ہے، تو نیولا موقع پاتے ہی چھلانگ لگا کر سیدھا سانپ کے سر کو اپنے تیز دانتوں میں دبوچ لیتا ہے۔",
        "response_cap1": "JAB SAANP THAK JATA HAI:",
        "response_cap2": "EK CHHALANG MEIN FAISLA!",
        "res_visual_1": "predator teeth bite",
        "res_visual_2": "snake in dry grass",
        "future_urdu": "صرف چند منٹوں کے اس سنسنی خیز مقابلے میں زہر کا بادشاہ کہلانے والا شکاری بے بس ہو کر نیولے کا شکار بن جاتا ہے۔",
        "future_cap1": "SANSANI KHEZ MUQABLA:",
        "future_cap2": "SHIKARI HE SHIKAR BAN GAYA!",
        "fut_visual_1": "mongoose desert nature",
        "fut_visual_2": "african sunset wildlife",
        "vid_queries": ["snake", "mongoose", "safari", "predator"]
    },
    {
        "topic": "Giant River Otters vs Caiman: Amazon Ki Nadi Mein Gang War",
        "tagline": "Akela Caiman magarmach khatarnak hai, magar Giant Otters ki family usey zinda chaba jati hai! 🦦🐊",
        "description": "Amazon ki nadiyon mein Giant River Otters jinhein 'River Wolves' kaha jata hai, kaise khaufnak Caiman aur Anaconda ka shikar karte hain!",
        "badge": "RIVER WOLVES",
        "hook_visual_1": "otter swimming water",
        "hook_visual_2": "alligator jaws water",
        "context_urdu": "عام طور پر اودبلاؤ یعنی اوٹرز کو ایک معصوم اور کھیلنے کودنے والا جانور سمجھا جاتا ہے، جو مچھلیاں پکڑ کر اپنا گزارہ کرتا ہے۔",
        "context_cap1": "DIKHNE MEIN MASOOM:",
        "context_cap2": "MAGAR PAANI KE BHERIYE!",
        "ctx_visual_1": "river otter family",
        "ctx_visual_2": "amazon river jungle",
        "event_urdu": "لیکن ایمیزون کے جائنٹ ریور اوٹرز چھ فٹ تک لمبے ہوتے ہیں اور مقامی زبان میں انہیں دریائی بھیڑیے کہا جاتا ہے کیونکہ یہ پورے خاندان کے ساتھ مل کر شکار کرتے ہیں۔",
        "event_cap1": "6 FOOT LAMBAY GIANT OTTERS:",
        "event_cap2": "POORI FAMILY KA EK SATH HAMLA!",
        "evt_visual_1": "otters swimming group",
        "evt_visual_2": "crocodile hiding water",
        "impact_urdu": "جب کوئی کیمن مگرمچھ ان کے علاقے میں شکار کرنے کے ارادے سے آتا ہے، تو سات سے آٹھ اوٹرز مل کر اسے چاروں طرف سے گھیر لیتے ہیں۔",
        "impact_cap1": "CHARON TARAF SE GHERAO:",
        "impact_cap2": "MAGARMACH PHANS GAYA!",
        "imp_visual_1": "splashing river water",
        "imp_visual_2": "alligator tail splash",
        "response_urdu": "کچھ اوٹرز آگے سے مگرمچھ کا دھیان بھٹکاتے ہیں جبکہ باقی پیچھے سے اس کی دم اور گردن پر تیز دھار دانتوں سے تابڑ توڑ حملے کرتے ہیں یہاں تک کہ مگرمچھ نڈھال ہو جاتا ہے۔",
        "response_cap1": "SOCHI SAMJHI STRATEGY:",
        "response_cap2": "HAR TARAF SE TABAR-TOR WAR!",
        "res_visual_1": "otter teeth closeup",
        "res_visual_2": "muddy river bank",
        "future_urdu": "یوں اتحاد اور حکمت عملی کی طاقت سے ایمیزون کا خوفناک شکاری مگرمچھ اپنے ہی پانی میں ان دریائی بھیڑیوں کا شکار بن جاتا ہے۔",
        "future_cap1": "ITTEHAD KI TAQAT:",
        "future_cap2": "SHIKARI KHUD SHIKAR BAN GAYA!",
        "fut_visual_1": "rainforest river mist",
        "fut_visual_2": "otters resting log",
        "vid_queries": ["otter", "crocodile", "river wildlife", "jungle"]
    }
]


def load_used_topics():
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
    try:
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(used_list[-300:], f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [!] Could not save used topics: {e}")


def get_fresh_wildlife_seeds(used_topics):
    """Selects unused wildlife 'Shikari he Shikar' ideas to feed Gemini for fresh topics."""
    used_lower = " | ".join(used_topics).lower()
    fresh = [idea for idea in WILDLIFE_SEED_IDEAS if idea.lower() not in used_lower]
    if len(fresh) < 8:
        fresh = WILDLIFE_SEED_IDEAS[:]
    random.shuffle(fresh)
    return fresh[:12]


def discover_gemini_model():
    """Dynamically finds a working Gemini model via REST API so 404 errors never happen."""
    if not GEMINI_API_KEY:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            models = r.json().get("models", [])
            capable = []
            for m in models:
                methods = m.get("supportedGenerationMethods", [])
                name = m.get("name", "")
                if "generateContent" in methods and "gemini" in name.lower():
                    capable.append(name)
            preferred_order = [
                "models/gemini-2.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-1.5-flash-latest",
                "models/gemini-1.5-flash",
                "models/gemini-2.5-pro",
                "models/gemini-1.5-pro-latest"
            ]
            for pref in preferred_order:
                if pref in capable:
                    return pref
            for c in capable:
                if "flash" in c and "tts" not in c and "image" not in c:
                    return c
            if capable:
                return capable[0]
    except Exception as e:
        print(f"  [!] Gemini model discovery note: {e}")
    return "models/gemini-2.0-flash"


def build_fourteen_scenes_from_template(chosen):
    """Expands a wildlife topic template into a full 14-scene (~2 minute) documentary script."""
    v_queries = chosen.get("vid_queries", ["wildlife predator", "jungle animal", "nature", "safari"])
    while len(v_queries) < 4:
        v_queries.append("wildlife")

    return {
        "topic": chosen["topic"],
        "title": f"🦁 {chosen['topic']} | Shikari He Shikar",
        "tagline": chosen["tagline"],
        "description": chosen["description"],
        "hashtags": "#ShikariHeShikar #WildlifeDocumentary #UrduDocumentary #AnimalFacts #JungleLaws #PredatorVsPrey #NatureInUrdu #ViralWildlife",
        "category_badge": chosen.get("badge", "SHIKARI HE SHIKAR"),
        "scenes": [
            {
                "tts_urdu": "جنگل کے بے رحم قانون میں کوئی بھی شکاری ہمیشہ کے لیے محفوظ نہیں ہوتا، کیونکہ یہاں ایک ہی لمحے میں بازی پلٹ جاتی ہے اور شکاری خود شکار بن جاتا ہے!",
                "caption_part1": "JUNGLE KA BE-RAHAM QANOON:",
                "caption_part2": "SHIKARI KHUD SHIKAR!",
                "search_query_1": chosen["hook_visual_1"],
                "search_query_2": chosen["hook_visual_2"],
                "video_query": v_queries[0]
            },
            {
                "tts_urdu": chosen["context_urdu"],
                "caption_part1": chosen["context_cap1"],
                "caption_part2": chosen["context_cap2"],
                "search_query_1": chosen["ctx_visual_1"],
                "search_query_2": chosen["ctx_visual_2"],
                "video_query": ""
            },
            {
                "tts_urdu": "قدرت کے اس میدانِ جنگ میں ہر جانور کو زندہ رہنے کے لیے یا تو تیز دوڑنا پڑتا ہے یا پھر اپنے سے بڑے شکاری کو مات دینے کا ہنر سیکھنا پڑتا ہے۔",
                "caption_part1": "ZINDA REHNE KI JANG:",
                "caption_part2": "HAR KADAM PAR KHATRA!",
                "search_query_1": "wild jungle forest dark",
                "search_query_2": "predator eyes in dark",
                "video_query": ""
            },
            {
                "tts_urdu": chosen["event_urdu"],
                "caption_part1": chosen["event_cap1"],
                "caption_part2": chosen["event_cap2"],
                "search_query_1": chosen["evt_visual_1"],
                "search_query_2": chosen["evt_visual_2"],
                "video_query": v_queries[1]
            },
            {
                "tts_urdu": "وائلڈ لائف ماہرین اور کیمروں میں قید ہونے والے مناظر بتاتے ہیں کہ جب یہ دونوں آمنے سامنے آتے ہیں تو جنگل میں سناٹا چھا جاتا ہے۔",
                "caption_part1": "JAB DONO AAMNE SAMNE AAYE:",
                "caption_part2": "JUNGLE MEIN SANNATA!",
                "search_query_1": "safari wildlife camera",
                "search_query_2": "wild animals face off",
                "video_query": ""
            },
            {
                "tts_urdu": chosen["impact_urdu"],
                "caption_part1": chosen["impact_cap1"],
                "caption_part2": chosen["impact_cap2"],
                "search_query_1": chosen["imp_visual_1"],
                "search_query_2": chosen["imp_visual_2"],
                "video_query": v_queries[2]
            },
            {
                "tts_urdu": "یہاں طاقت سے زیادہ رفتار، صبر اور صحیح وقت پر کیے گئے ایک زوردار وار کا فیصلہ چلتا ہے، جہاں ایک چھوٹی سی غلطی کا مطلب سیدھی موت ہے۔",
                "caption_part1": "EK CHOTI SI GHALTI:",
                "caption_part2": "AUR KHEL HAMESHA KE LIYE KHATAM!",
                "search_query_1": "animal running fast dust",
                "search_query_2": "claws predator hunting",
                "video_query": ""
            },
            {
                "tts_urdu": chosen["response_urdu"],
                "caption_part1": chosen["response_cap1"],
                "caption_part2": chosen["response_cap2"],
                "search_query_1": chosen["res_visual_1"],
                "search_query_2": chosen["res_visual_2"],
                "video_query": ""
            },
            {
                "tts_urdu": "اپنے آپ کو ناقابلِ شکست سمجھنے والا شکاری جب اس اچانک اور طوفانی جوابی حملے کی زد میں آتا ہے تو اسے سنبھلنے کا موقع تک نہیں ملتا۔",
                "caption_part1": "ACHANAK JAWABI HAMLA:",
                "caption_part2": "SAMBHALNE KA MAUQA NAHI MILA!",
                "search_query_1": "wild animal fight action",
                "search_query_2": "dramatic storm clouds nature",
                "video_query": v_queries[3]
            },
            {
                "tts_urdu": "یہی قدرت کا وہ حیرت انگیز توازن ہے جو کسی بھی ایک شکاری کو پورے جنگل یا سمندر پر اندھا راج کرنے کی اجازت نہیں دیتا۔",
                "caption_part1": "QUDRAT KA AMAZING BALANCE:",
                "caption_part2": "HAR SHIKARI KE UPAR EK SHIKARI!",
                "search_query_1": "african savanna ecosystem",
                "search_query_2": "wilderness river aerial",
                "video_query": ""
            },
            {
                "tts_urdu": chosen["future_urdu"],
                "caption_part1": chosen["future_cap1"],
                "caption_part2": chosen["future_cap2"],
                "search_query_1": chosen["fut_visual_1"],
                "search_query_2": chosen["fut_visual_2"],
                "video_query": ""
            },
            {
                "tts_urdu": "اس واقعے سے ثابت ہوتا ہے کہ جنگل کی دنیا میں غرور اور طاقت ہمیشہ کام نہیں آتی، بلکہ ہوشیاری اور بے خوفی ہی اصل ہتھیار ہیں۔",
                "caption_part1": "TAQAT NAHI HOSHIYARI:",
                "caption_part2": "BE-KHAUFI ASLI HATHIYAR HAI!",
                "search_query_1": "lion resting sunset",
                "search_query_2": "eagle soaring high mountain",
                "video_query": ""
            },
            {
                "tts_urdu": "شکاری ہی شکار کی یہ سنسنی خیز داستان ہمیں یاد دلاتی ہے کہ فطرت کے راز انسان کی سوچ سے کہیں زیادہ گہرے اور حیران کن ہیں۔",
                "caption_part1": "SHIKARI HE SHIKAR:",
                "caption_part2": "FITRAT KE HAIRAN KUN RAAZ!",
                "search_query_1": "deep jungle sunlight rays",
                "search_query_2": "wild animal silhouette sunset",
                "video_query": ""
            },
            {
                "tts_urdu": "وائلڈ لائف اور شکاری جانوروں کی ایسی ہی سنسنی خیز اور سچی دستاویزی ویڈیوز روزانہ دیکھنے کے لیے ہمارے چینل کو ابھی سبسکرائب اور فالو کر لیں!",
                "caption_part1": "DAILY WILDLIFE VIDEOS KE LIYE:",
                "caption_part2": "ABHI SUBSCRIBE AUR FOLLOW KAREIN!",
                "search_query_1": "smartphone video streaming",
                "search_query_2": "wildlife photographer camera",
                "video_query": ""
            }
        ]
    }


def generate_script_via_gemini(used_topics):
    """Uses Gemini REST API to generate a fresh 14-scene (2-minute) Wildlife 'Shikari he Shikar' documentary script."""
    if not GEMINI_API_KEY:
        return None

    model_name = discover_gemini_model()
    if not model_name:
        return None

    seed_ideas = get_fresh_wildlife_seeds(used_topics)
    print(f"🦁 Generating 2-Minute Wildlife 'Shikari he Shikar' Script via {model_name}...")

    prompt = f"""You are a National Geographic & BBC Earth style wildlife documentary producer creating a thrilling 2-minute (14-scene) Urdu documentary video on the theme: "SHIKARI HE SHIKAR" (The Hunter Becomes the Hunted / Predator vs. Predator / When Prey Turns the Tables on the Predator).

Here are some unused wildlife matchup ideas for inspiration (or pick another real-world wildlife 'Shikari he Shikar' battle):
{json.dumps(seed_ideas, ensure_ascii=False)}

CRITICAL RULE: Do NOT pick any topic or animal matchup already in this used list:
{json.dumps(used_topics[-80:], ensure_ascii=False)}

Pick ONE specific, real-world wildlife encounter where a deadly predator becomes the hunted (or gets defeated/eaten by another animal).
Return ONLY a raw, valid JSON object with NO markdown formatting and NO code fences, matching this EXACT schema:
{{
  "topic": "Unique concise English topic title (e.g. Leopard vs Python: Jungle Ambush Reversal)",
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
      "search_query_1": "2-3 word English stock photo keyword of the specific animal/nature scene (e.g. jaguar swimming river)",
      "search_query_2": "2-3 word English stock photo keyword of the second animal/action (e.g. crocodile jaws water)",
      "video_query": "1-2 word English stock video keyword of the animal (e.g. jaguar, crocodile, eagle, snake, shark)"
    }}
  ]
}}
Ensure the `scenes` array has EXACTLY 14 scenes so the total video duration is 2 minutes (~120 seconds), telling a complete dramatic story from the initial stalk/ambush to the final reversal where the hunter becomes the hunted."""

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "responseMimeType": "application/json"
        }
    }

    try:
        resp = requests.post(url, json=payload, timeout=45)
        if resp.status_code != 200:
            del payload["generationConfig"]["responseMimeType"]
            resp = requests.post(url, json=payload, timeout=45)

        if resp.status_code == 200:
            candidates = resp.json().get("candidates", [])
            if candidates:
                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                raw
