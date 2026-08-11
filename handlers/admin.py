import asyncio
import os
from aiogram import Router, F, html, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import config
from utils.admin_manager import is_admin, is_super_admin, add_admin, remove_admin, get_admins
from utils.user_manager import get_all_users
from utils.channel_manager import add_channel, remove_channel, load_channels
from utils.stats import format_stats_text, generate_activity_chart
from utils.backup import create_backup

router = Router()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast_info"),
        ],
        [
            InlineKeyboardButton(text="👥 Adminlar ro'yxati", callback_data="admin_list"),
            InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add_info"),
        ],
        [
            InlineKeyboardButton(text="🗑 Admin o'chirish", callback_data="admin_remove_info"),
        ],
        [
            InlineKeyboardButton(text="📡 Kanal qo'shish", callback_data="admin_add_channel_info"),
            InlineKeyboardButton(text="🗑 Kanal o'chirish", callback_data="admin_remove_channel_info"),
        ],
        [
            InlineKeyboardButton(text="💾 Zaxira nusxa (Backup)", callback_data="admin_backup"),
        ],
    ])


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_menu")]
    ])


async def check_super_admin(message: Message) -> bool:
    if not is_super_admin(message.from_user.id):
        await message.answer("❌ Bu buyruqni faqat Super Admin ishlata oladi.")
        return False
    return True


async def check_admin(message: Message) -> bool:
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruqni faqat bot adminlari ishlata oladi.")
        return False
    return True


async def send_extended_stats(target: Message):
    stats_text = format_stats_text()
    chart_path = os.path.join(config.TEMP_DIR, "activity_chart.png")
    if generate_activity_chart(chart_path) and os.path.exists(chart_path):
        await target.answer_photo(
            FSInputFile(chart_path),
            caption=stats_text,
        )
        try:
            os.remove(chart_path)
        except OSError:
            pass
    else:
        await target.answer(stats_text)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not await check_admin(message):
        return
    await message.answer(
        f"⚙️ {html.bold('Admin Panel')}\nKerakli bo'limni tanlang:",
        reply_markup=get_admin_keyboard(),
    )


@router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    await callback.message.edit_text(
        f"⚙️ {html.bold('Admin Panel')}\nKerakli bo'limni tanlang:",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    stats_text = format_stats_text()
    total_admins = len(get_admins())
    stats_text += f"\n\n👑 {html.bold('Super Admin:')} 1\n🛠 {html.bold('Adminlar:')} {total_admins}"
    await callback.message.edit_text(stats_text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast_info")
async def cb_admin_broadcast_info(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    text = (
        f"📢 {html.bold('Xabar yuborish (Broadcast):')}\n\n"
        f"1. {html.code(html.quote('/broadcast <xabar matni>'))}\n"
        f"2. Yoki rasm/video faylga reply berib {html.code('/broadcast')} yuboring."
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_list")
async def cb_admin_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    admins = get_admins()
    response_text = f"👑 {html.bold('Super Admin:')} {config.SUPER_ADMIN_ID}\n\n"
    response_text += f"👥 {html.bold('Oddiy Adminlar:')}\n"
    response_text += "\n".join(f"{i}. {a}" for i, a in enumerate(admins, 1)) if admins else "• Hozircha yo'q."
    await callback.message.edit_text(response_text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_add_info")
async def cb_admin_add_info(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    text = (
        f"➕ {html.bold('Admin qo`shish:')}\n\n"
        f"Super Admin: {html.code('/addadmin <user_id>')}\n"
        f"Masalan: {html.code('/addadmin 123456789')}"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_remove_info")
async def cb_admin_remove_info(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    text = (
        f"🗑 {html.bold('Admin o`chirish:')}\n\n"
        f"Super Admin: {html.code('/removeadmin <user_id>')}"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_add_channel_info")
async def cb_admin_add_channel_info(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    text = (
        f"📡 {html.bold('Majburiy kanal qo`shish:')}\n\n"
        f"{html.code('/addchannel @kanal_username')}\n"
        f"yoki {html.code('/addchannel -1001234567890')}\n\n"
        f"⚠️ Bot ushbu kanalda admin bo'lishi kerak!"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_remove_channel_info")
async def cb_admin_remove_channel_info(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    channels = load_channels()
    buttons = []
    if channels:
        text = f"🗑 {html.bold('Kanalni o`chirish uchun tugmani bosing')}\nyoki buyruq yuboring: {html.code('/removechannel @kanal')}\n"
        for ch in channels:
            buttons.append([InlineKeyboardButton(
                text=f"❌ {ch['title']} ({ch['id']})",
                callback_data=f"admin_del_ch:{ch['id']}",
            )])
    else:
        text = "📭 Hozircha majburiy kanallar yo'q."
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_ch:"))
async def cb_admin_del_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    channel_id = callback.data.split(":", 1)[1]
    if remove_channel(channel_id):
        await callback.answer(f"✅ {channel_id} o'chirildi!", show_alert=True)
    else:
        await callback.answer("❌ Kanal topilmadi.", show_alert=True)
    await cb_admin_remove_channel_info(callback)



@router.message(Command("addadmin"))
async def cmd_addadmin(message: Message):
    if not await check_super_admin(message):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer(f"⚠️ Foydalanish: {html.code('/addadmin <user_id>')}")
        return
    try:
        new_admin_id = int(args[1])
    except ValueError:
        await message.answer("❌ Admin ID faqat raqamlardan iborat bo'lishi kerak.")
        return
    if add_admin(new_admin_id):
        await message.answer(f"✅ {new_admin_id} admin etib tayinlandi.")
    else:
        await message.answer(f"❌ {new_admin_id} allaqachon admin.")


@router.message(Command("removeadmin"))
async def cmd_removeadmin(message: Message):
    if not await check_super_admin(message):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer(f"⚠️ Foydalanish: {html.code('/removeadmin <user_id>')}")
        return
    try:
        admin_id = int(args[1])
    except ValueError:
        await message.answer("❌ Admin ID faqat raqamlardan iborat bo'lishi kerak.")
        return
    if remove_admin(admin_id):
        await message.answer(f"✅ {admin_id} adminlar ro'yxatidan o'chirildi.")
    else:
        await message.answer(f"❌ {admin_id} topilmadi.")


@router.message(Command("addchannel"))
async def cmd_addchannel(message: Message):
    if not await check_admin(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(f"⚠️ Foydalanish: {html.code('/addchannel @username yoki -100...')}")
        return
    channel_id = args[1].strip()
    title = channel_id.lstrip("@")
    if add_channel(channel_id, title):
        await message.answer(f"✅ Kanal {html.bold(channel_id)} majburiy ro'yxatga qo'shildi.")
    else:
        await message.answer(f"❌ Kanal {channel_id} allaqachon ro'yxatda.")


@router.message(Command("removechannel"))
async def cmd_removechannel(message: Message):
    if not await check_admin(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(f"⚠️ Foydalanish: {html.code('/removechannel @username')}")
        return
    channel_id = args[1].strip()
    if remove_channel(channel_id):
        await message.answer(f"✅ Kanal {channel_id} ro'yxatdan o'chirildi.")
    else:
        await message.answer(f"❌ Kanal {channel_id} topilmadi.")


@router.message(Command("channels"))
async def cmd_channels(message: Message):
    if not await check_admin(message):
        return
    channels = load_channels()
    if not channels:
        await message.answer("📭 Majburiy kanallar ro'yxati bo'sh.")
        return
    text = f"📡 {html.bold('Majburiy kanallar:')}\n\n"
    for i, ch in enumerate(channels, 1):
        text += f"{i}. {ch['title']} — {ch['id']}\n"
    await message.answer(text)


@router.message(Command("admins"))
async def cmd_admins(message: Message):
    if not await check_admin(message):
        return
    admins = get_admins()
    response_text = f"👑 {html.bold('Super Admin:')} {config.SUPER_ADMIN_ID}\n\n"
    response_text += f"👥 {html.bold('Oddiy Adminlar:')}\n"
    response_text += "\n".join(f"{i}. {a}" for i, a in enumerate(admins, 1)) if admins else "• Hozircha yo'q."
    await message.answer(response_text)


@router.callback_query(F.data == "admin_backup")
async def cb_admin_backup(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
    await callback.answer("⏳ Zaxira olinmoqda...")
    try:
        zip_path = create_backup()
        await callback.message.answer_document(
            FSInputFile(zip_path),
            caption=f"💾 Zaxira nusxa: {os.path.basename(zip_path)}",
            reply_markup=get_back_keyboard(),
        )
    except Exception as e:
        await callback.message.answer(f"❌ Zaxira olishda xatolik: {str(e)}")
    await callback.answer()


@router.message(Command("backup"))
async def cmd_backup(message: Message):
    if not await check_admin(message):
        return
    status = await message.answer("⏳ Zaxira olinmoqda...")
    try:
        zip_path = create_backup()
        await status.delete()
        await message.answer_document(
            FSInputFile(zip_path),
            caption=f"💾 Zaxira nusxa: {os.path.basename(zip_path)}",
        )
    except Exception as e:
        await status.edit_text(f"❌ Zaxira olishda xatolik: {str(e)}")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not await check_admin(message):
        return
    await send_extended_stats(message)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot):
    if not await check_admin(message):
        return
    reply = message.reply_to_message
    text_to_send = None
    if not reply:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer(
                f"⚠️ Foydalanish:\n"
                f"1. {html.code('/broadcast <xabar>')}\n"
                f"2. Reply + {html.code('/broadcast')}"
            )
            return
        text_to_send = args[1]

    users = get_all_users()
    if not users:
        await message.answer("⚠️ Botda foydalanuvchilar mavjud emas.")
        return

    status_msg = await message.answer(f"📤 Xabar yuborish boshlandi... ({len(users)} ta)")
    success_count = fail_count = 0
    for user_id in users:
        try:
            if reply:
                await reply.copy_to(chat_id=user_id)
            else:
                await bot.send_message(chat_id=user_id, text=text_to_send)
            success_count += 1
        except Exception:
            fail_count += 1
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"📢 {html.bold('Broadcast yakunlandi!')}\n\n"
        f"✅ Muvaffaqiyatli: {success_count}\n"
        f"❌ Yetkazilmadi: {fail_count}"
    )
