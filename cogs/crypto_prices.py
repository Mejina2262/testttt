import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from typing import Optional

class CryptoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        
    @discord.ui.select(
        placeholder="暗号通貨を選択してください",
        options=[
            discord.SelectOption(label="Bitcoin (BTC)", value="bitcoin", emoji="₿"),
            discord.SelectOption(label="Ethereum (ETH)", value="ethereum", emoji="Ξ"),
            discord.SelectOption(label="Ripple (XRP)", value="ripple", emoji="✕"),
            discord.SelectOption(label="Cardano (ADA)", value="cardano", emoji="₳"),
            discord.SelectOption(label="Solana (SOL)", value="solana", emoji="◎"),
            discord.SelectOption(label="Polkadot (DOT)", value="polkadot", emoji="●"),
            discord.SelectOption(label="Dogecoin (DOGE)", value="dogecoin", emoji="Ð"),
            discord.SelectOption(label="Avalanche (AVAX)", value="avalanche", emoji="🔺"),
            discord.SelectOption(label="Chainlink (LINK)", value="chainlink", emoji="🔗"),
            discord.SelectOption(label="Polygon (MATIC)", value="matic-network", emoji="⬡"),
            discord.SelectOption(label="Litecoin (LTC)", value="litecoin", emoji="Ł"),
            discord.SelectOption(label="Uniswap (UNI)", value="uniswap", emoji="🦄"),
            discord.SelectOption(label="Binance Coin (BNB)", value="binancecoin", emoji="💰"),
            discord.SelectOption(label="Tron (TRX)", value="tron", emoji="⚡"),
            discord.SelectOption(label="Stellar (XLM)", value="stellar", emoji="*"),
            discord.SelectOption(label="Monero (XMR)", value="monero", emoji="ɱ"),
            discord.SelectOption(label="Cosmos (ATOM)", value="cosmos", emoji="⚛"),
            discord.SelectOption(label="Algorand (ALGO)", value="algorand", emoji="▲"),
            discord.SelectOption(label="VeChain (VET)", value="vechain", emoji="V"),
            discord.SelectOption(label="Filecoin (FIL)", value="filecoin", emoji="⨎"),
            discord.SelectOption(label="Tezos (XTZ)", value="tezos", emoji="ꜩ"),
            discord.SelectOption(label="Shiba Inu (SHIB)", value="shiba-inu", emoji="🐕"),
            discord.SelectOption(label="Bitcoin Cash (BCH)", value="bitcoin-cash", emoji="₿"),
            discord.SelectOption(label="Aptos (APT)", value="aptos", emoji="🅰"),
            discord.SelectOption(label="Near Protocol (NEAR)", value="near", emoji="Ⓝ"),
        ]
    )
    async def select_crypto(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
        
        crypto_id = select.values[0]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd,jpy,btc&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if crypto_id in data:
                            crypto_data = data[crypto_id]
                            
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
                                value=f"${usd_price:,.2f}",
                                inline=True
                            )
                            embed.add_field(
                                name="💴 JPY",
                                value=f"¥{jpy_price:,.2f}",
                                inline=True
                            )
                            embed.add_field(
                                name="₿ BTC",
                                value=f"{btc_price:.8f}",
                                inline=True
                            )
                            
                            # 24時間変動率
                            change_24h = crypto_data.get('usd_24h_change', 0)
                            change_emoji = "📈" if change_24h > 0 else "📉"
                            change_color = "+" if change_24h > 0 else ""
                            
                            embed.add_field(
                                name=f"{change_emoji} 24時間変動",
                                value=f"{change_color}{change_24h:.2f}%",
                                inline=True
                            )
                            
                            # 時価総額
                            market_cap = crypto_data.get('usd_market_cap', 0)
                            if market_cap > 0:
                                embed.add_field(
                                    name="📊 時価総額 (USD)",
                                    value=f"${market_cap:,.0f}",
                                    inline=True
                                )
                            
                            # 24時間取引量
                            volume_24h = crypto_data.get('usd_24h_vol', 0)
                            if volume_24h > 0:
                                embed.add_field(
                                    name="📦 24時間取引量 (USD)",
                                    value=f"${volume_24h:,.0f}",
                                    inline=True
                                )
                            
                            embed.set_footer(text="データ提供: CoinGecko API")
                            
                            await interaction.followup.send(embed=embed, ephemeral=True)
                        else:
                            await interaction.followup.send("❌ データの取得に失敗しました。", ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ API エラー: {response.status}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)


class CryptoPrices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="crypto", description="暗号通貨の価格を表示します")
    async def crypto_prices(self, interaction: discord.Interaction):
        """暗号通貨の価格をドロップダウンから選択して表示"""
        view = CryptoView()
        embed = discord.Embed(
            title="🪙 暗号通貨価格チェッカー",
            description="下のドロップダウンメニューから暗号通貨を選択してください",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="crypto_list", description="複数の暗号通貨の価格を一覧表示します")
    async def crypto_list(self, interaction: discord.Interaction):
        """人気の暗号通貨の価格を一覧表示"""
        await interaction.response.defer()
        
        try:
            # 主要な暗号通貨のIDリスト
            crypto_ids = "bitcoin,ethereum,ripple,cardano,solana,polkadot,dogecoin,avalanche-2,chainlink,matic-network"
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_ids}&vs_currencies=usd,jpy&include_24hr_change=true"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
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
                            change_24h = crypto_data.get('usd_24h_change', 0)
                            
                            change_emoji = "📈" if change_24h > 0 else "📉"
                            change_text = f"{change_emoji} {change_24h:+.2f}%"
                            
                            embed.add_field(
                                name=name,
                                value=f"💵 ${usd_price:,.2f}\n💴 ¥{jpy_price:,.2f}\n{change_text}",
                                inline=True
                            )
                        
                        embed.set_footer(text="データ提供: CoinGecko API")
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"❌ API エラー: {response.status}")
        except Exception as e:
            await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}")


async def setup(bot):
    await bot.add_cog(CryptoPrices(bot))
