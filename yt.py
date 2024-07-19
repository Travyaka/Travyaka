import os
import subprocess

import youtube_dl
import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

from config import bot_token, api_id, api_hash, watermark_path

def get_youtube_video_download_link(video_url):
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
    }

    with youtube_dl.YoutubeDL(ydl_opts) as dl:
        info_dict = dl.extract_info(video_url, download=False)
        return info_dict['video_url']

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Отправь мне ссылку на видео с YouTube, и я даже смогу его просмотреть.')

def handle_video_link(update: Update, context: CallbackContext) -> None:
    video_url = update.message.text
    download_link = get_youtube_video_download_link(video_url)
    update.message.reply_text('Ссылка на скачивание видео: {download_link}')

def ypremenot_subscription(update: Update, context: CallbackContext) -> None:
    client = Client("my_account", api_id=api_id, api_hash=api_hash)

    async def send_video_to_chat(client, video_url):
        try:
            video_url = video_url.strip()
            if not video_url.startswith('http'):
                await update.message.reply_text('Некорректная ссылка на видео.')
                return

            # Скачайте видео с YouTube
            ydl_opts = {
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                'outtmpl': 'video.mp4'
            }
            with youtube_dl.YoutubeDL(ydl_opts) as dl:
                dl.download([video_url])

            # Добавьте водяной знак в начале и конце видео
            watermark = TextClip(txt='YPremiumEnot', fontsize=50, color='white')
            watermark = watermark.set_position((50, 50)).set_duration(5)

            video = VideoFileClip('video.mp4')
            video_with_watermark = CompositeVideoClip([video, watermark.set_pos((video.w - watermark.w, video.h - watermark.h))])
            video_with_watermark = video_with_watermark.set_duration(video.duration)

            # Сохраните видео с водяным знаком
            video_with_watermark.write_videofile('video_with_watermark.mp4', fps=video.fps, codec='libx264')

            # Отправьте видео с водяным знаком
            await client.send_video(chat_id=update.message.chat_id, video='video_with_watermark.mp4')

            # Удалите временные файлы
            os.remove('video.mp4')
            os.remove('video_with_watermark.mp4')
        except FloodWait as e:
            await update.message.reply_text(f'Подождите {e.x} секунд перед повторной отправкой сообщения.')
        except Exception as e:
            await update.message.reply_text(f'Ошибка: {str(e)}')

    client.start()
    client.loop.run_until_complete(send_video_to_chat(client, video_url))
    client.stop()

def main() -> None:
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    video_link_handler = MessageHandler(Filters.regex(r'https?://(?:www\.)?youtube\.com'), handle_video_link)
    ypremenot_subscription_handler = CommandHandler('ypremenot', ypremenot_subscription)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(video_link_handler)
    dispatcher.add_handler(ypremenot_subscription_handler)
    
    updater.start_polling()
updater.idle()

if __name__ == '__main__':
main()

