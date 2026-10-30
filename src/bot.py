import asyncio
import os
import signal
import subprocess

import discord
import psutil
from dotenv import load_dotenv

SERVER_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim dedicated server\valheim_server.exe"
STEAM_APP_ID = 892970

load_dotenv()

bot = discord.Bot(intents=discord.Intents.default())

processing_command = False


async def is_server_running():
    validator = await asyncio.subprocess.create_subprocess_exec(
        "tasklist",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, _ = await validator.communicate()
    stdout_str = stdout.decode(errors="ignore")

    return "valheim_server.exe".lower() in stdout_str.lower()


async def start_server():

    if not await is_server_running():
        SP_VAL = os.environ["SERVER_PASS"]

        SERVER_PASS = SP_VAL if SP_VAL is not None else "12345"

        ARGS = [
            "-nographics",
            "-batchmode",
            "-name",
            "BBCentral",
            "-port",
            "2456",
            "-world",
            "Yorbjenheim",
            "-password",
            SERVER_PASS,
            "-savedir",
            "C:\\ValheimServerData",
            "-public",
            "1",
            "-crossplay",
        ]

        server_env = os.environ.copy()
        server_env["SteamAppId"] = str(STEAM_APP_ID)

        process = await asyncio.create_subprocess_exec(
            SERVER_PATH,
            *ARGS,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            env=server_env,
        )


async def stop_server():
    if await is_server_running():
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == "valheim_server.exe":
                target_pid = proc.info["pid"]
                break

        os.kill(target_pid, signal.CTRL_BREAK_EVENT)


@bot.slash_command()
async def start(ctx):
    global processing_command

    if not processing_command:
        processing_command = True

        try:
            await ctx.respond("Beginning server bootup...")
            await start_server()

        except Exception as err:
            with open("errlog.txt", "a") as file:
                file.write(str(err))

        processing_command = False

    else:
        await ctx.respond("Please do not spam commands.")


@bot.slash_command()
async def stop(ctx):
    global processing_command

    if not processing_command:
        processing_command = True

        try:
            await ctx.respond("Shutting down the server...")
            await stop_server()

        except Exception as err:
            with open("errlog.txt", "a") as file:
                file.write(str(err))

        processing_command = False

    else:
        await ctx.respond("Please do not spam commands.")


if __name__ == "__main__":
    bot.run(os.environ["TOKEN"])
