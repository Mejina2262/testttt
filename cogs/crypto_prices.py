import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict

class CryptoCache:
    """APIレスポンスをキャッシュするクラス"""
    def __init__(self, cache_duration=60):
        self.cache: Dict[str, tuple] = {}
        self.cache_duration = cache_duration
    
    def get(self, key: str):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return data
        return None
    
    def set(self, key: str, data):
        self.cache[key] = (data, datetime.now())

class CryptoView(discord.ui.View):
    def __init__(self, cache: CryptoCache):
        super().__init__(timeout=180)
        self.cache = cache
        
    @discord.ui.select(
        placeholder="暗号通貨を選択してください",
        options=[
            discord.SelectOption(label="Bitcoin (BTC)", value="bitcoin", emoji="🪙"),
            discord.SelectOption(label="Ethereum (ETH)", value="ethereum", emoji="💎"),
            discord.SelectOption(label="Ripple (XRP)", value="ripple", emoji="💧"),
            discord.SelectOption(label="Cardano (ADA)", value="cardano", emoji="🎴"),
            discord.SelectOption(label="Solana (SOL)", value="solana", emoji="☀️"),
            discord.SelectOption(label="Polkadot (DOT)", value="polkadot", emoji="🔴"),
            discord.SelectOption(label="Dogecoin (DOGE)", value="dogecoin", emoji="🐕"),
            discord.SelectOption(label="Avalanche (AVAX)", value="avalanche-2", emoji="🔺"),
            discord.SelectOption(label="Chainlink (LINK)", value="chainlink", emoji="🔗"),
            discord.SelectOption(label="Polygon (MATIC)", value="matic-network", emoji="🟣"),
            discord.SelectOption(label="Litecoin (LTC)", value="litecoin", emoji="⚡"),
            discord.SelectOption(label="Uniswap (UNI)", value="uniswap", emoji="🦄"),
            discord.SelectOption(label="Binance Coin (BNB)", value="binancecoin", emoji="💰"),
            discord.SelectOption(label="Tron (TRX)", value="tron", emoji="⚙️"),
            discord.SelectOption(label="Stellar (XLM)", value="stellar", emoji="⭐"),
            discord.SelectOption(label="Monero (XMR)", value="monero", emoji="🔒"),
            discord.SelectOption(label="Cosmos (ATOM)", value="cosmos", emoji="🌌"),
            discord.SelectOption(label="Algorand (ALGO)", value="algorand", emoji="🔷"),
            discord.SelectOption(label="VeChain (VET)", value="vechain", emoji="✅"),
            discord.SelectOption(label="Filecoin (FIL)", value="filecoin", emoji="📁"),
            discord.SelectOption(label="Tezos (XTZ)", value="tezos", emoji="🔵"),
            discord.SelectOption(label="Shiba Inu (SHIB)", value="shiba-inu", emoji="🐶"),
            discord.SelectOption(label="Bitcoin Cash (BCH)", value="bitcoin-cash", emoji="💵"),
            discord.SelectOption(label="Aptos (APT)", value="aptos", emoji="🅰️"),
            discord.SelectOption(label="Near Protocol (NEAR)", value="near", emoji="🔷"),
        ]
    )
    async def select_crypto(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            return
        
        crypto_id = select.values[0]
        
        # キャッシュチェック
        cached_data = self.cache.get(crypto_id)
        if cached_data:
            await self.send_crypto_embed(interaction, crypto_id, cached_data, select, from_cache=True)
            return
        
        # API呼び出し（リトライ付き）
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd,jpy,btc&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true"
                    
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if crypto_id in data:
                                # キャッシュに保存
                                self.cache.set(crypto_id, data[crypto_id])
                                await self.send_crypto_embed(interaction, crypto_id, data[crypto_id], select)
                                return
                            else:
                                await interaction.followup.send("❌ データが見つかりませんでした。", ephemeral=True)
                                return
                        
                        elif response.status == 429:
                            # レート制限
                            if attempt < 2:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            else:
                                await interaction.followup.send(
                                    "⚠️ APIのレート制限に達しました。しばらく待ってから再度お試しください。",
                                    ephemeral=True
                                )
                                return
                        
                        else:
                            # その他のHTTPエラー
                            error_text = await response.text()
                            print(f"API Error {response.status}: {error_text}")
                            
                            if attempt < 2:
                                await asyncio.sleep(1)
                                continue
                            else:
                                await interaction.followup.send(
                                    f"❌ API エラー (ステータス: {response.status})\nしばらく待ってから再度お試しください。",
                                    ephemeral=True
                                )
                                return
            
            except asyncio.TimeoutError:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    await interaction.followup.send("❌ API接続がタイムアウトしました。", ephemeral=True)
                    return
            
            except Exception as e:
                print(f"予期せぬエラー (試行 {attempt + 1}/3): {str(e)}")
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
                    return
    
    async def send_crypto_embed(self, interaction, crypto_id, crypto_data, select, from_cache=False):
        """暗号通貨情報のEmbedを送信"""
        try:
            # 選択された通貨名を取得
            selected_option = next((opt for opt in select.options if opt.value == crypto_id), None)
            crypto_name = selected_option.label if selected_option else crypto_id.title()
            
            embed = discord.Embed(
                title=f"💰 {crypto_name}",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            
            # 価格情報
            usd_price = crypto_data.get('usd', 0)
            jpy_price = crypto_data.get('jpy', 0)
            btc_price = crypto_data.get('btc', 0)
            
            embed.add_field(
                name="💵 USD",
                value=f"${usd_price:,.2f}" if usd_price >= 1 else f"${usd_price:.8f}",
                inline=True
            )
            embed.add_field(
                name="💴 JPY",
                value=f"¥{jpy_price:,.2f}" if jpy_price >= 1 else f"¥{jpy_price:.8f}",
                inline=True
            )
            embed.add_field(
                name="🪙 BTC",
                value=f"{btc_price:.8f}",
                inline=True
            )
            
            # 24時間変動率
            change_24h = crypto_data.get('usd_24h_change')
            if change_24h is not None:
                change_emoji = "📈" if change_24h > 0 else "📉"
                change_color = "+" if change_24h > 0 else ""
                
                embed.add_field(
                    name=f"{change_emoji} 24時間変動",
                    value=f"{change_color}{change_24h:.2f}%",
                    inline=True
                )
            
            # 時価総額
            market_cap = crypto_data.get('usd_market_cap')
            if market_cap and market_cap > 0:
                embed.add_field(
                    name="📊 時価総額 (USD)",
                    value=f"${market_cap:,.0f}",
                    inline=True
                )
            
            # 24時間取引量
            volume_24h = crypto_data.get('usd_24h_vol')
            if volume_24h and volume_24h > 0:
                embed.add_field(
                    name="📦 24時間取引量 (USD)",
                    value=f"${volume_24h:,.0f}",
                    inline=True
                )
            
            footer_text = "データ提供: CoinGecko API"
            if from_cache:
                footer_text += " (キャッシュ)"
            embed.set_footer(text=footer_text)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            print(f"Embed送信エラー: {str(e)}")
            await interaction.followup.send("❌ データの表示中にエラーが発生しました。", ephemeral=True)


class CryptoPrices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ready = False
        self.cache = CryptoCache(cache_duration=60)  # 60秒キャッシュ
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Cogが準備完了したことをマーク"""
        self.ready = True
        print("✅ CryptoPrices Cog が準備完了しました")
    
    @app_commands.command(name="crypto", description="暗号通貨の価格を表示します")
    async def crypto_prices(self, interaction: discord.Interaction):
        """暗号通貨の価格をドロップダウンから選択して表示"""
        try:
            # Botが準備完了しているか確認
            if not self.ready:
                await interaction.response.send_message(
                    "⚠️ Botがまだ準備中です。少し待ってから再度お試しください。",
                    ephemeral=True
                )
                return
            
            view = CryptoView(self.cache)
            embed = discord.Embed(
                title="🪙 暗号通貨価格チェッカー",
                description="下のドロップダウンメニューから暗号通貨を選択してください\n\n💡 価格データは60秒間キャッシュされます",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, view=view)
        
        except discord.errors.NotFound:
            print("⚠️ インタラクションがタイムアウトしました")
        except Exception as e:
            print(f"❌ crypto コマンドエラー: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ エラーが発生しました", ephemeral=True)
            except:
                pass
    
    @app_commands.command(name="crypto_list", description="主要な暗号通貨の価格を一覧表示します")
    async def crypto_list(self, interaction: discord.Interaction):
        """人気の暗号通貨の価格を一覧表示"""
        await interaction.response.defer()
        
        # キャッシュチェック
        cache_key = "crypto_list"
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            await self.send_list_embed(interaction, cached_data, from_cache=True)
            return
        
        try:
            # 主要な暗号通貨のIDリスト
            crypto_ids = "bitcoin,ethereum,ripple,cardano,solana,polkadot,dogecoin,avalanche-2,chainlink,matic-network"
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_ids}&vs_currencies=usd,jpy&include_24hr_change=true"
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.cache.set(cache_key, data)
                        await self.send_list_embed(interaction, data)
                    
                    elif response.status == 429:
                        await interaction.followup.send(
                            "⚠️ APIのレート制限に達しました。しばらく待ってから再度お試しください。"
                        )
                    
                    else:
                        error_text = await response.text()
                        print(f"API Error {response.status}: {error_text}")
                        await interaction.followup.send(
                            f"❌ API エラー (ステータス: {response.status})"
                        )
        
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ API接続がタイムアウトしました。")
        except Exception as e:
            print(f"crypto_list エラー: {str(e)}")
            await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}")
    
    async def send_list_embed(self, interaction, data, from_cache=False):
        """一覧表示用のEmbedを送信"""
        embed = discord.Embed(
            title="📊 主要暗号通貨 価格一覧",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        
        crypto_names = {
            "bitcoin": "Bitcoin (BTC)",
            "ethereum": "Ethereum (ETH)",
            "ripple": "Ripple (XRP)",
            "cardano": "Cardano (ADA)",
            "solana": "Solana (SOL)",
            "polkadot": "Polkadot (DOT)",
            "dogecoin": "Dogecoin (DOGE)",
            "avalanche-2": "Avalanche (AVAX)",
            "chainlink": "Chainlink (LINK)",
            "matic-network": "Polygon (MATIC)"
        }
        
        for crypto_id, crypto_data in data.items():
            name = crypto_names.get(crypto_id, crypto_id.title())
            usd_price = crypto_data.get('usd', 0)
            jpy_price = crypto_data.get('jpy', 0)
            change_24h = crypto_data.get('usd_24h_change')
            
            usd_str = f"${usd_price:,.2f}" if usd_price >= 1 else f"${usd_price:.8f}"
            jpy_str = f"¥{jpy_price:,.2f}" if jpy_price >= 1 else f"¥{jpy_price:.8f}"
            
            if change_24h is not None:
                change_emoji = "📈" if change_24h > 0 else "📉"
                change_text = f"{change_emoji} {change_24h:+.2f}%"
            else:
                change_text = "N/A"
            
            embed.add_field(
                name=name,
                value=f"💵 {usd_str}\n💴 {jpy_str}\n{change_text}",
                inline=True
            )
        
        footer_text = "データ提供: CoinGecko API"
        if from_cache:
            footer_text += " (キャッシュ)"
        embed.set_footer(text=footer_text)
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CryptoPrices(bot))
