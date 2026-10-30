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
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageStat

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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
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
        "hook_visual_1": "jaguar wild cat river",
        "hook_visual_2": "crocodile alligator water",
        "context_urdu": "ایمیزون کے گھنے اور خطرناک جنگلوں میں کیمن مگرمچھ کو پانی کا بے تاج بادشاہ مانا جاتا ہے، جو پانی کے اندر چھپ کر کنارے پر آنے والے ہر جانور کو پلک جھپکتے ہی نگل لیتا ہے۔",
        "context_cap1": "AMAZON KA KHAUFNAK SHIKARI:",
        "context_cap2": "PAANI KA BADSHAH MAGARMACH!",
        "ctx_visual_1": "crocodile swamp river",
        "ctx_visual_2": "amazon rainforest river daylight",
        "event_urdu": "مگر قدرت کا ایک ایسا خاموش شکاری بھی ہے جس کے سامنے یہ خوفناک مگرمچھ بھی بے بس ہو جاتا ہے، اور وہ ہے ایمیزون کا طاقتور ترین جیگوار!",
        "event_cap1": "MAGARMACH KA ASLI KHAUF:",
        "event_cap2": "TAQATWAR AMAZON JAGUAR!",
        "evt_visual_1": "jaguar walking jungle daylight",
        "evt_visual_2": "leopard face closeup",
        "impact_urdu": "باقی بڑی بلیوں کے برعکس جیگوار پانی سے ڈرتا نہیں بلکہ ایک ماہر تیراک کی طرح دریا میں اتر کر مگرمچھ کو اسی کے گھر میں جا کر للکارتا ہے۔",
        "impact_cap1": "PAANI SE NA DARNE WALA:",
        "impact_cap2": "DARYA MEIN MAUT KI CHHALANG!",
        "imp_visual_1": "jaguar swimming river water",
        "imp_visual_2": "crocodile swimming river",
        "response_urdu": "جیگوار کے جبڑوں کی طاقت تمام بڑی بلیوں میں سب سے زیادہ ہوتی ہے، جو شیر سے بھی دوگنی طاقت سے سیدھا مگرمچھ کی کھوپڑی اور گردن کو ایک ہی وار میں توڑ دیتا ہے۔",
        "response_cap1": "SAB SE TAQATWAR JABRAY:",
        "response_cap2": "EK WAR MEIN KHOPRI KHATAM!",
        "res_visual_1": "jaguar roaring teeth",
        "res_visual_2": "crocodile jaws open",
        "future_urdu": "یوں جو مگرمچھ خود کسی شکار کے انتظار میں گھات لگائے بیٹھا تھا، چند ہی سیکنڈز میں جیگوار کے پنجوں میں آ کر خود شکار بن جاتا ہے۔",
        "future_cap1": "QUDRAT KA QANOON:",
        "future_cap2": "SHIKARI KHUD SHIKAR BAN GAYA!",
        "fut_visual_1": "jaguar resting tree branch",
        "fut_visual_2": "tropical jungle river sunlight",
        "vid_queries": ["jaguar", "crocodile", "jungle river", "leopard"]
    },
    {
        "topic": "Orca Killer Whale vs Great White Shark: Samandar Mein Shikari Ka Shikar",
        "tagline": "Great White Shark se poora samandar darta hai, magar Orca ko dekh kar Shark kyun bhaag jati hai? 🐋🦈",
        "description": "Samandar ke sab se khaufnak shikari Great White Shark ka jab Killer Whale (Orca) se samna hota hai, to kaise shikari khud shikar ban jata hai!",
        "badge": "OCEAN PREDATORS",
        "hook_visual_1": "great white shark ocean",
        "hook_visual_2": "orca killer whale jumping",
        "context_urdu": "لاکھوں سالوں سے گریٹ وائٹ شارک کو سمندر کا سب سے خوفناک شکاری سمجھا جاتا رہا ہے، جس کے تیز دھار دانتوں سے بچنا کسی بھی سمندری مخلوق کے لیے ناممکن ہوتا ہے۔",
        "context_cap1": "SAMANDAR KA KHAUF:",
        "context_cap2": "GREAT WHITE SHARK!",
        "ctx_visual_1": "shark swimming blue water",
        "ctx_visual_2": "ocean waves sunlight",
        "event_urdu": "لیکن جب سمندر کے اصل حکمران یعنی اورکا کلر وہیلز کا جھنڈ میدان میں آتا ہے، تو یہی خوفناک شارک اپنی جان بچانے کے لیے سینکڑوں میل دور بھاگنے پر مجبور ہو جاتی ہے۔",
        "event_cap1": "SAMANDAR KA ASLI BADSHAH:",
        "event_cap2": "ORCA KILLER WHALE!",
        "evt_visual_1": "orca killer whale ocean",
        "evt_visual_2": "great white shark underwater",
        "impact_urdu": "اورکا وہیلز نہ صرف شارک سے جسامت میں بہت بڑی ہوتی ہیں بلکہ ان کا دماغ انتہائی تیز ہوتا ہے اور وہ ایک منظم فوج کی طرح مل کر حملہ کرتی ہیں۔",
        "impact_cap1": "TEZ DIMAAGH AUR TEAMWORK:",
        "impact_cap2": "FOUJ KI TARAH HAMLA!",
        "imp_visual_1": "orca whales pod ocean",
        "imp_visual_2": "shark underwater blue sea",
        "response_urdu": "اورکا وہیل شارک کو ٹکر مار کر اسے پانی میں الٹا کر دیتی ہے، جس سے شارک پر فالج جیسی کیفیت طاری ہو جاتی ہے جسے ٹونک اموبیلائزیشن کہا جاتا ہے۔",
        "response_cap1": "SHARK KO ULTA KAR DENA:",
        "response_cap2": "TONIC IMMOBILITY KA JAAL!",
        "res_visual_1": "whale breach ocean splash",
        "res_visual_2": "shark swimming coral reef",
        "future_urdu": "اس کے بعد سمندر کا سب سے بڑا شکاری بے بس ہو کر خود شکار بن جاتا ہے، اور اس علاقے سے شارکس مہینوں تک غائب ہو جاتی ہیں۔",
        "future_cap1": "SAMANDAR KA FAISLA:",
        "future_cap2": "SHARK KHUD SHIKAR BAN GAYI!",
        "fut_visual_1": "bright ocean horizon sunlight",
        "fut_visual_2": "orca whale tail water",
        "vid_queries": ["shark", "whale", "ocean", "underwater"]
    },
    {
        "topic": "Honey Badger vs Deadly King Cobra: Zehreele Shikari Ka Be-Khauf Shikar",
        "tagline": "Zehreele King Cobra ka zehar bhi Honey Badger ka kuch nahi bigaar sakta! 🦡🐍",
        "description": "Jungle ka sab se be-khauf janwar Honey Badger kaise khatarnak aur zehreele saanpon ko apna shikar bana leta hai? Dekhiye qudrat ka hairat angez manzar!",
        "badge": "FEARLESS HUNTER",
        "hook_visual_1": "king cobra snake hood",
        "hook_visual_2": "honey badger wild animal",
        "context_urdu": "افریقہ اور ایشیا کے جنگلوں میں زہریلے کوبرا اور بلیک مامبا جیسے سانپ موت کی علامت سمجھے جاتے ہیں، جن کا ایک ڈنک بڑے سے بڑے جانور کو منٹوں میں ختم کر سکتا ہے۔",
        "context_cap1": "ZEHREELE SAANP KA KHAUF:",
        "context_cap2": "EK DUNK MEIN KHEL KHATAM!",
        "ctx_visual_1": "cobra snake closeup",
        "ctx_visual_2": "african savanna daylight",
        "event_urdu": "مگر ہنی بیجر جسے اردو میں بجو کہا جاتا ہے، ان جان لیوا سانپوں سے ڈرنے کے بجائے الٹا انہیں اپنا پسندیدہ کھانا بنانے کے لیے ڈھونڈتا پھرتا ہے۔",
        "event_cap1": "JUNGLE KA BE-KHAUF BADSHAH:",
        "event_cap2": "HONEY BADGER KA HAMLA!",
        "evt_visual_1": "badger mammal wildlife",
        "evt_visual_2": "snake desert sand",
        "impact_urdu": "ہنی بیجر کی چمڑی اتنی موٹی اور ڈھیلی ہوتی ہے کہ سانپ کے دانت اکثر اس کے جسم میں اتر ہی نہیں پاتے اور وہ پلٹ کر سانپ کی گردن دبوچ لیتا ہے۔",
        "impact_cap1": "MOTI CHAMRI KI DHAAL:",
        "impact_cap2": "SAANP KE DAANT BE-ASAR!",
        "imp_visual_1": "badger walking savanna",
        "imp_visual_2": "king cobra strike",
        "response_urdu": "سب سے حیرت انگیز بات یہ ہے کہ ہنی بیجر کے خون میں قدرتی طور پر زہر کے خلاف ایسی قوت مدافعت ہوتی ہے کہ اگر کوبرا اسے ڈس بھی لے، تو یہ تھوڑی دیر بے ہوش ہونے کے بعد دوبارہ اٹھ کھڑا ہوتا ہے!",
        "response_cap1": "QUDRATI IMMUNITY KA RAAZ:",
        "response_cap2": "ZEHAR BHI BE-ASAR HO JATA HAI!",
        "res_visual_1": "snake scales macro",
        "res_visual_2": "african safari wildlife",
        "future_urdu": "ہوش میں آتے ہی ہنی بیجر اپنا ادھورا شکار مکمل کرتا ہے اور یوں جنگل کا سب سے زہریلا شکاری خود شکار بن کر ختم ہو جاتا ہے۔",
        "future_cap1": "SHIKARI HE SHIKAR:",
        "future_cap2": "ZEHREELA COBRA HAAR GAYA!",
        "fut_visual_1": "savanna golden sunlight",
        "fut_visual_2": "wild animal nature",
        "vid_queries": ["snake", "cobra", "safari", "wildlife"]
    },
    {
        "topic": "Golden Eagle vs Red Fox and Mountain Wolves: Aasman Se Utarti Maut",
        "tagline": "Zameen par shikar dhoondne wali Lomri aur Bheriye jab khud Uqaab ka shikar ban jate hain! 🦅🦊",
        "description": "Paharon aur barfani maidan mein jab Golden Eagle 240 km/h ki raftar se neeche aata hai, to zameen ke shikari khud shikar ban jate hain!",
        "badge": "SKY PREDATOR",
        "hook_visual_1": "golden eagle flying sky",
        "hook_visual_2": "red fox snow mountain",
        "context_urdu": "برفانی پہاڑوں اور کھلے میدانوں میں لومڑی اور بھیڑیے انتہائی چالاک شکاری مانے جاتے ہیں، جو چھوٹے جانوروں اور پرندوں کا چپکے سے شکار کرتے ہیں۔",
        "context_cap1": "ZAMEEN KE CHALAK SHIKARI:",
        "context_cap2": "LOMRI AUR BHERIYE!",
        "ctx_visual_1": "red fox hunting snow",
        "ctx_visual_2": "grey wolf winter snow",
        "event_urdu": "لیکن جب وہ اپنے شکار کے پیچھے بھاگ رہے ہوتے ہیں تو انہیں اندازہ بھی نہیں ہوتا کہ بادلوں کے اوپر سے دو تیز ترین آنکھیں خود ان کا نشانہ لے رہی ہیں۔",
        "event_cap1": "AASMAN SE DO TEZ AANKHEIN:",
        "event_cap2": "GOLDEN EAGLE KA NISHANA!",
        "evt_visual_1": "golden eagle head closeup",
        "evt_visual_2": "snowy mountain peaks sun",
        "impact_urdu": "گولڈن ایگل یعنی سنہری عقاب سات فٹ لمبے پروں اور دو سو چالیس کلومیٹر فی گھنٹہ کی طوفانی رفتار کے ساتھ آسمان سے میزائل کی طرح نیچے جھپٹتا ہے۔",
        "impact_cap1": "240 KM/H KI RAFTAR:",
        "impact_cap2": "MISSILE KI TARAH HAMLA!",
        "imp_visual_1": "eagle diving wings spread",
        "imp_visual_2": "mountain valley landscape",
        "response_urdu": "عقاب کے خنجر جیسے پنجوں کی گرفت اتنی خوفناک ہوتی ہے کہ اس کے دباؤ سے لومڑی اور یہاں تک کہ جوان بھیڑیے کی ہڈیاں بھی ٹوٹ جاتی ہیں۔",
        "response_cap1": "KHANJAR JAISE PANJAY:",
        "response_cap2": "LOHE JAISI MAZBOOT GIRAFT!",
        "res_visual_1": "eagle talons bird of prey",
        "res_visual_2": "fox running winter",
        "future_urdu": "جو شکاری زمین پر کسی دوسرے کا شکار کرنے نکلا تھا، عقاب کے پنجوں میں جکڑ کر ہواؤں میں اڑتا ہوا خود شکار بن جاتا ہے۔",
        "future_cap1": "AASMAN KA FAISLA:",
        "future_cap2": "SHIKARI KHUD SHIKAR BANA!",
        "fut_visual_1": "golden eagle perched cliff",
        "fut_visual_2": "bright mountain sunrise",
        "vid_queries": ["eagle", "fox", "wolf", "mountain"]
    },
    {
        "topic": "Mongoose vs Black Mamba: Maut Ke Saudagar Ka Sab Se Bara Dushman",
        "tagline": "Duniya ke sab se tez aur zehreele saanp Black Mamba ko Mongoose kaise shikar karta hai? 🐍⚡",
        "description": "Black Mamba aur Cobra ki bijli jaisi raftar ke samne har janwar haar jata hai, magar Nevla (Mongoose) apni phurti se shikari ko shikar bana deta hai!",
        "badge": "DEADLY DUEL",
        "hook_visual_1": "mongoose animal standing",
        "hook_visual_2": "cobra snake hood",
        "context_urdu": "افریقہ کے جنگلوں میں بلیک مامبا اور کنگ کوبرا ایسے شکاری ہیں جن کے سایے سے بھی شیر اور ہاتھی جیسے بڑے جانور راستہ بدل لیتے ہیں۔",
        "context_cap1": "JUNGLE KA SAB SE BADA KHAUF:",
        "context_cap2": "ZEHREELA BLACK MAMBA!",
        "ctx_visual_1": "snake fangs closeup",
        "ctx_visual_2": "savanna grassland sun",
        "event_urdu": "مگر ایک چھوٹا سا نیولا یعنی مونگوز وہ واحد شکاری ہے جو سانپ کو دیکھ کر بھاگتا نہیں بلکہ سیدھا اس کی آنکھوں میں آنکھیں ڈال کر مقابلہ شروع کر دیتا ہے۔",
        "event_cap1": "CHOTA JISM MAGAR BADA JIGAR:",
        "event_cap2": "NEVLE KA KHULA CHALLENGE!",
        "evt_visual_1": "mongoose desert sunlight",
        "evt_visual_2": "cobra snake sand",
        "impact_urdu": "سانپ بار بار بجلی کی تیزی سے وار کرتا ہے، لیکن نیولے کے ریفلیکسز اتنے تیز ہوتے ہیں کہ وہ ملی سیکنڈز کے فرق سے ہر وار کو ہوا میں ہی چکما دے دیتا ہے۔",
        "impact_cap1": "BIJLI JAISE REFLEXES:",
        "impact_cap2": "HAR WAR KO CHAKMA!",
        "imp_visual_1": "mongoose jumping action",
        "imp_visual_2": "snake striking pose",
        "response_urdu": "لگاتار حملے کر کے جب زہریلا سانپ تھک کر چور ہو جاتا ہے، تو نیولا موقع پاتے ہی چھلانگ لگا کر سیدھا سانپ کے سر کو اپنے تیز دانتوں میں دبوچ لیتا ہے۔",
        "response_cap1": "JAB SAANP THAK JATA HAI:",
        "response_cap2": "EK CHHALANG MEIN FAISLA!",
        "res_visual_1": "mongoose closeup face",
        "res_visual_2": "snake in grass",
        "future_urdu": "صرف چند منٹوں کے اس سنسنی خیز مقابلے میں زہر کا بادشاہ کہلانے والا شکاری بے بس ہو کر نیولے کا شکار بن جاتا ہے۔",
        "future_cap1": "SANSANI KHEZ MUQABLA:",
        "future_cap2": "SHIKARI HE SHIKAR BAN GAYA!",
        "fut_visual_1": "mongoose standing rock",
        "fut_visual_2": "golden african plains",
        "vid_queries": ["snake", "meerkat", "safari", "wildlife"]
    },
    {
        "topic": "Giant River Otters vs Caiman: Amazon Ki Nadi Mein Gang War",
        "tagline": "Akela Caiman magarmach khatarnak hai, magar Giant Otters ki family usey zinda chaba jati hai! 🦦🐊",
        "description": "Amazon ki nadiyon mein Giant River Otters jinhein 'River Wolves' kaha jata hai, kaise khaufnak Caiman aur Anaconda ka shikar karte hain!",
        "badge": "RIVER WOLVES",
        "hook_visual_1": "river otter swimming",
        "hook_visual_2": "alligator crocodile river",
        "context_urdu": "عام طور پر اودبلاؤ یعنی اوٹرز کو ایک معصوم اور کھیلنے کودنے والا جانور سمجھا جاتا ہے، جو مچھلیاں پکڑ کر اپنا گزارہ کرتا ہے۔",
        "context_cap1": "DIKHNE MEIN MASOOM:",
        "context_cap2": "MAGAR PAANI KE BHERIYE!",
        "ctx_visual_1": "river otters family",
        "ctx_visual_2": "amazon river forest",
        "event_urdu": "لیکن ایمیزون کے جائنٹ ریور اوٹرز چھ فٹ تک لمبے ہوتے ہیں اور مقامی زبان میں انہیں دریائی بھیڑیے کہا جاتا ہے کیونکہ یہ پورے خاندان کے ساتھ مل کر شکار کرتے ہیں۔",
        "event_cap1": "6 FOOT LAMBAY GIANT OTTERS:",
        "event_cap2": "POORI FAMILY KA EK SATH HAMLA!",
        "evt_visual_1": "otter closeup water",
        "evt_visual_2": "crocodile eyes water",
        "impact_urdu": "جب کوئی کیمن مگرمچھ ان کے علاقے میں شکار کرنے کے ارادے سے آتا ہے، تو سات سے آٹھ اوٹرز مل کر اسے چاروں طرف سے گھیر لیتے ہیں۔",
        "impact_cap1": "CHARON TARAF SE GHERAO:",
        "impact_cap2": "MAGARMACH PHANS GAYA!",
        "imp_visual_1": "river water splash",
        "imp_visual_2": "crocodile jaws open",
        "response_urdu": "کچھ اوٹرز آگے سے مگرمچھ کا دھیان بھٹکاتے ہیں جبکہ باقی پیچھے سے اس کی دم اور گردن پر تیز دھار دانتوں سے تابڑ توڑ حملے کرتے ہیں یہاں تک کہ مگرمچھ نڈھال ہو جاتا ہے۔",
        "response_cap1": "SOCHI SAMJHI STRATEGY:",
        "response_cap2": "HAR TARAF SE TABAR-TOR WAR!",
        "res_visual_1": "otter swimming fast",
        "res_visual_2": "river bank jungle",
        "future_urdu": "یوں اتحاد اور حکمت عملی کی طاقت سے ایمیزون کا خوفناک شکاری مگرمچھ اپنے ہی پانی میں ان دریائی بھیڑیوں کا شکار بن جاتا ہے۔",
        "future_cap1": "ITTEHAD KI TAQAT:",
        "future_cap2": "SHIKARI KHUD SHIKAR BAN GAYA!",
        "fut_visual_1": "rainforest river sunlight",
        "fut_visual_2": "otters resting log",
        "vid_queries": ["otter", "crocodile", "river", "jungle"]
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
    used_lower = " | ".join(used_topics).lower()
    fresh = [idea for idea in WILDLIFE_SEED_IDEAS if idea.lower() not in used_lower]
    if len(fresh) < 8:
        fresh = WILDLIFE_SEED_IDEAS[:]
    random.shuffle(fresh)
    return fresh[:12]


def discover_gemini_model():
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
    v_queries = chosen.get("vid_queries", ["wildlife", "jungle", "nature", "safari"])
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
                "search_query_1": "african safari lions daylight",
                "search_query_2": "leopard in tree sunlight",
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
                "search_query_1": "tiger walking jungle river",
                "search_query_2": "wild animals savanna",
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
                "search_query_1": "cheetah running fast savanna",
                "search_query_2": "eagle flying wings spread",
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
                "search_query_1": "lion roaring closeup",
                "search_query_2": "crocodile splashing river",
                "video_query": v_queries[3]
            },
            {
                "tts_urdu": "یہی قدرت کا وہ حیرت انگیز توازن ہے جو کسی بھی ایک شکاری کو پورے جنگل یا سمندر پر اندھا راج کرنے کی اجازت نہیں دیتا۔",
                "caption_part1": "QUDRAT KA AMAZING BALANCE:",
                "caption_part2": "HAR SHIKARI KE UPAR EK SHIKARI!",
                "search_query_1": "serengeti national park wildlife",
                "search_query_2": "tropical rainforest waterfall",
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
                "search_query_1": "lion king savanna golden hour",
                "search_query_2": "hawk perched mountain peak",
                "video_query": ""
            },
            {
                "tts_urdu": "شکاری ہی شکار کی یہ سنسنی خیز داستان ہمیں یاد دلاتی ہے کہ فطرت کے راز انسان کی سوچ سے کہیں زیادہ گہرے اور حیران کن ہیں۔",
                "caption_part1": "SHIKARI HE SHIKAR:",
                "caption_part2": "FITRAT KE HAIRAN KUN RAAZ!",
                "search_query_1": "green jungle sunlight rays",
                "search_query_2": "elephant herd african plains",
                "video_query": ""
            },
            {
                "tts_urdu": "وائلڈ لائف اور شکاری جانوروں کی ایسی ہی سنسنی خیز اور سچی دستاویزی ویڈیوز روزانہ دیکھنے کے لیے ہمارے چینل کو ابھی سبسکرائب اور فالو کر لیں!",
                "caption_part1": "DAILY WILDLIFE VIDEOS KE LIYE:",
                "caption_part2": "ABHI SUBSCRIBE AUR FOLLOW KAREIN!",
                "search_query_1": "wildlife photographer nature",
                "search_query_2": "majestic tiger portrait",
                "video_query": ""
            }
        ]
    }


def generate_script_via_gemini(used_topics):
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
      "search_query_1": "2-4 word English visual description of the animal in bright daylight for AI image generation (e.g. jaguar hunting crocodile in amazon river)",
      "search_query_2": "2-4 word English visual description of the second animal shot in bright daylight (e.g. caiman crocodile open jaws in river)",
      "video_query": "1-2 word simple English animal name for stock video search (e.g. jaguar, crocodile, eagle, snake, shark, lion, tiger, wolf)"
    }}
  ]
}}
Ensure the `scenes` array has EXACTLY 14 scenes so the total video duration is 2 minutes (~120 seconds)."""

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
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                script_data = json.loads(raw_text.strip())
                scenes = script_data.get("scenes", [])
                if script_data.get("topic") and len(scenes) >= 10:
                    print(f"  [✓] Gemini generated 2-min Wildlife script ({len(scenes)} scenes): {script_data['topic']}")
                    return script_data
        else:
            print(f"  [!] Gemini API status {resp.status_code}: {resp.text[:160]}")
    except Exception as e:
        print(f"  [!] Gemini generation fallback note: {e}")

    return None


def generate_script_data():
    used = load_used_topics()

    ai_script = generate_script_via_gemini(used)
    if ai_script:
        used.append(ai_script["topic"])
        save_used_topics(used)
        return ai_script

    available = [t for t in FALLBACK_WILDLIFE_TOPICS if t["topic"] not in used]
    if not available:
        used = []
        available = FALLBACK_WILDLIFE_TOPICS

    chosen = random.choice(available)
    used.append(chosen["topic"])
    save_used_topics(used)
    print(f"🔥 Building 2-Minute (14-Scene) Wildlife Script for: {chosen['topic']}")
    return build_fourteen_scenes_from_template(chosen)


def verify_and_grade_image(filepath):
    """
    Strictly verifies that a downloaded image is NOT dark/black/blank,
    auto-brightens dark-ish photos, and normalizes size to 1080x1920 RGB.
    """
    try:
        with Image.open(filepath) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w < 240 or h < 240:
                return False

            stat = ImageStat.Stat(im)
            mean_brightness = sum(stat.mean) / 3.0
            mean_stddev = sum(stat.stddev) / 3.0

            # Reject solid black/brown/blank images (fixes the dark screen bug!)
            if mean_brightness < 22 or mean_stddev < 10:
                print(f"  [!] Rejecting dark/blank image (brightness={mean_brightness:.1f}, stddev={mean_stddev:.1f})")
                return False

            # Center-crop & resize cleanly to 1080x1920 so FFmpeg never has aspect-ratio glitches
            target_ratio = 1080 / 1920
            img_ratio = w / h
            if img_ratio > target_ratio:
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                im = im.crop((left, 0, left + new_w, h))
            else:
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                im = im.crop((0, top, w, top + new_h))
            im = im.resize((1080, 1920), Image.Resampling.LANCZOS)

            # If the image is somewhat dim, automatically boost brightness so video is vivid
            if mean_brightness < 85:
                boost = min(1.65, max(1.18, 95.0 / max(mean_brightness, 1.0)))
                im = ImageEnhance.Brightness(im).enhance(boost)

            im = ImageEnhance.Contrast(im).enhance(1.15)
            im = ImageEnhance.Color(im).enhance(1.22)
            im.save(filepath, "JPEG", quality=94)
        return True
    except Exception as e:
        print(f"  [!] Image verification error: {e}")
        return False


def fetch_pollinations_graphic(query, filename):
    """Generates custom 1080x1920 vertical HD wildlife graphics using Pollinations.ai."""
    clean_q = re.sub(r"[^a-zA-Z0-9\s,]", " ", query).strip()
    vivid_prompt = (
        f"{clean_q}, National Geographic wildlife photography, bright golden daylight, "
        f"ultra detailed, 8k resolution, vibrant natural colors, sharp focus, cinematic action shot"
    )
    encoded_prompt = urllib.parse.quote(vivid_prompt)
    seed = random.randint(1000, 9999999)

    endpoints = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&seed={seed}&model=flux&nologo=true&enhance=true",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&seed={seed}&model=turbo&nologo=true",
        f"https://gen.pollinations.ai/image/{encoded_prompt}?width=1080&height=1920&seed={seed}&nologo=true"
    ]

    for url in endpoints:
        try:
            r = requests.get(url, headers=HEADERS, timeout=28)
            if r.status_code == 200 and len(r.content) > 18000:
                with open(filename, "wb") as f:
                    f.write(r.content)
                if verify_and_grade_image(filename):
                    print(f"  [✓] Pollinations.ai AI Graphic generated for '{query}'")
                    return filename
        except Exception as e:
            print(f"  [!] Pollinations attempt note ({query}): {e}")
    return None


def fetch_contextual_stock_video(query, filename):
    """Fetches HD Stock Video using Official PIXABAY_API_KEY first, then Mixkit fallback."""
    if not query:
        return None

    search_terms = [query.strip()]
    words = query.strip().split()
    if len(words) > 1:
        search_terms.append(words[0])

    if PIXABAY_API_KEY:
        for term in search_terms:
            try:
                encoded = urllib.parse.quote(term)
                p_url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={encoded}&safesearch=true&per_page=15"
                r = requests.get(p_url, headers=HEADERS, timeout=20)
                if r.status_code == 200:
                    hits = r.json().get("hits", [])
                    for hit in hits:
                        videos = hit.get("videos", {})
                        vid_url = (
                            videos.get("medium", {}).get("url")
                            or videos.get("small", {}).get("url")
                            or videos.get("large", {}).get("url")
                        )
                        if vid_url and vid_url not in USED_MEDIA_URLS:
                            USED_MEDIA_URLS.add(vid_url)
                            vr = requests.get(vid_url, headers=HEADERS, timeout=30)
                            if vr.status_code == 200 and len(vr.content) > 50000:
                                with open(filename, "wb") as f:
                                    f.write(vr.content)
                                print(f"  [✓] Pixabay Stock Video downloaded for '{term}'")
                                return filename
            except Exception as e:
                print(f"  [!] Pixabay video skip ({term}): {e}")

    slug = urllib.parse.quote(words[0].lower())
    search_url = f"https://mixkit.co/free-stock-video/{slug}/"
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=18)
        if resp.status_code == 200:
            pattern = r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4'
            mp4_urls = re.findall(pattern, resp.text)
            fresh_urls = [u for u in mp4_urls if u not in USED_MEDIA_URLS]
            if fresh_urls:
                chosen_url = fresh_urls[0]
                USED_MEDIA_URLS.add(chosen_url)
                vid_resp = requests.get(chosen_url, headers=HEADERS, timeout=25)
                if vid_resp.status_code == 200 and len(vid_resp.content) > 50000:
                    with open(filename, "wb") as f:
                        f.write(vid_resp.content)
                    print(f"  [✓] Mixkit Stock Video downloaded for '{slug}'")
                    return filename
    except Exception:
        pass
    return None


def create_bright_wildlife_poster(query, filename):
    """
    Creates a vibrant, high-contrast emerald & gold studio graphic card if all network sources fail,
    ensuring the video section is NEVER dark or black.
    """
    img = Image.new("RGB", (1080, 1920), (15, 65, 55))
    draw = ImageDraw.Draw(img)

    for y in range(1920):
        ratio = y / 1920.0
        r = int(20 + 95 * (1.0 - abs(ratio - 0.45)))
        g = int(75 + 115 * (1.0 - ratio * 0.5))
        b = int(55 + 85 * ratio)
        draw.line([(0, y), (1080, y)], fill=(r, g, b))

    for radius in range(120, 520, 80):
        draw.ellipse(
            [540 - radius, 760 - radius, 540 + radius, 760 + radius],
            outline=(255, 215, 80),
            width=3
        )
    draw.rounded_rectangle([40, 40, 1040, 1880], radius=36, outline=(255, 215, 0), width=6)

    try:
        title_font = ImageFont.truetype(FONT_BOLD, 68)
        sub_font = ImageFont.truetype(FONT_BOLD, 42)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    lines = textwrap.wrap(query.upper(), width=16)[:3]
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(((1080 - tw) // 2, 660 + i * 90), line, font=title_font, fill=(255, 240, 150))

    sub_text = "WILDLIFE DOCUMENTARY HD"
    sbbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    stw = sbbox[2] - sbbox[0]
    draw.text(((1080 - stw) // 2, 980), sub_text, font=sub_font, fill=(255, 255, 255))

    img.save(filename, "JPEG", quality=94)
    return filename


def fetch_exact_scene_photo(query, filename):
    """
    Multi-Engine Graphics Pipeline:
    1. Pollinations.ai AI Image Generator (Primary Custom Graphics)
    2. Official Pixabay HD Photo API (with keyword simplification)
    3. Wikimedia Commons Public Domain Wildlife Photos
    4. Bright Wildlife Studio Graphic Poster (Never dark!)
    """
    # 1. Pollinations.ai AI Graphics
    polli_file = fetch_pollinations_graphic(query, filename)
    if polli_file:
        return polli_file

    # 2. Official Pixabay Image API
    if PIXABAY_API_KEY:
        words = [w for w in re.sub(r"[^a-zA-Z0-9\s]", " ", query).split() if len(w) > 2]
        candidate_queries = [query.strip()]
        if len(words) >= 2:
            candidate_queries.append(f"{words[0]} {words[1]}")
        if words:
            candidate_queries.append(words[0])

        for q_try in candidate_queries:
            try:
                encoded = urllib.parse.quote(q_try)
                p_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={encoded}&image_type=photo&safesearch=true&per_page=15"
                r = requests.get(p_url, headers=HEADERS, timeout=18)
                if r.status_code == 200:
                    hits = r.json().get("hits", [])
                    for hit in hits:
                        img_url = hit.get("largeImageURL") or hit.get("webformatURL")
                        if img_url and img_url not in USED_MEDIA_URLS:
                            USED_MEDIA_URLS.add(img_url)
                            img_r = requests.get(img_url, headers=HEADERS, timeout=15)
                            if img_r.status_code == 200 and len(img_r.content) > 15000:
                                with open(filename, "wb") as f:
                                    f.write(img_r.content)
                                if verify_and_grade_image(filename):
                                    print(f"  [✓] Pixabay HD Photo downloaded for '{q_try}'")
                                    return filename
            except Exception as e:
                print(f"  [!] Pixabay photo skip ({q_try}): {e}")

    # 3. Wikimedia Commons High-Res Wildlife API
    try:
        w_url = (
            "https://commons.wikimedia.org/w/api.php"
            f"?action=query&generator=search&gsrsearch=filetype:bitmap%20{urllib.parse.quote(query)}"
            "&gsrlimit=8&prop=imageinfo&iiprop=url&iiurlwidth=1280&format=json"
        )
        r = requests.get(w_url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for _, pdata in pages.items():
                ii = pdata.get("imageinfo", [{}])[0]
                img_url = ii.get("thumburl") or ii.get("url")
                if img_url and img_url not in USED_MEDIA_URLS:
                    USED_MEDIA_URLS.add(img_url)
                    img_r = requests.get(img_url, headers=HEADERS, timeout=15)
                    if img_r.status_code == 200 and len(img_r.content) > 18000:
                        with open(filename, "wb") as f:
                            f.write(img_r.content)
                        if verify_and_grade_image(filename):
                            print(f"  [✓] Wikimedia HD Photo downloaded for '{query}'")
                            return filename
    except Exception:
        pass

    print(f"  [i] Using bright studio graphic poster for '{query}'")
    return create_bright_wildlife_poster(query, filename)


def create_burned_hud_overlay(caption_text, badge_text, scene_idx, total_scenes, part_num):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(220):
        alpha = int(130 * (1 - y / 220))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    for y in range(1320, 1920):
        alpha = int(175 * ((y - 1320) / 600))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    try:
        badge_font = ImageFont.truetype(FONT_BOLD, 38)
        cap_font = ImageFont.truetype(FONT_BOLD, 64)
    except Exception:
        badge_font = ImageFont.load_default()
        cap_font = ImageFont.load_default()

    bw, bh = 640, 82
    bx, by = (1080 - bw) // 2, 95
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=41, fill=(200, 25, 25, 250), outline=(255, 215, 0, 240), width=4)
    b_text = str(badge_text or "SHIKARI HE SHIKAR").upper()[:24]
    b_bbox = draw.textbbox((0, 0), b_text, font=badge_font)
    b_tw, b_th = b_bbox[2] - b_bbox[0], b_bbox[3] - b_bbox[1]
    draw.text((bx + (bw - b_tw) // 2, by + (bh - b_th) // 2 - 4), b_text, font=badge_font, fill=(255, 255, 255, 255))

    lines = textwrap.wrap(str(caption_text or "SHIKARI HE SHIKAR!").upper(), width=15)
    if not lines:
        lines = ["SHIKARI HE SHIKAR!"]

    line_height = 92
    total_text_h = len(lines) * line_height
    box_y1 = 1420 - (total_text_h // 2)
    box_y2 = box_y1 + total_text_h + 44

    draw.rounded_rectangle([55, box_y1, 1025, box_y2], radius=28, fill=(10, 14, 12, 225), outline=(255, 215, 0, 235), width=4)

    for i, line in enumerate(lines):
        t_bbox = draw.textbbox((0, 0), line, font=cap_font)
        tw = t_bbox[2] - t_bbox[0]
        tx = (1080 - tw) // 2
        ty = box_y1 + 20 + (i * line_height)

        if part_num == 1:
            fill_col = (255, 230, 0, 255) if i == 0 else (255, 255, 255, 255)
        else:
            fill_col = (0, 255, 150, 255) if i == 0 else (255, 230, 0, 255)

        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (0, 5)]:
            draw.text((tx + dx, ty + dy), line, font=cap_font, fill=(0, 0, 0, 255))
        draw.text((tx, ty), line, font=cap_font, fill=fill_col)

    progress_fraction = (scene_idx + (0.5 if part_num == 1 else 1.0)) / max(total_scenes, 1)
    prog_w = int(980 * progress_fraction)
    draw.rounded_rectangle([50, 1835, 1030, 1855], radius=10, fill=(255, 255, 255, 85))
    draw.rounded_rectangle([50, 1835, 50 + max(prog_w, 25), 1855], radius=10, fill=(255, 215, 0, 255))

    out_png = f"hud_{scene_idx}_p{part_num}.png"
    overlay.save(out_png)
    return out_png


def composite_photo_with_hud(photo_path, overlay_path, out_jpg):
    with Image.open(photo_path) as bg, Image.open(overlay_path) as ov:
        bg_rgba = bg.convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
        ov_rgba = ov.convert("RGBA").resize((1080, 1920), Image.Resampling.LANCZOS)
        comp = Image.alpha_composite(bg_rgba, ov_rgba).convert("RGB")
        comp.save(out_jpg, "JPEG", quality=94)
    return out_jpg


async def synthesize_scene_voice(urdu_text, index):
    raw_audio = f"raw_voice_{index}.mp3"
    mastered_audio = f"voice_{index}.m4a"

    communicate = edge_tts.Communicate(urdu_text, voice="ur-PK-AsadNeural", rate="+8%", pitch="-2Hz")
    await communicate.save(raw_audio)

    af_chain = (
        "silenceremove=start_periods=1:start_silence=0.04:start_threshold=-45dB,"
        "highpass=f=75,"
        "bass=g=4:f=110,"
        "treble=g=3:f=4500,"
        "acompressor=threshold=-16dB:ratio=3:attack=5:release=60:makeup=3dB,"
        "apad=pad_dur=0.18"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_audio,
        "-af", af_chain,
        "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
        mastered_audio
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mastered_audio


def get_audio_duration(audio_path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]).decode().strip()
    return max(float(out), 3.0)


def prepare_visual_subclip(media_path, is_video, overlay_path, duration, sub_idx, out_clip):
    common_out_args = [
        "-r", "24", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-video_track_timescale", "24000",
        out_clip
    ]

    if is_video:
        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setsar=1,eq=brightness=0.04:contrast=1.10:saturation=1.18,format=rgba[bg];"
            "[1:v]scale=1080:1920,setsar=1,format=rgba[ov];"
            "[bg][ov]overlay=0:0:shortest=1,format=yuv420p,setsar=1[v]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-t", str(duration), "-i", media_path,
            "-loop", "1", "-framerate", "24", "-t", str(duration), "-i", overlay_path,
            "-filter_complex", vf,
            "-map", "[v]"
        ] + common_out_args
    else:
        direction = 1 if sub_idx % 2 == 0 else -1
        vf = (
            f"[0:v]scale=1240:2200:force_original_aspect_ratio=increase,crop=1240:2200,setsar=1,"
            f"crop=1080:1920:'(in_w-out_w)/2+({direction}*50)*sin(t*1.1)':'(in_h-out_h)/2+65*cos(t*0.8)',"
            f"format=rgba[bg];"
            f"[1:v]scale=1080:1920,setsar=1,format=rgba[ov];"
            f"[bg][ov]overlay=0:0:shortest=1,format=yuv420p,setsar=1[v]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "24", "-t", str(duration), "-i", media_path,
            "-loop", "1", "-framerate", "24", "-t", str(duration), "-i", overlay_path,
            "-filter_complex", vf,
            "-map", "[v]"
        ] + common_out_args

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        baked_jpg = f"baked_{out_clip}.jpg"
        if is_video:
            baked_jpg = create_bright_wildlife_poster("WILDLIFE DOCUMENTARY", baked_jpg)
        else:
            composite_photo_with_hud(media_path, overlay_path, baked_jpg)
        safe_cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "24", "-t", str(duration), "-i", baked_jpg,
            "-vf", "scale=1080:1920,setsar=1,format=yuv420p"
        ] + common_out_args
        subprocess.run(safe_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render_two_cut_scene(scene, idx, total_scenes, badge):
    audio_path = asyncio.run(synthesize_scene_voice(scene["tts_urdu"], idx))
    total_dur = get_audio_duration(audio_path)
    half_dur = round(total_dur / 2.0, 2)
    rem_dur = round(total_dur - half_dur, 2)

    q1 = scene.get("search_query_1", "wildlife predator daylight")
    q2 = scene.get("search_query_2", "jungle animal daylight")
    v_q = scene.get("video_query", "")

    vid_file = fetch_contextual_stock_video(v_q, f"stock_vid_{idx}.mp4") if v_q else None
    if vid_file:
        media1, is_vid1 = vid_file, True
    else:
        media1 = fetch_exact_scene_photo(q1, f"photo_{idx}_1.jpg")
        is_vid1 = False

    media2 = fetch_exact_scene_photo(q2, f"photo_{idx}_2.jpg")

    ov1 = create_burned_hud_overlay(scene.get("caption_part1", "SHIKARI HE SHIKAR"), badge, idx, total_scenes, 1)
    ov2 = create_burned_hud_overlay(scene.get("caption_part2", "JUNGLE KA QANOON"), badge, idx, total_scenes, 2)

    if idx == 0:
        thumb_bg = media2 if is_vid1 else media1
        composite_photo_with_hud(thumb_bg, ov1, "cover_thumb.jpg")

    sub1 = f"sub_{idx}_1.mp4"
    sub2 = f"sub_{idx}_2.mp4"
    prepare_visual_subclip(media1, is_vid1, ov1, half_dur, 0, sub1)
    prepare_visual_subclip(media2, False, ov2, rem_dur, 1, sub2)

    list_file = f"scene_list_{idx}.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        f.write(f"file '{sub1}'\nfile '{sub2}'\n")

    scene_out = f"scene_final_{idx}.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_file,
        "-i", audio_path,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-r", "24", "-video_track_timescale", "24000",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest",
        scene_out
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return scene_out


def build_full_video(script_data):
    scenes = script_data["scenes"]
    badge = script_data.get("category_badge", "SHIKARI HE SHIKAR")
    scene_files = []

    for idx, scene in enumerate(scenes):
        print(f"🎬 Scene {idx+1}/{len(scenes)}: '{scene.get('caption_part1')} | {scene.get('caption_part2')}'")
        s_file = render_two_cut_scene(scene, idx, len(scenes), badge)
        scene_files.append(s_file)

    with open("master_concat.txt", "w", encoding="utf-8") as f:
        for sf in scene_files:
            f.write(f"file '{sf}'\n")

    raw_output = "raw_reel.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "master_concat.txt",
        "-vf", "scale=1080:1920,setsar=1,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-maxrate", "2500k", "-bufsize", "5000k",
        "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        raw_output
    ], check=True)

    print("🎵 Mixing Cinematic Background Music...")
    final_output = "final_reel.mp4"
    bgm_url = "https://actions.google.com/sounds/v1/ambiences/cyberpunk_drone.ogg"
    try:
        bgm_resp = requests.get(bgm_url, headers=HEADERS, timeout=20)
        if bgm_resp.status_code == 200:
            with open("bgm.ogg", "wb") as f:
                f.write(bgm_resp.content)
            mix_cmd = [
                "ffmpeg", "-y",
                "-i", raw_output,
                "-stream_loop", "-1", "-i", "bgm.ogg",
                "-filter_complex", "[1:a]volume=0.09[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy",
                "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                final_output
            ]
            subprocess.run(mix_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return final_output
    except Exception as e:
        print(f"BGM mixing skip: {e}")

    subprocess.run(["cp", raw_output, final_output], check=False)
    return final_output


def upload_to_youtube(video_path, script_data):
    if not (YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN):
        print("ℹ️ YouTube OAuth secrets not set; skipping YouTube auto-upload.")
        return False, "YT Secrets not set"

    print("🚀 Uploading 2-Minute Wildlife Documentary to YouTube...")
    try:
        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": YOUTUBE_CLIENT_ID,
                "client_secret": YOUTUBE_CLIENT_SECRET,
                "refresh_token": YOUTUBE_REFRESH_TOKEN,
                "grant_type": "refresh_token"
            },
            timeout=30
        )
        if token_resp.status_code != 200:
            return False, f"YT Token Error: {token_resp.text[:120]}"

        access_token = token_resp.json().get("access_token")
        file_size = os.path.getsize(video_path)

        title = script_data.get("title", "Shikari He Shikar | Wildlife Documentary")[:95]
        description = (
            f"{script_data.get('tagline', '')}\n\n"
            f"{script_data.get('description', '')}\n\n"
            f"{script_data.get('hashtags', '#ShikariHeShikar #WildlifeDocumentary')}"
        )
        tags = [t.strip("#") for t in script_data.get("hashtags", "").split() if t.startswith("#")]

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags[:15],
                "categoryId": "15"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        init_resp = requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Length": str(file_size),
                "X-Upload-Content-Type": "video/mp4"
            },
            json=body,
            timeout=30
        )
        if init_resp.status_code != 200 or "Location" not in init_resp.headers:
            return False, f"YT Init Error: {init_resp.text[:120]}"

        upload_url = init_resp.headers["Location"]
        with open(video_path, "rb") as vf:
            put_resp = requests.put(
                upload_url,
                headers={
                    "Content-Length": str(file_size),
                    "Content-Type": "video/mp4"
                },
                data=vf,
                timeout=360
            )
        if put_resp.status_code in (200, 201):
            vid_id = put_resp.json().get("id", "")
            return True, f"https://youtu.be/{vid_id}"
        return False, f"YT Upload Error: {put_resp.text[:120]}"
    except Exception as e:
        print(f"YouTube Upload Exception: {e}")
        return False, str(e)[:120]


def resolve_fb_page_credentials():
    page_id = FB_PAGE_ID
    token = FB_ACCESS_TOKEN

    m = re.search(r'(\d{8,})', page_id)
    if m:
        page_id = m.group(1)

    try:
        r = requests.get(
            "https://graph.facebook.com/v20.0/me/accounts",
            params={"access_token": token},
            timeout=15
        )
        if r.status_code == 200:
            pages = r.json().get("data", [])
            if pages:
                for p in pages:
                    if p.get("id") == page_id or p.get("name", "").lower() in page_id.lower():
                        return p.get("id"), p.get("access_token", token)
                first_page = pages[0]
                return first_page.get("id"), first_page.get("access_token", token)
    except Exception:
        pass

    return page_id, token


def upload_to_facebook(video_path, script_data):
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        return False, "FB Secrets not set"

    page_id, page_token = resolve_fb_page_credentials()
    print(f"🚀 Uploading Video to Facebook Page ID: {page_id}...")
    url = f"https://graph-video.facebook.com/v20.0/{page_id}/videos"

    title = script_data.get("title", "Shikari He Shikar - Wildlife Documentary!")
    tagline = script_data.get("tagline", "Jab jungle ka shikari khud shikar ban jata hai!")
    description = script_data.get("description", "Daily wildlife documentaries ke liye follow karein!")
    hashtags = script_data.get("hashtags", "#ShikariHeShikar #WildlifeDocumentary")

    full_post_description = (
        f"{title}\n\n"
        f"⚡ {tagline}\n\n"
        f"📌 {description}\n\n"
        f"{hashtags}"
    )

    try:
        with open(video_path, "rb") as vf:
            payload = {
                "access_token": page_token,
                "title": title,
                "description": full_post_description
            }
            files = {"source": vf}
            resp = requests.post(url, data=payload, files=files, timeout=240)
            if resp.status_code == 200 and "id" in resp.json():
                vid_id = resp.json()["id"]
                return True, f"Published on FB (ID: {vid_id})"
            err_msg = resp.json().get("error", {}).get("message", resp.text[:120])
            return False, f"FB Error: {err_msg}"
    except Exception as e:
        return False, str(e)[:120]


def send_to_telegram(video_path, script_data, yt_ok, yt_msg, fb_ok, fb_msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not set; skipping Telegram delivery.")
        return

    print("📲 Uploading 2-Minute Wildlife Video & Report to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"

    status_lines = []
    if YOUTUBE_REFRESH_TOKEN:
        status_lines.append(f"✅ YouTube: {yt_msg}" if yt_ok else f"⚠️ YouTube: {yt_msg}")
    if FB_ACCESS_TOKEN:
        status_lines.append(f"✅ Facebook: {fb_msg}" if fb_ok else f"⚠️ Facebook: {fb_msg}")
    status_block = "\n".join(status_lines) if status_lines else "✅ Video Rendered Successfully!"

    caption = (
        f"🦁 {script_data.get('title')}\n\n"
        f"⚡ {script_data.get('tagline')}\n\n"
        f"📝 {script_data.get('description')}\n\n"
        f"🏷️ {script_data.get('hashtags')}\n\n"
        f"{status_block}"
    )[:1000]

    data_payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": caption,
        "width": "1080",
        "height": "1920",
        "supports_streaming": "true"
    }

    with open(video_path, "rb") as vf:
        files_payload = {"video": ("final_reel.mp4", vf, "video/mp4")}
        thumb_handle = None
        if os.path.exists("cover_thumb.jpg"):
            thumb_handle = open("cover_thumb.jpg", "rb")
            files_payload["thumbnail"] = ("cover_thumb.jpg", thumb_handle, "image/jpeg")

        try:
            resp = requests.post(
                url,
                data=data_payload,
                files=files_payload,
                timeout=240
            )
            print("Telegram Upload Status:", resp.status_code)
        finally:
            if thumb_handle:
                thumb_handle.close()

    if resp.status_code != 200:
        print("Retrying Telegram video upload without caption...")
        with open(video_path, "rb") as vf:
            requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "supports_streaming": "true"},
                files={"video": ("final_reel.mp4", vf, "video/mp4")},
                timeout=240
            )


if __name__ == "__main__":
    data = generate_script_data()
    print("Video Title:", data.get("title"))
    final_vid = build_full_video(data)
    yt_success, yt_info = upload_to_youtube(final_vid, data)
    fb_success, fb_info = upload_to_facebook(final_vid, data)
    send_to_telegram(final_vid, data, yt_success, yt_info, fb_success, fb_info)
