import asyncio
import discord
from dotenv import load_dotenv
import os
import signal

load_dotenv()
TOKEN = os.getenv("TOKEN")

server_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim dedicated server"
server_exe = "valheim_server.exe"
server_path = os.path.join(server_dir, server_exe)

dev_role_id = "<@&1565556353097797732>"
steam_app_id = 892970 # the steam app id of the steam dedicaed valheim server


async def is_server_hot():
    validator = await asyncio.subprocess.create_subprocess_exec(
        "tasklist",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, _ = await validator.communicate()
    stdout_str = stdout.decode(errors="ignore")

    return server_exe.lower() in stdout_str.lower()


async def start_server_process(server_path):
    try:

        # this flag represents the CREATE_NEW_PROCESS_GROUP constant
        creation_flags = 0x00000200

        args = [
            "-nographics",
            "-batchmode",
            "-name",
            "BBCentral",
            "-port",
            "2456",
            "-world",
            "Yorbjenheim",
            "-password",
            "valheim",
            "-savedir",
            "C:\\ValheimServerData",
            "-public",
            "1",
            "-crossplay",
        ]

        server_env = os.environ.copy()
        server_env["SteamAppId"] = str(steam_app_id)

        process = await asyncio.create_subprocess_exec(
            server_path,
            *args,
            creationflags=creation_flags,
            env=server_env,
        )

        return process, None

    except Exception as e:
        return None, e


async def stop_server_process(process):
    try:

        if process is None or process.returncode is not None:
            return

        # CTRL_BREAK is an alternative to CTRL_C; CTRL_BREAK is able to target the process group created with CREATE_NEW_PROCESS_GROUP.
        os.kill(process.pid, signal.CTRL_BREAK_EVENT)

        await process.communicate()

        return None

    except Exception as e:
        return e


class ServerBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        self.processing = False

    async def on_ready(self):
        print("Logged in")

    async def on_message(self, message: discord.Message):
        try:

            if message.author == self.user:  # ignore own messages
                return

            if message.content.startswith("$tart") and not self.processing:
                self.processing = True

                if not await is_server_hot():

                    await message.channel.send(
                        "Booting up server, please be patient..."
                    )

                    self.server_process, err = await start_server_process(
                        server_path=server_path
                    )
                    if err is not None:

                        with open("errlog.txt", "a") as file:
                            file.write(str(err)+"\n")

                        await message.channel.send(
                            f"{dev_role_id} Startup error, check log when possible."
                        )

                    else:
                        await message.channel.send(
                            f"The server has been started, have fun! {message.author.mention}"
                        )

                else:
                    await message.channel.send(
                        f"Server is already active, please refrain from spamming the start command.{message.author.mention}"
                    )

                self.processing = False

            if message.content.startswith("$top") and not self.processing:
                self.processing = True

                if await is_server_hot():

                    await message.channel.send("Shutting the server down...")

                    err = await stop_server_process(self.server_process)
                    if err is not None:

                        with open("errlog.txt", "a") as file:
                            file.write(str(err)+"\n")

                        await message.channel.send(
                            f"{dev_role_id} Shutdown error, check errlog when possible."
                        )

                    else:
                        await message.channel.send(
                            "Server has been shut down, hope you had fun!"
                        )

                else:
                    await message.channel.send(f"Server is not active.")

                self.processing = False

        except Exception as err:
            self.processing = False

            with open("errlog.txt", "a") as file:
                file.write(str(err)+"\n")


if __name__ == "__main__":
    bot = ServerBot()
    bot.run(TOKEN)
