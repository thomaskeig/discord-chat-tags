import discord
from discord import option
from discord.commands import option, Option
from discord.ext import commands, tasks
import asyncio

import json
import yaml
import time

greenColour = 0x41FF33
redColour = 0xFF3333
yellowColour = 0xFFD33A
defaultColour = 0x78a7ff

tagNames = []

print('Loading Settings...')

# Load Settings
with open('./settings.yml', encoding="utf8") as file:
    settings = yaml.load(file, Loader=yaml.FullLoader)
    print('Loaded settings!')

# Define Discord Modules
intents = discord.Intents.default()
# intents.members = True
# intents.message_content = True

bot = discord.Bot(debug_guilds=[settings["main-server-id"]], intents=intents)

def permissionCheck(userid, allowedRoles, list=True):
    server = bot.get_guild(settings['main-server-id'])
    user = server.get_member(int(userid))

    if list == True:
        allowed = False
        for i in allowedRoles:
            if i in [r.id for r in user.roles]:
                allowed = True
                break
    
    return allowed

@bot.event
async def on_ready():
    syncall.start()
    print(f'Logged in as {bot.user}')

tag = bot.create_group("tag", "Manage chat tags")

@bot.command(name='ghostping', description = 'Ghost ping a user in the chat')
@option("mention", discord.User, description="User to ping", required=True)
async def ghostping(ctx, mention):

    message = await ctx.send(f'<@{mention.id}>')
    await message.delete()

    await ctx.respond('Ghost ping has been sent.', ephemeral=True)


@tag.command(name='use', description = 'Use a tag in the chat')
@option("query", description="The name/identifier of the tag", required=True)
@option("mention", discord.User, description="Mention a user in the response", required=False)
async def tag_use(ctx, query: str, mention=''):

    with open('./tags.json', 'r') as f:
        tags = json.load(f)
    
    query = query.lower()

    found = False
    dictUnit = 0
    for i in tags:
        if i['name'] == query or str(i['id']) == query:
            found = True

            placement = dictUnit
            tagMessage = i['message']
            break
        dictUnit += 1
    
    if not found:
        await ctx.respond('That tag was not found.', ephemeral=True)
    
    else:

        with open('./tags.json', 'r') as f:
            tags = json.load(f)

        tags[placement]['uses'] = tags[placement]['uses'] + 1
        
        with open('./tags.json', 'w') as f:
            json.dump(tags, f, indent=4)
        
        if mention != '': # If the mention is used
            mention = f'<@{mention.id}>'
        
        embed = discord.Embed(color=defaultColour, description=tagMessage)

        await ctx.respond(content=mention, embed=embed)
    

@tag.command(name='create', description = 'Create a tag to use in the chat')
@option("name", description="The name/identifier of the tag - Keep this as simple as possible with as little spaces as possible", required=True)
@option("message", description="The message to attach to the tag.", required=True)
async def tag_create(ctx, name: str, message: str):

    if not permissionCheck(userid = ctx.author.id,
        allowedRoles = settings['roles']['tagCreator']):

        await ctx.respond('You are not allowed to create tags.', ephemeral=True)
    
    elif permissionCheck(userid = ctx.author.id,
        allowedRoles = settings['roles']['tagCreationBlacklist']):
    
        await ctx.respond('You have been banned from creating tags.', ephemeral=True)

    else:
        nameMaxLength = 15
        messageMaxLength = 200

        if len(name) > nameMaxLength:
            await ctx.respond(f'The tag name must be no more than **{nameMaxLength}** characters. The one you entered is **{len(name)}** characters long.')

        elif len(message) > messageMaxLength:
                    await ctx.respond(f'The tag message must be no more than **{messageMaxLength}** characters. The one you entered is **{len(message)}** characters long.')
        
        else:
            with open('./tags.json', 'r') as f:
                tags = json.load(f)
            
            try:
                prevId = tags[-1]['id']
            except:
                prevId = 0
            
            creationTime = round(time.time())
            newTagEntry = {
                "id": prevId+1,
                "name": name,
                "message": message,
                "author": ctx.author.id,
                "creationTime": creationTime,
                "uses": 0
            }

            tags.append(newTagEntry)

            with open('./tags.json', 'w') as f:
                json.dump(tags, f, indent=4)

            embed = discord.Embed(title='Tag Created', color=defaultColour)

            embed.add_field(name='Name', value=name, inline=True)
            embed.add_field(name='Message', value=message, inline=True)
            embed.add_field(name='Author', value=f'<@{ctx.author.id}>', inline=True)
            embed.add_field(name='Creation Time', value=f'<t:{creationTime}>', inline=True)
            embed.add_field(name='ID', value=prevId+1, inline=True)

            await ctx.respond(embed=embed, ephemeral=True)




@tag.command(name='delete', description = 'Delete one of your existing tags')
@option("name", description="The name/identifier of the tag to delete", required=True)
@option("warning", description="Running this command will delete the tag forever. Type 'confirm' in this box to acknowledge.", required=True)
async def tag_create(ctx, name: str, warning: str):

    if permissionCheck(userid = ctx.author.id,
        allowedRoles = settings['roles']['moderator']):
        moderator = True
    
    else:
        moderator = False


    with open('./tags.json', 'r') as f:
        tags = json.load(f)
    
    query = name.lower()

    found = False
    dictUnit = 0
    for i in tags:
        if i['name'].lower() == query.lower() or str(i['id']) == query:
            found = True

            placement = dictUnit

            tagId = i['id']
            tagName = i['name']
            #tagMessage = i['message']
            tagAuthor = i['author']
            #tagCreationTime = i['creationTime']
            #tagUses = i['uses']
            break
        dictUnit += 1
    
    if not found:
        await ctx.respond('That tag was not found.', ephemeral=True)
    
    else:

        if tagAuthor != ctx.author.id and moderator == False: # If the tag isn't created by the author and they are not a moderator
            await ctx.respond('You can only delete tags that you own.', ephemeral=True)
        
        if warning.lower() != 'confirm':
            await ctx.respond('Please retype this command with "confirm" in the command box to proceed with deleting this tag.', ephemeral=True)
        
        else:

            with open('./tags.json', 'r') as f:
                tags = json.load(f)

            tags.remove(tags[placement])
            
            with open('./tags.json', 'w') as f:
                json.dump(tags, f, indent=4)

            await ctx.respond(f'Tag `{tagName}` (`{tagId}`) has successfully been deleted!')


@tag.command(name='list', description = 'List all the active tags')
async def tag_list(ctx):
    with open('./tags.json', 'r') as f:
        tags = json.load(f)
    
    message = ''
    for i in tags:
        message = message + i['name'] + ', '
    
    await ctx.respond(message, ephemeral=True)


@tag.command(name='info', description = 'Find info/stats on any tag')
@option("query", description="The name/identifier of the tag", required=True)
async def tag_info(ctx, query: str, mention=''):

    with open('./tags.json', 'r') as f:
        tags = json.load(f)
    
    query = query.lower()

    found = False
    dictUnit = 0
    for i in tags:
        if i['name'] == query or str(i['id']) == query:
            found = True

            tagId = i['id']
            tagName = i['name']
            tagMessage = i['message']
            tagAuthor = i['author']
            tagCreationTime = i['creationTime']
            tagUses = i['uses']
            break
        dictUnit += 1
    
    if not found:
        await ctx.respond('That tag was not found.', ephemeral=True)
    
    else:
        
        embed = discord.Embed(color=defaultColour, title=f'Tag Info: {tagName}')

        embed.add_field(name='Message', value=tagMessage, inline=True)
        embed.add_field(name='Author', value=f'<@{tagAuthor}>', inline=True)
        embed.add_field(name='Creation Time', value=f'<t:{tagCreationTime}>', inline=True)
        embed.add_field(name='Uses', value=tagUses, inline=True)
        embed.add_field(name='ID', value=tagId, inline=True)

        embed.set_footer(text=f'There are currently {len(tags)} active tags')

        await ctx.respond(embed=embed)


@tasks.loop(minutes=30)
async def syncall():

    with open('./users.json', 'r') as f:
        data = json.load(f)
    
    linked_users = (list(data.keys()))

    for userid in linked_users:

        await syncPurchases(userid)
        await asyncio.sleep(15)

bot.run(settings['bot-token'])
