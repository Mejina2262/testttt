import discord
from discord.ext import commands
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import asyncio
import sys

# --- 1. BOTクライアントとセットアップ ---
# intentsの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージコンテンツを取得（必要に応じて）
client = commands.Bot(command_prefix='!', intents=intents)

# --- 2. HTTPサーバーの設定（RenderのWeb Serviceとして必須） ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # ヘルスチェック用のエンドポイント
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # BOTのステータス情報を返す
            status = "Online" if client.is_ready() else "Starting..."
            response = f"""
            <html>
            <head><title>Discord Bot Status</title></head>
            <body>
                <h1>Discord Bot is {status}!</h1>
                <p>Bot User: {client.user if client.user else 'Not logged in'}</p>
                <p>Guilds: {len(client.guilds) if client.is_ready() else 'N/A'}</p>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
        elif self.path == '/health':
            # シンプルなヘルスチェック
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # アクセスログを抑制（オプション）
        pass

def run_web_server():
    """Webサーバーを起動"""
    try:
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"🌐 Webサーバーがポート {port} で起動しました")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Webサーバー起動エラー: {e}")

# --- 3. イベントとCogsの読み込み ---
@client.event
async def on_ready():
    """BOT起動時の処理"""
    print('=' * 50)
    print(f'✅ ログイン成功: {client.user} (ID: {client.user.id})')
    print(f'📊 接続サーバー数: {len(client.guilds)}')
    print('=' * 50)
    
    # Cogsを読み込む
    cogs_list = ['cogs.boot', 'cogs.crypto_prices']
    loaded_cogs = []
    failed_cogs = []
    
    for cog in cogs_list:
        try:
            await client.load_extension(cog)
            loaded_cogs.append(cog)
            print(f"✅ Cog '{cog}' をロードしました")
        except Exception as e:
            failed_cogs.append(cog)
            print(f"❌ Cog '{cog}' のロードエラー: {e}")
    
    print('-' * 50)
    
    # スラッシュコマンドをDiscordに同期
    try:
        print("🔄 コマンドを同期中...")
        synced = await client.tree.sync()
        print(f"✅ {len(synced)} 個のコマンドを同期しました:")
        for command in synced:
            print(f"   • /{command.name}: {command.description}")
    except Exception as e:
        print(f"❌ コマンド同期エラー: {e}")
    
    print('-' * 50)
    print(f"📦 ロード成功: {len(loaded_cogs)}/{len(cogs_list)} Cogs")
    if failed_cogs:
        print(f"⚠️  ロード失敗: {', '.join(failed_cogs)}")
    print('=' * 50)
    print("🚀 BOTの準備が完了しました！")
    print('=' * 50)

@client.event
async def on_guild_join(guild):
    """サーバーに参加した時"""
    print(f"📥 新しいサーバーに参加: {guild.name} (ID: {guild.id})")

@client.event
async def on_guild_remove(guild):
    """サーバーから退出した時"""
    print(f"📤 サーバーから退出: {guild.name} (ID: {guild.id})")

@client.event
async def on_command_error(ctx, error):
    """コマンドエラーハンドリング"""
    if isinstance(error, commands.CommandNotFound):
        return  # コマンドが見つからない場合は無視
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ このコマンドを実行する権限がありません。")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ BOTに必要な権限がありません。")
    else:
        print(f"❌ コマンドエラー: {error}")

@client.event
async def on_error(event, *args, **kwargs):
    """一般的なエラーハンドリング"""
    print(f"❌ エラーが発生しました (イベント: {event})")
    import traceback
    traceback.print_exc()

# --- 4. BOTの実行 ---
def main():
    """メイン処理"""
    print("🤖 Discord BOTを起動中...")
    
    # 環境変数からトークンを取得
    DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
    
    if not DISCORD_BOT_TOKEN:
        print("=" * 50)
        print("❌ エラー: DISCORD_BOT_TOKEN 環境変数が設定されていません")
        print("=" * 50)
        print("\n設定方法:")
        print("1. Renderの環境変数設定で DISCORD_BOT_TOKEN を追加")
        print("2. Discord Developer Portalからトークンを取得して設定")
        print("=" * 50)
        sys.exit(1)
    
    # Webサーバーを別スレッドで起動
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    
    # 起動前に少し待機（Renderの安定化のため）
    import time
    time.sleep(2)
    
    # BOTを起動
    try:
        print("🔌 Discordに接続中...")
        client.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("=" * 50)
        print("❌ エラー: 不正なトークンが指定されました")
        print("=" * 50)
        print("Discord Developer Portalでトークンを確認してください")
        sys.exit(1)
    except discord.errors.PrivilegedIntentsRequired:
        print("=" * 50)
        print("❌ エラー: 特権インテントが有効になっていません")
        print("=" * 50)
        print("Discord Developer Portalで以下を有効化してください:")
        print("- MESSAGE CONTENT INTENT")
        print("- SERVER MEMBERS INTENT (必要に応じて)")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  BOTを手動で停止しました")
        sys.exit(0)
    except Exception as e:
        print("=" * 50)
        print(f"❌ 予期せぬエラーが発生しました: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
