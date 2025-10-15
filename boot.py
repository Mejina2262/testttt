import discord
from discord.ext import commands
from discord import app_commands
import time

class Boot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # スラッシュコマンドの実装
    @app_commands.command(name="boot", description="BOTを復帰させ、起動時間を計測・報告します。")
    async def boot_command(self, interaction: discord.Interaction):
        # 🚨 BOTがスリープから復帰する際の遅延（数十秒）に対応するための重要ステップ
        # 1. コマンド受信時の時間を記録
        start_time = time.time()

        # 2. Discordに「処理中」の即時応答（Defer）を送り、待機時間（最大15分）を延長
        # Renderの復帰待ちでコマンドがタイムアウトするのを防ぎます。
        # ephemeral=Falseで公開応答（全員に見える）として defer 
        await interaction.response.defer(ephemeral=False) 

        # --- ここでRenderのWeb Serviceがスリープから復帰し、BOTの処理が完全に始まる ---

        # 3. 復帰後、改めて起動時間を計測
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)
        
        # 4. 最終応答（Follow-up）を送信
        message = (
            "🤖 **BOTがスリープから復帰しました！**\n"
            f"⏳ 起動までに **{elapsed_time}** 秒かかりました！"
        )
        # deferしたインタラクションに対する最終的な応答を送信
        await interaction.followup.send(message)

# Cogsをセットアップするための必須関数
async def setup(bot: commands.Bot):
    await bot.add_cog(Boot(bot))