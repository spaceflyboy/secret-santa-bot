import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter
import random

description = "secreting santa"
bot = commands.Bot(command_prefix='.', description=description)

pools = {}
pairings = {}

#output options: console, discord channel where command sent, both
config = {"output": "console"}

@bot.command(pass_context=True) 
async def setOutput(ctx, out):
    s = str(out)
    if s == "channel" or s == "console" or s == "both":
        config["output"] = s
    else:
        await ctx.channel.send(f"setOutput failed because the output parameter provided {out} did not match one of the valid options: \"channel\", \"console\", \"both\"")


@bot.command(pass_context=True)
async def _help(ctx):
    if config["output"] == "console" or config["output"] == "both":
        print("Available commands:")
        print("\tcreateNewPool: create a new pool at the end of our pools dictionary and give it an empty list")
        print("\tdeletePool(index): delete the pool at passed in index parameter within pools dictionary")
        print("\taddUserToPool(index, user): add user parameter to pool at index parameter")
        print("\tviewPool(index): view the pool at index parameter in pools dict")
        print("\tviewAllPools: View all currently stored pools in the pools dict")
        print("\tgeneratePairingsForPool(index): Generate secret santa pairings for pool at index parameter")
        print("\treportPairingsToUsers(index): Report generated secret santa pairings for pool at index parameter")
        print("\t_exit: Bot log-off command")
        print("\t_help: List available commands")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.channel.send("Available commands:\n \
                \tcreateNewPool: create a new pool at the end of our pools dictionary and give it an empty list\n \
                \tdeletePool(index): delete the pool at passed in index parameter within pools dictionary \
                \taddUserToPool(index, user): add user parameter to pool at index parameter \
                \tviewPool(index): view the pool at index parameter in pools dict \
                \tviewAllPools: View all currently stored pools in the pools dict \
                \tgeneratePairingsForPool(index): Generate secret santa pairings for pool at index parameter \
                \treportPairingsToUsers(index): Report generated secret santa pairings for pool at index parameter \
                \t_exit: Bot log-off command \
                \t_help: List available commands \
                ")
@bot.command(pass_context=True)
async def runSecretSanta(ctx, userList : list): #Take in all users and do all the back end stuff
    userList = [] # Need to parse parameter list into users
    ID = await ctx.invoke(bot.get_command("createAndPopulate"), userList=userList)
    await ctx.invoke(bot.get_command("generatePairingsForPool"), index=ID)
    await ctx.invoke(bot.get_command("reportPairingsToUsers"), index=ID)
    
@bot.command(pass_context=True)
async def createNewPool(ctx):
    returnPool = len(pools)
    pools[returnPool] = list()
    if config["output"] == "console" or config["output"] == "both":
        print(f"Created new pool with ID {returnPool}")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.channel.send(f"Created new pool with ID {returnPool}")
    return returnPool
      

@bot.command(pass_context=True)
async def populatePool(ctx, index, userList: list):
    for user in userList:
        await ctx.invoke(bot.get_command("addUserToPool"), index = ID, user = user)
    
@bot.command(pass_context=True)
async def createAndPopulate(ctx, userList: list):
    ID = await ctx.invoke(bot.get_command("createNewPool"))
    await ctx.invoke(bot.get_command("populatePool"), index=ID,userList=userList)
    return ID
    
    
@bot.command(pass_context=True)
async def deletePool(ctx, index):
    pools.pop(int(index))

@bot.command(pass_context=True)
async def addUserToPool(ctx, index, user):
    cur_pool = pools[int(index)].copy()
    cur_pool.append(user)
    pools[int(index)] = cur_pool

@bot.command(pass_context=True)
async def viewPool(ctx, index):
    if config["output"] == "console" or config["output"] == "both":
        print(f"Viewing pool #{index}: {pools[int(index)]}")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.channel.send(f"Viewing pool #{index}: {pools[int(index)]}")

@bot.command(pass_context=True)
async def viewAllPools(ctx):
    if config["output"] == "console" or config["output"] == "both":
        print(f"{len(pools)} total active pools- Printing them, if applicable:")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.channel.send(f"{len(pools)} total active pools- Printing them, if applicable:")
    for key in pools.keys():
        if config["output"] == "console" or config["output"] == "both":
            print(f"pool #{key} = {pools[key]}")
        if config["output"] == "channel" or config["output"] == "both":
            await ctx.channel.send(f"pool #{key} = {pools[key]}")
        
@bot.command(pass_context=True)
async def generatePairingsForPool(ctx, index):
    local_pairs = {}
    
    cur_pool = pools[int(index)]
    random.shuffle(cur_pool)
    
    #cur_pool = ['<@!156894239123439616>', '<@!185422675974291457>', '<@!150458822778028032>', '<@!334148033946320897>', '<@!220704831931678731>']
    #cur_pool = ['<@!156894239123439616>', '<@!185422675974291457>', '<@!150458822778028032>', '<@!334148033946320897>']
    
    temp_pool = cur_pool.copy()
    inverse = False
    while len(temp_pool) > 0:
        if inverse:
            giver = temp_pool[-1]
            receiver = temp_pool[0]
            inverse = False
        else:
            giver = temp_pool[0]
            receiver = temp_pool[-1]
            inverse = True
        local_pairs[giver] = receiver
        try:
            temp_pool.remove(giver)
        except ValueError:
            pass
    
    local_pairs[giver] = cur_pool[0]
    pairings[int(index)] = local_pairs
    if config["output"] == "console" or config["output"] == "both":
        print(f"Generated the following pairings for pool #{index}: {pairings[int(index)]}")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.channel.send(f"Generated the following pairings for pool #{index}: {pairings[int(index)]}")
    
    """
    done = False
    giver = 0
    recipient = len(cur_pool) - 1
    leftOffset = True
    offset = 1
    print(f"generatePairingsForPool({index}): Before Loop: giver = {giver}, recipient = {recipient}, cur_pool = {cur_pool}")
    while not done:
        print(f"Top of Loop: giver = {giver}, recipient = {recipient}, offset = {offset}, leftOffset flag = {leftOffset}")
        if recipient == 0:
            done = True
            local_pairs[cur_pool[giver]] = cur_pool[recipient]
        else:
            local_pairs[cur_pool[giver]] = cur_pool[recipient]
            temp = giver
            giver = recipient
            if leftOffset:
                recipient = temp + offset
                leftOffset = False
            else:
                recipient = temp - offset
                offset += 1
                leftOffset = True
        
            if giver == len(cur_pool)//2:
                recipient = 0
                print(f"We are going to end the loop next iteration since giver = {giver} and recipient = {recipient}")
    """
    
    """
    print(f"generatePairingsForPool({index}): about to enter loop, pool = {pool}")
    for user in cur_pool:
        print(f"Top of loop: user = {user}, uncompleted_users = {uncompleted_users}")
        temp = uncompleted_users.copy()
        try:
            temp.remove(user)
        except ValueError:
            pass         
        print(f"Middle of loop: temp = {temp}")
        partner = random.choice(temp)
        print(f"Near end of loop: chosen partner = {partner}")
        uncompleted_users.remove(partner)
        print(f"End of loop: uncompleted_users = {uncompleted_users}")
        local_pairs[user] = partner
    """
    
@bot.command(pass_context=True)
async def reportPairingsToUsers(ctx, index):
    #cur_pool = pools[index]
    local_pairs = pairings[int(index)]
    converter = MemberConverter()
   
    for user in local_pairs.keys():
        #report local_pairs[user] to each user
        giver = await converter.convert(ctx, user)
        receiver = await converter.convert(ctx, local_pairs[user])
        channel = await giver.create_dm()
        await channel.send(f"You are secret santa for {receiver}")
        
@bot.command()
async def _exit(ctx):
    await bot.logout()
        
#print("test")

        
    



    

