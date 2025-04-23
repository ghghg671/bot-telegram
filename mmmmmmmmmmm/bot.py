import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler
from telegram.ext import Filters
from dotenv import load_dotenv
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Game Data
CLASSES = {
    "warrior": {"health": 120, "attack": 15, "defense": 10, "description": "قوي ومتين"},
    "mage": {"health": 80, "attack": 20, "defense": 5, "description": "قوى سحرية لكن هش"},
    "rogue": {"health": 90, "attack": 18, "defense": 7, "description": "سريع وفتاك"}
}

ENEMIES = [
    {"name": "غوبلين", "health": 50, "attack": 8, "defense": 3, "reward": 10},
    {"name": "أورك", "health": 80, "attack": 12, "defense": 5, "reward": 20},
    {"name": "تنين", "health": 150, "attack": 20, "defense": 10, "reward": 50}
]

ITEMS = {
    "health_potion": {"name": "جرعة صحية", "effect": 30, "price": 20},
    "sword": {"name": "سيف فولاذي", "attack": 5, "price": 50},
    "shield": {"name": "درع حديدي", "defense": 5, "price": 40}
}

QUESTS = [
    {"id": 1, "name": "مطاردة الغوبلين", "description": "هزم 3 غوبلين", "target": "غوبلين", "count": 3, "reward": 50},
    {"id": 2, "name": "قاتل الأورك", "description": "هزم 2 أورك", "target": "أورك", "count": 2, "reward": 80},
    {"id": 3, "name": "تحدي التنين", "description": "هزم التنين", "target": "تنين", "count": 1, "reward": 150}
]

# Player Data
players = {}
battles = {}

def main_menu(update: Update, context: CallbackContext, message: str = "القائمة الرئيسية:") -> None:
    keyboard = [
        [KeyboardButton("🌟 إنشاء شخصية")],
        [KeyboardButton("⚔️ استكشاف"), KeyboardButton("🎒 المعدات")],
        [KeyboardButton("🏪 المتجر"), KeyboardButton("📜 المهام")],
        [KeyboardButton("📊 الإحصائيات"), KeyboardButton("ℹ️ المساعدة")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.message:
        update.message.reply_text(message, reply_markup=reply_markup)
    else:
        update.callback_query.message.reply_text(message, reply_markup=reply_markup)

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if str(user.id) in players:
        main_menu(update, context, f"مرحبًا بعودتك، {players[str(user.id)]['name']}!")
    else:
        main_menu(update, context, "مرحبًا ببوت RPG! اختر 'إنشاء شخصية' لتبدأ.")

def handle_menu_selection(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    user = update.effective_user
    
    if text == "🌟 إنشاء شخصية":
        if str(user.id) in players:
            update.message.reply_text("لديك شخصية بالفعل!")
            return
            
        keyboard = [
            [InlineKeyboardButton("محارب", callback_data='create_warrior')],
            [InlineKeyboardButton("ساحر", callback_data='create_mage')],
            [InlineKeyboardButton("لص", callback_data='create_rogue')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر فئة شخصيتك:", reply_markup=reply_markup)
    
    elif text == "⚔️ استكشاف":
        explore(update, context)
    
    elif text == "🎒 المعدات":
        inventory(update, context)
    
    elif text == "🏪 المتجر":
        shop(update, context)
    
    elif text == "📜 المهام":
        quests(update, context)
    
    elif text == "📊 الإحصائيات":
        stats(update, context)
    
    elif text == "ℹ️ المساعدة":
        help_command(update, context)

def create_character(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    user = query.from_user
    class_type = query.data.split('_')[1]
    
    players[str(user.id)] = {
        "name": user.first_name,
        "class": class_type,
        "level": 1,
        "xp": 0,
        "gold": 50,
        "health": CLASSES[class_type]["health"],
        "max_health": CLASSES[class_type]["health"],
        "attack": CLASSES[class_type]["attack"],
        "defense": CLASSES[class_type]["defense"],
        "inventory": [],
        "quests": [],
        "kills": {"غوبلين": 0, "أورك": 0, "تنين": 0}
    }
    
    query.edit_message_text(
        f"تم إنشاء شخصيتك:\n"
        f"الاسم: {user.first_name}\n"
        f"الفئة: {class_type}\n"
        f"الصحة: {CLASSES[class_type]['health']}\n"
        f"الهجوم: {CLASSES[class_type]['attack']}\n"
        f"الدفاع: {CLASSES[class_type]['defense']}\n\n"
        "يمكنك الآن البدء بالمغامرة!"
    )
    main_menu(update, context)

def explore(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    player = players.get(str(user.id))
    
    if not player:
        update.message.reply_text("يجب إنشاء شخصية أولاً!")
        return
    
    if player["health"] <= 0:
        update.message.reply_text("صحتك منخفضة! استخدم جرعة صحية أو انتظر للتعافي.")
        return
    
    enemy = random.choice(ENEMIES)
    battles[str(user.id)] = {
        "enemy": enemy,
        "enemy_health": enemy["health"]
    }
    
    keyboard = [
        [InlineKeyboardButton("⚔️ هجوم", callback_data='battle_attack')],
        [InlineKeyboardButton("🧪 استخدام عنصر", callback_data='battle_item')],
        [InlineKeyboardButton("🏃‍♂️ هروب", callback_data='battle_flee')],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        update.callback_query.edit_message_text(
            f"واجهت {enemy['name']}!\n"
            f"صحة العدو: {enemy['health']}\n"
            f"صحتك: {player['health']}/{player['max_health']}\n\n"
            "ماذا ستفعل؟",
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            f"واجهت {enemy['name']}!\n"
            f"صحة العدو: {enemy['health']}\n"
            f"صحتك: {player['health']}/{player['max_health']}\n\n"
            "ماذا ستفعل؟",
            reply_markup=reply_markup
        )

def battle_action(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    user = query.from_user
    player = players.get(str(user.id))
    battle = battles.get(str(user.id))
    
    if not player or not battle:
        query.edit_message_text("المعركة غير موجودة. ابدأ معركة جديدة باستخدام /استكشف")
        return
    
    action = query.data.split('_')[1]
    enemy = battle["enemy"]
    
    if action == "attack":
        player_damage = max(1, player["attack"] - random.randint(0, enemy["defense"]))
        battle["enemy_health"] -= player_damage
        
        if battle["enemy_health"] > 0:
            enemy_damage = max(1, enemy["attack"] - random.randint(0, player["defense"]))
            player["health"] -= enemy_damage
            damage_text = f"لقد ضربك {enemy['name']} بـ {enemy_damage} نقطة ضرر!\n"
        else:
            damage_text = ""
            
        if battle["enemy_health"] <= 0:
            reward = enemy["reward"]
            xp_gain = enemy["reward"] * 2
            player["gold"] += reward
            player["xp"] += xp_gain
            player["kills"][enemy["name"]] += 1
            
            xp_needed = player["level"] * 100
            if player["xp"] >= xp_needed:
                player["level"] += 1
                player["attack"] += 2
                player["defense"] += 1
                player["max_health"] += 10
                player["health"] = player["max_health"]
                level_text = f"\n\nلقد ارتقت مستوى! أنت الآن مستوى {player['level']}!"
            else:
                level_text = ""
            
            quest_updates = check_quests(user.id, enemy["name"])
            
            query.edit_message_text(
                f"لقد هزمت {enemy['name']}!\n"
                f"لقد كسبت {xp_gain} نقطة خبرة و {reward} ذهب.{level_text}\n\n"
                f"{quest_updates}\n"
                f"صحتك الحالية: {player['health']}/{player['max_health']}\n"
                "اضغط /استكشف للعثور على عدو آخر."
            )
            del battles[str(user.id)]
            return
    
    elif action == "item":
        if not player["inventory"]:
            query.edit_message_text("ليس لديك أي عناصر لاستخدامها!")
            return
        
        items_text = "\n".join([f"{i+1}. {ITEMS[item]['name']}" for i, item in enumerate(player["inventory"])])
        query.edit_message_text(
            f"اختر عنصرًا لاستخدامه:\n{items_text}\n\n"
            "رد برقم العنصر أو 'إلغاء' للعودة."
        )
        return
    
    elif action == "flee":
        if random.random() < 0.5:
            query.edit_message_text(
                f"لقد هربت بنجاح من {enemy['name']}!\n"
                "اضغط /استكشف للعثور على عدو آخر."
            )
            del battles[str(user.id)]
            return
        else:
            enemy_damage = max(1, enemy["attack"] - random.randint(0, player["defense"]))
            player["health"] -= enemy_damage
            damage_text = f"فشلت في الهروب!\nلقد ضربك {enemy['name']} بـ {enemy_damage} نقطة ضرر!\n"
    
    keyboard = [
        [InlineKeyboardButton("⚔️ هجوم", callback_data='battle_attack')],
        [InlineKeyboardButton("🧪 استخدام عنصر", callback_data='battle_item')],
        [InlineKeyboardButton("🏃‍♂️ هروب", callback_data='battle_flee')],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        f"لقد ضربت {enemy['name']} بـ {player_damage} نقطة ضرر!\n"
        f"{damage_text}\n"
        f"صحة العدو: {max(0, battle['enemy_health'])}/{enemy['health']}\n"
        f"صحتك: {player['health']}/{player['max_health']}\n\n"
        "ماذا ستفعل؟",
        reply_markup=reply_markup
    )
    
    if player["health"] <= 0:
        query.edit_message_text(
            "لقد هزمت!\n"
            "لقد خسرت 20 ذهبًا وكل التقدم في المهام الحالية.\n"
            "ستستعيد نصف صحتك بعد هذه المعركة."
        )
        player["gold"] = max(0, player["gold"] - 20)
        player["health"] = player["max_health"] // 2
        player["quests"] = []
        del battles[str(user.id)]

def use_item(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    player = players.get(str(user.id))
    battle = battles.get(str(user.id))
    
    if not player or not battle:
        update.message.reply_text("لا توجد معركة نشطة. اضغط /استكشف للعثور على أعداء.")
        return
    
    try:
        if update.message.text.lower() == "إلغاء":
            update.message.reply_text("تم إلغاء استخدام العنصر.")
            return explore(update, context)
        
        item_index = int(update.message.text) - 1
        if item_index < 0 or item_index >= len(player["inventory"]):
            update.message.reply_text("رقم عنصر غير صالح. حاول مرة أخرى أو اكتب 'إلغاء'.")
            return
        
        item_id = player["inventory"][item_index]
        item = ITEMS[item_id]
        
        if item_id == "health_potion":
            heal_amount = min(item["effect"], player["max_health"] - player["health"])
            player["health"] += heal_amount
            player["inventory"].remove(item_id)
            update.message.reply_text(
                f"لقد استخدمت {item['name']} واستعديت {heal_amount} نقطة صحية!\n"
                f"صحتك الحالية: {player['health']}/{player['max_health']}"
            )
        else:
            update.message.reply_text("لا يمكنك استخدام هذا العنصر في المعركة!")
            return
        
        explore(update, context)
        
    except ValueError:
        update.message.reply_text("الرجاء إدخال رقم صالح أو 'إلغاء'.")

def inventory(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    player = players.get(str(user.id))
    
    if not player:
        update.message.reply_text("الرجاء إنشاء شخصية أولاً باستخدام /ابدأ")
        return
    
    if not player["inventory"]:
        update.message.reply_text("المخزن فارغ. زر /المتجر لشراء العناصر.")
        return
    
    items_text = "\n".join([ITEMS[item]["name"] for item in player["inventory"]])
    update.message.reply_text(
        f"المخزن الخاص بك:\n{items_text}\n\n"
        f"الذهب: {player['gold']}"
    )

def shop(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    player = players.get(str(user.id))
    
    if not player:
        update.message.reply_text("الرجاء إنشاء شخصية أولاً باستخدام /ابدأ")
        return
    
    keyboard = []
    for item_id, item in ITEMS.items():
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} - {item['price']} ذهب",
            callback_data=f'buy_{item_id}'
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "مرحبًا بكم في المتجر! ماذا تريد أن تشتري؟\n"
        f"ذهبك: {player['gold']}",
        reply_markup=reply_markup
    )

def buy_item(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    user = query.from_user
    player = players.get(str(user.id))
    
    if not player:
        query.edit_message_text("الشخصية غير موجودة. اكتب /ابدأ لإنشاء واحدة.")
        return
    
    item_id = query.data.split('_')[1]
    item = ITEMS[item_id]
    
    if player["gold"] < item["price"]:
        query.edit_message_text(f"لا تملك ذهبًا كافيًا! تحتاج {item['price']} ولكن لديك فقط {player['gold']}.")
        return
    
    player["gold"] -= item["price"]
    player["inventory"].append(item_id)
    
    query.edit_message_text(f"لقد اشتريت {item['name']} بـ {item['price']} ذهب!")

def quests(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    player = players.get(str(user.id))
    
    if not player:
        update.message.reply_text("الرجاء إنشاء شخصية أولاً باستخدام /ابدأ")
        return
    
    available_quests = [q for q in QUESTS if q["id"] not in [q["id"] for q in player["quests"]]]
    active_quests = player["quests"]
    
    available_text = "\n".join([
        f"{q['name']}: {q['description']} (مكافأة: {q['reward']} ذهب)"
        for q in available_quests
    ]) if available_quests else "لا توجد مهام متاحة"
    
    active_text = "\n".join([
        f"{q['name']}: {player['kills'].get(q['target'], 0)}/{q['count']} {q['target']} تم هزيمتهم"
        for q in active_quests
    ]) if active_quests else "لا توجد مهام نشطة"
    
    keyboard = [
        [InlineKeyboardButton(f"قبول: {q['name']}", callback_data=f'accept_{q["id"]}')]
        for q in available_quests
    ]
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    update.message.reply_text(
        f"المهام المتاحة:\n{available_text}\n\n"
        f"المهام النشطة:\n{active_text}",
        reply_markup=reply_markup
    )

def accept_quest(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    user = query.from_user
    player = players.get(str(user.id))
    
    if not player:
        query.edit_message_text("الشخصية غير موجودة. اكتب /ابدأ لإنشاء واحدة.")
        return
    
    quest_id = int(query.data.split('_')[1])
    quest = next((q for q in QUESTS if q["id"] == quest_id), None)
    
    if not quest:
        query.edit_message_text("المهمة غير موجودة!")
        return
    
    if quest in player["quests"]:
        query.edit_message_text("لديك هذه المهمة بالفعل!")
        return
    
    player["quests"].append(quest)
    query.edit_message_text(f"تم قبول المهمة: {quest['name']}!")

def check_quests(user_id: int, enemy_name: str) -> str:
    player = players.get(str(user_id))
    if not player or not player["quests"]:
        return ""
    
    completed = []
    for quest in player["quests"][:]:
        if quest["target"] == enemy_name:
            if player["kills"].get(enemy_name, 0) >= quest["count"]:
                player["gold"] += quest["reward"]
                player["xp"] += quest["reward"] * 2
                player["quests"].remove(quest)
                completed.append(f"تم الانتهاء من: {quest['name']}!")
    
    return "\n".join(completed) if completed else ""

def stats(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    player = players.get(str(user.id))
    
    if not player:
        update.message.reply_text("الرجاء إنشاء شخصية أولاً باستخدام /ابدأ")
        return
    
    kills_text = "\n".join([f"{k}: {v}" for k, v in player["kills"].items()])
    
    update.message.reply_text(
        f"الشخصية: {player['name']}\n"
        f"الفئة: {player['class']}\n"
        f"المستوى: {player['level']}\n"
        f"الخبرة: {player['xp']}/{player['level'] * 100}\n"
        f"الذهب: {player['gold']}\n"
        f"الصحة: {player['health']}/{player['max_health']}\n"
        f"الهجوم: {player['attack']}\n"
        f"الدفاع: {player['defense']}\n\n"
        f"عمليات القتل:\n{kills_text}"
    )

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "أوامر بوت RPG:\n"
        "/ابدأ - إنشاء أو عرض شخصيتك\n"
        "/استكشف - العثور على أعداء للقتال\n"
        "/المخزن - عرض العناصر الخاصة بك\n"
        "/المتجر - شراء العناصر\n"
        "/المهام - عرض المهام المتاحة\n"
        "/الإحصائيات - عرض إحصائيات شخصيتك\n"
        "/المساعدة - عرض هذه الرسالة"
    )

def main() -> None:
    """تشغيل البوت"""
    load_dotenv('token.env')  # تحميل الملف
    TOKEN = os.getenv('BOT_TOKEN')  # قراءة التوكن
    
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # تسجيل ال handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_menu_selection))
    dispatcher.add_handler(CallbackQueryHandler(create_character, pattern='^create_'))
    dispatcher.add_handler(CallbackQueryHandler(battle_action, pattern='^battle_'))
    dispatcher.add_handler(CallbackQueryHandler(buy_item, pattern='^buy_'))
    dispatcher.add_handler(CallbackQueryHandler(accept_quest, pattern='^accept_'))
    dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, use_item))

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()