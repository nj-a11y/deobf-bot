import discord
from discord.ext import commands
import os
import tempfile
import subprocess
import asyncio
import sys
from pathlib import Path

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

BASE_DIR = Path(__file__).resolve().parent

# Automatically locate deob.py anywhere
if (BASE_DIR / "deob.py").exists():
    DEOBF_SCRIPT = BASE_DIR / "deob.py"
elif (BASE_DIR / "deobf" / "deob.py").exists():
    DEOBF_SCRIPT = BASE_DIR / "deobf" / "deob.py"
else:
    DEOBF_SCRIPT = BASE_DIR / "deob.py"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="!deobf | Deobfuscating Scripts"))

@bot.command(name="deobf")
async def deobfuscate(ctx):
    """Deobfuscate a script attached as a file or provided in a code block."""
    script_content = ""
    file_name = "script.lua"

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith((".lua", ".txt", ".luau")):
            script_content = (await attachment.read()).decode("utf-8", errors="ignore")
            file_name = attachment.filename
    else:
        content = ctx.message.content.replace("!deobf", "").strip()
        if content.startswith("```") and content.endswith("```"):
            lines = content.splitlines()
            if len(lines) > 2:
                script_content = "\n".join(lines[1:-1])
        elif content:
            script_content = content

    if not script_content:
        await ctx.send("❌ **Please attach a script file (.lua) or provide it in a code block with the command.**\nExample: `!deobf` with an attached file.")
        return

    msg = await ctx.send("⏳ **Deobfuscating script... Please wait.**")

    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = Path(temp_dir) / file_name
        output_file = Path(temp_dir) / "output" / file_name

        input_file.write_text(script_content, encoding="utf-8")

        def run_process():
            return subprocess.run(
                [sys.executable, str(DEOBF_SCRIPT), str(input_file)],
                cwd=str(temp_dir),
                capture_output=True,
                text=True
            )

        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, run_process)

        if output_file.exists():
            result_code = output_file.read_text(encoding="utf-8", errors="ignore")
            
            if len(result_code) <= 1900:
                await msg.edit(content=f"✅ **Script deobfuscated successfully:**\n```lua\n{result_code}\n```")
            else:
                out_path = Path(temp_dir) / f"deobfuscated_{file_name}"
                out_path.write_text(result_code, encoding="utf-8")
                await msg.edit(content="✅ **Script deobfuscated successfully! The output is attached below:**")
                await ctx.send(file=discord.File(str(out_path)))
        else:
            err_msg = res.stderr[:1000] if res.stderr else "No output generated."
            await msg.edit(content=f"❌ **An error occurred during deobfuscation:**\n```text\n{err_msg}\n```")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
    else:
        bot.run(TOKEN)
