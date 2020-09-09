from discord.ext import commands
from discord import Embed
from sqlalchemy.sql.expression import select, func as sql_func
from db import models
import discord
import random
import asyncio
import os


discord_channel_id = os.environ.get('DISCORD_CHANNEL_ID')

class PeshoBot(commands.Bot):

    def __init__(self, prefix, db_connection):
        super().__init__(
            command_prefix = prefix
        )
        self.db_conn = db_connection
        self.reactions = [
            '1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟', '\U0001F170', '\U0001F171',
            '\U0001F1E8', '\U0001F1E9', '\U0001F1EA', '\U0001F1EB', '\U0001F1EC', '\U0001F1ED',
            '\U0001F1EF', '\U0001F1F0', '\U0001F1F1', '\U0001F1F2'
        ]
        self.setup()

    def setup(self):

        @self.event
        async def on_ready():
            print(f'{self.user} has connected to Discord!')

        @self.event
        async def on_message(message):
            '''
            Method that adds a reaction if a word is contained in a given message.
            :param message:
            :return:
            '''
            if message.author == self.user:
                return
            elif 'dota' in message.content or 'dotichka' in message.content:
                await message.add_reaction('\U0001F44D')
            elif 'boje' in message.content or 'boga' in message.content:
                await message.add_reaction('\U0001F4A9')

            await self.process_commands(message)

        @self.event
        async def on_voice_state_update(member, before, after):
            '''
            Method that sends a message whenever a member joins a given voice channel.
            :param member:
            :param before:
            :param after:
            :return:
            '''
            discord_guild_channel = self.get_channel(int(discord_channel_id))
            query = await self.db_conn.execute(
                select(
                    [models.users.c.voice_channel_greeting]
                ).where(models.users.c.discord_id == str(member.id))
            )
            msg = await query.first()
            if msg[0]is not None and not before.channel:
                await discord_guild_channel.send(msg[0])

        @self.command(aliases=['pesho'])
        async def peshe(ctx):
            '''
            Method that just returns some phrase from the database.
            :param ctx:
            :return:
            '''
            x = await self.db_conn.execute(select(
                [models.pesho_tapni.c.text]).order_by(sql_func.random()))
            msg = await x.first()
            await ctx.send(msg[0])

        @self.command(content=None)
        async def vqrno(ctx, member=None, question=None, wait_time=30):
            '''
            Method that asks a user a question of the form: "Is it true that 'member' 'question'?" and then given YES
            and NO options as reactions. If after the given wait time the YES votes are more the bot will send a
            message confirming that the answer to the question is true.
            If no parameters a supplied a random question from the database is taken with a random member of the
            discord server.
            :param ctx:
            :param member: full discord user name
            :param question:
            :param wait_time: (int) seconds to wait before confirming answer
            :return:
            '''
            if not member:
                member = random.choice([m for m in ctx.guild.members if m.status == discord.Status.online])
                member = member.mention
            if not question:
                query = await self.db_conn.execute(select(
                    [models.vqrno.c.text]).order_by(sql_func.random()))
                query_result = await query.first()
                question = query_result[0]

            embed = Embed(description=f'Вярно ли е че {member} {question}?')
            msg = await ctx.send(embed=embed)
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')
            await asyncio.sleep(wait_time)
            msg = await ctx.channel.fetch_message(msg.id)

            if msg.reactions[0].count > msg.reactions[1].count:
                embed_answer = Embed(description=f'{member} {question}!!!')
                await ctx.send(embed=embed_answer)
            else:
                return

        @self.command()
        async def roll(ctx, *args):
            '''
            Method to roll a random number. Given 1 argument it rolls from 1 to arg, else it defaults to
            1-100 rolls.
            :param ctx:
            :param args: upper bound for roll
            :return:
            '''
            if len(args) == 1:
                if args[0].isdigit():
                    upper_bound = int(args[0])
                    await ctx.send(f'{random.randrange(1, upper_bound)} (1-{upper_bound})')
                else:
                    return
            elif len(args) == 0:
                await ctx.send(f'{random.randrange(1, 100)} (1-100)')
            else:
                return

        @self.command(
            pass_context=True,
            brief='Анкета',
            description='Форматът на анкетата е: !poll "Въпрос" "Oтговор_1" "Oтговор_2" ... "Oтговор_N"')
        async def poll(ctx, question, *options: str):
            #credit to: https://gist.github.com/Vexs/f2c1bfd6bda68a661a71accd300d2adc
            if len(options) <= 1 or len(options) > 22:
                return

            description = []

            for x, option in enumerate(options):
                description += '\n {} {}'.format(self.reactions[x], option)

            embed = Embed(title=question, description=''.join(description))
            react_message = await ctx.send(embed=embed)

            for reaction in self.reactions[:len(options)]:
                await react_message.add_reaction(reaction)

            embed.set_footer(text='Poll ID: {}'.format(react_message.id))
            await react_message.edit(embed=embed)

        @self.command(pass_context=True)
        async def add_to_poll(ctx, poll_id, *new_options):
            '''
            A method to add new poll options to an existing poll
            :param ctx:
            :param poll_id: id of previously created poll
            :param new_options: poll options to be added
            :return:
            '''
            msg = await ctx.channel.fetch_message(poll_id)
            options_number = len(msg.embeds[0].description.splitlines())
            new_description = msg.embeds[0].description

            for n, new_option in enumerate(new_options):
                new_description += f'\n {self.reactions[options_number + n]} {new_option}'

            new_embed = Embed(title=msg.embeds[0].title, description=new_description)
            new_embed.set_footer(text=f'Poll ID: {poll_id}')

            await msg.edit(embed=new_embed)
            for n, new_option in enumerate(new_options):
                await msg.add_reaction(self.reactions[options_number + n])

        @self.group()
        async def update(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send('Invalid update command...')

        @update.command()
        async def join_message(ctx, discord_id, message):
            '''
            Method to update the join message of a user. Requires server admin privilege.
            :param ctx:
            :param discord_id: discord id of a user
            :param message: new join message for given user
            :return:
            '''
            query = await self.db_conn.execute(
                select([models.users.c.is_bot_admin]).where(
                    models.users.c.discord_id == str(ctx.message.author.id))
            )
            is_bot_admin = await query.first()
            if is_bot_admin[0] == True:
                await self.db_conn.execute(models.users.update().where(
                    models.users.c.discord_id == discord_id).values(voice_channel_greeting=message))
                await ctx.send('Done')
            else:
                await ctx.send('Oh no no no...')

        @update.command(description='input 2 for add permission')
        async def permission(ctx, discord_id, option):
            '''
            Method do add permissions to given user. Requires server admin privilege.
            :param ctx:
            :param discord_id: discord id of user
            :param option: (int) valid values of 1 and 2. 1 for playing music, 2 for adding options
            to other commands
            :return:
            '''
            query = await self.db_conn.execute(
                select([models.users.c.is_bot_admin]).where(
                    models.users.c.discord_id == str(ctx.message.author.id))
            )
            is_bot_admin = await query.first()
            if is_bot_admin[0] == True:
                if option == '1':
                    await self.db_conn.execute(
                        models.users.update().where(
                            models.users.c.discord_id==str(discord_id)).values(play_music=True)
                    )
                    await ctx.send('Done')
                elif option == '2':
                    await self.db_conn.execute(
                        models.users.update().where(
                            models.users.c.discord_id == str(discord_id)).values(add_to_commands=True)
                    )
                    await ctx.send('Done')
                else:
                    await ctx.send('Invalid permission...')
            else:
                await ctx.send('Oh no no no...')

        @update.command()
        async def vqrno(ctx, question):
            '''
            Method to add new questions to !vqrno command. Requires server admin privilege.
            :param ctx:
            :param vapros: question to be added.
            :return:
            '''
            query = await self.db_conn.execute(
                select([models.users.c.add_to_commands]).where(
                    models.users.c.discord_id == str(ctx.message.author.id))
            )
            commands_permission = await query.first()
            if commands_permission[0] == True:
                await self.db_conn.execute(models.vqrno.insert().values(text=question))
                await ctx.send('Done')
            else:
                await ctx.send('Oh no no no...')

        @self.group()
        async def list(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send('Invalid update command...')

        @list.command()
        async def vqrno(ctx):
            '''
            List all questions saved in the database under the vqrno table. It lists in batches of 20
            as otherwise the message length overflows.
            :param ctx:
            :return:
            '''
            query = await self.db_conn.execute(
                select([models.vqrno.c.id, models.vqrno.c.text]
                ).order_by(models.vqrno.c.active, models.vqrno.c.id)
            )
            queryset = await query.fetchall()
            output = ''
            for index, row in enumerate(queryset):
                output = output + f'{row[0]}   |   {row[1]}\n'
                if index % 20 == 0:
                    await ctx.send(output)
                    output = ''
            await ctx.send(output)

        @list.command()
        async def peshe(ctx):
            '''
            List all phrases in the database under the peshe table. It lists in batches of 20
            as otherwise the message length overflows.
            :param ctx:
            :return:
            '''
            query = await self.db_conn.execute(
                select([models.pesho_tapni.c.id,models.pesho_tapni.c.text]
                ).order_by(models.pesho_tapni.c.active, models.pesho_tapni.c.id)
            )
            queryset = await query.fetchall()
            output = ''
            for index, row in enumerate(queryset):
                output = output + f'{row[0]}  |   {row[1]}\n'
                if index % 20 == 0:
                    await ctx.send(output)
                    output = ''
            await ctx.send(output)

        @self.group()
        async def rm(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send('Invalid update command...')

        @rm.command()
        async def vqrno(ctx, id):
            query = await self.db_conn.execute(
                select([models.users.c.add_to_commands]).where(
                    models.users.c.discord_id == str(ctx.message.author.id))
            )
            commands_permission = await query.first()
            if commands_permission[0] == True:
                await self.db_conn.execute(models.vqrno.delete().where(models.vqrno.c.id == int(id)))
                await ctx.send('Done')
            else:
                await ctx.send('Oh no no no...')

        @rm.command()
        async def peshe(ctx, id):
            query = await self.db_conn.execute(
                select([models.users.c.add_to_commands]).where(
                    models.users.c.discord_id == str(ctx.message.author.id))
            )
            commands_permission = await query.first()
            if commands_permission[0] == True:
                await self.db_conn.execute(models.pesho_tapni.delete().where(models.pesho_tapni.c.id == int(id)))
                await ctx.send('Done')
            else:
                await ctx.send('Oh no no no...')
