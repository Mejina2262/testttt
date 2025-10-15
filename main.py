import discord
from discord.ext import commands
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- 1. BOTクライアントとセットアップ ---
# intentsの設定
intents = discord.Intents.default()
# intents.message_content = True # 必要に応じて有効化
client = commands.Bot(command_prefix='!', intents=intents)

# --- 2. HTTPサーバーの設定（RenderのWeb Serviceとして必須） ---
# RenderはWeb Serviceとしてデプロイするため、外部からのHTTPリクエストを待ち受ける必要があります。
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ヘルスチェック用のエンドポイント
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Bot is alive!")
        else:
            self.send_response(404)
            self.end_headers()

def run_web_server():
    # Renderが指定するポート（環境変数から取得）
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('', port), HealthCheckHandler)
    server.serve_forever()

# --- 3. イベントとCogsの読み込み ---
@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    
    # Cogsを読み込む
    try:
        await client.load_extension('cogs.boot')
        print("Cogs 'boot' をロードしました。")
    except Exception as e:
        print(f"Cogsロードエラー: {e}")
        
    # スラッシュコマンドをDiscordに同期
    try:
        synced = await client.tree.sync()
        print(f"同期されたコマンド数: {len(synced)}")
    except Exception as e:
        print(f"コマンド同期エラー: {e}")
    
# --- 4. BOTの実行 ---
if __name__ == "__main__":
    # RenderのWeb Serviceとして動かすため、Webサーバーを別スレッドで起動
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # 環境変数からDiscord BOTのトークンを取得
    DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
    
    if not DISCORD_BOT_TOKEN:
        print("エラー: DISCORD_BOT_TOKEN 環境変数が設定されていません。")
    else:
        try:
            client.run(DISCORD_BOT_TOKEN)
        except discord.errors.LoginFailure:
            print("エラー: 不正なトークンが指定されました。")
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")