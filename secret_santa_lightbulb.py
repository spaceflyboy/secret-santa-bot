import lightbulb
import hikari
import random
import tokenfile

bot = lightbulb.BotApp(token=tokenfile.token, prefix=".")

pools = {}
pairings = {}

user_maps = {} # Map pool id to a map of user id to user objects (complicated but necessary, I think)
#user_maps_inverse = {}
user_blacklist_maps = {}


#output options: console, discord channel where command sent, both
config = {"output": "console"}

@bot.command
@lightbulb.command("view-config", "View the config data structure")
@lightbulb.implements(lightbulb.SlashCommand)
async def view_config(ctx: lightbulb.Context) -> None:
    for key in config:
        if config["output"] == "console" or config["output"] == "both":
            print(f"config[{key}] = {config[key]}")
        if config["output"] == "channel" or config["output"] == "both":
            await ctx.respond(f"config[{key}] = {config[key]}")

@bot.command
@lightbulb.option("output", "output setting to be used by other bot commands", str)
@lightbulb.command("set-output", "Set the config value for where command results are outputted (console, channel, both)", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def set_output(ctx: lightbulb.Context, output: str) -> None:
    s = str(output)
    if s == "channel" or s == "console" or s == "both":
        config["output"] = s
        await ctx.respond(f"setOutput ran succesfully and all subsequent output will be routed according to the new setting, {s}")
    else:
        await ctx.respond(f"setOutput failed because the output parameter provided {out} did not match one of the valid options: \"channel\", \"console\", \"both\"")
      
async def create_and_populate_backend(userlist: list) -> int:
    ID = await create_new_pool_backend()
    await populate_pool_backend(ID, userlist)
    return ID

async def recurse(gidx: int, givers: list, already_receiving: list, local_pairs: dict) -> bool:
    giver = givers[gidx]
    choices = [i for i in givers if i != giver and i not in already_receiving and i not in user_blacklist_maps[int(idex)][giver]]
    if not choices:
        return False
    
    for choice in choices:
        already_receiving.append(choice)
        local_pairs[giver] = choice
        
        check = recurse(gidx+1, givers, already_receiving, local_pairs)
        
        if check:
            return True
        else:
            del local_pairs[giver]
            already_receiving.pop()
    
    return False
    

async def generate_pairings_for_pool_backend(index: int) -> bool:
    local_pairs = {}
    cur_pool = pools[int(index)]
    
    check = recurse(0, random.shuffle(cur_pool), [], local_pairs)
    if not check:
        return check
    else:
        pairings[int(index)] = local_pairs
        return True
        
    """
    done = False
    while not done:
        local_pairs = {}
        already_receiving = {}
        for giver in cur_pool:
            choices = [i for i in cur_pool if i != giver and i not in already_receiving and i not in user_blacklist_maps[int(index)][giver]]
            if not choices:
                break
            #print(f"giver = {giver}")
            #print(f"already_receiving = {already_receiving.keys()}")
            #print(f"giver's blacklist = {user_blacklist_maps[int(index)][giver]}")
            #print(f"choices = {choices}")
            receiver = random.choice(choices)
            local_pairs[giver] = receiver
            already_receiving[receiver] = 1
        
        done = True
    
    pairings[int(index)] = local_pairs
    
    """
    """
    local_pairs = {}
    
    cur_pool = pools[int(index)]
    #random.seed()
    random.shuffle(cur_pool)
    
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
    """

async def create_new_pool_backend() -> int:
    returnPool = len(pools)
    pools[returnPool] = list()
    user_blacklist_maps[returnPool] = dict()
    #user_maps[returnPool] = dict()
    #user_maps_inverse[returnPool] = dict()
    return returnPool

async def add_user_to_pool_backend(index: int, user) -> None:
    cur_pool = pools[int(index)].copy()
    #newID = len(cur_pool)
    #user_maps[int(index)][newID] = user
    cur_pool.append(user)
    pools[int(index)] = cur_pool
    user_blacklist_maps[int(index)][user] = []

async def populate_pool_backend(index: int, userlist: list) -> None:
    for user in userlist:
        await add_user_to_pool_backend(index, user)
        
async def process_user_list(userlist: str) -> list[hikari.Member]:
    return userlist.split(" ")
    
async def to_member(ctx: lightbulb.Context, user: str) -> hikari.Member:
    return_val = await lightbulb.converters.special.MemberConverter(ctx).convert(user)
    return return_val

async def report_pairings_to_users_backend(ctx: lightbulb.Context, index: int):

    #cur_pool = pools[index]
    local_pairs = pairings[int(index)]
    
    for user_id in local_pairs.keys():
        print(f"user_id = {user_id}")
        print(f"receiver_id = {local_pairs[user_id]}")
        #user = user_maps[int(index)][user_id]
        
        user = await to_member(ctx, user_id)
        receiver = await to_member(ctx, local_pairs[user_id])
        
        #print(f"local_pairs = {local_pairs}")
        #print(f"user = {user}")
        #print(f"receiver_id = {local_pairs[user_id]}")
        #print(f"user_maps[{index}] = {user_maps[index]}")
        #report local_pairs[user] to each user
        
        await user.send(f"You are secret santa for {receiver}")

# Make sure that the userlist provided only contains actual user objects
# async def user_list_sanity_check(userlist: list):

@bot.command()
@lightbulb.option("index", "Pool index for blacklisting", int)
@lightbulb.option("user1", "User to whose blacklist user2 will be added", str)
@lightbulb.option("user2", "User to add to user1's blacklist", str)
@lightbulb.command("add-user-to-blacklist", "Prevent user1 from getting user2 as a \"receiver\" in generation later on", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def add_user_to_blacklist(ctx: lightbulb.Context, index: int, user1: str, user2: str) -> None:
    user_blacklist_maps[int(index)][user1].append(user2)
    
@bot.command()
@lightbulb.option("index", "Pool index for blacklisting", int)
@lightbulb.option("user1", "User whose blacklist is being set", str)
@lightbulb.option("userlist", "List of users to add to user1's blacklist", str)
@lightbulb.command("set-user-blacklist", "Set user's blacklist", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def set_user_blacklist(ctx: lightbulb.Context, index: int, user1: str, userlist: str) -> None:
    userlist_processed = await process_user_list(userlist)
    user_blacklist_maps[int(index)][user1] = userlist_processed

@bot.command()
@lightbulb.option("index", "Pool index for blacklisting", int)
@lightbulb.option("user1", "User whose blacklist you want to view", str)
@lightbulb.command("view-blacklist", "View user's blacklist", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def view_blacklist(ctx: lightbulb.Context, index: int, user1: str) -> None:

    if config["output"] == "console" or config["output"] == "both":
        print(f"{user1}'s blacklist: {user_blacklist_maps[int(index)][user1]}")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.respond(f"{user1}'s blacklist: {user_blacklist_maps[int(index)][user1]}")
        
@bot.command()
@lightbulb.option("index", "Pool index for blacklisting", int)
@lightbulb.command("view-all-blacklists", "View all blacklists for a pool", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def view_all_blacklists(ctx: lightbulb.Context, index: int) -> None:

    if config["output"] == "console" or config["output"] == "both":
        for key in user_blacklist_maps[int(index)]:
            print(f"{key}'s blacklist: {user_blacklist_maps[int(index)][key]}")
    if config["output"] == "channel" or config["output"] == "both":
        for key in user_blacklist_maps[int(index)]:
            await ctx.respond(f"{key}'s blacklist: {user_blacklist_maps[int(index)][key]}")

@bot.command
@lightbulb.command("create-new-pool", "Create a new pool for pairing generation later on")
@lightbulb.implements(lightbulb.SlashCommand)
async def create_new_pool(ctx: lightbulb.Context) -> None:
    returnPool = await create_new_pool_backend()
    if config["output"] == "console" or config["output"] == "both":
        print(f"Created new pool with ID {returnPool}")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.respond(f"Created new pool with ID {returnPool}")
        
@bot.command
@lightbulb.option("user1", "User 1", hikari.Member)
@lightbulb.option("user2", "User 2", hikari.Member)
@lightbulb.command("equality-test", "Test equality of member objects", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def equality_test(ctx: lightbulb.Context, user1: hikari.Member, user2: hikari.Member) -> None:
    check = user1 == user2
    if check:
        await ctx.respond("Users are the same")
    else:
        await ctx.respond("Users are not the same")

@bot.command
@lightbulb.option("index", "Pool index for population operation", int)
@lightbulb.option("userlist", "List of users to populate pool with", str)
@lightbulb.command("populate-pool", "Fill a created pool with users", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def populate_pool(ctx: lightbulb.Context, index: int, userlist: str) -> None:
    
    if int(index) not in pools:
        await ctx.respond("Command populate-pool failed due to an invalid index.")
        return
    
    userlist_processed = await process_user_list(userlist)
    await populate_pool_backend(int, userlist_processed)
    
    
@bot.command
@lightbulb.option("userlist", "List of users to populate created pool with", str)
@lightbulb.command("create-and-populate", "Wrapper command for create-new-pool and populate-pool together", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def create_and_populate(ctx: lightbulb.Context, userlist: str) -> int:
    userlist_processed = await process_user_list(userlist)
    ID = await create_and_populate_backend(userlist_processed)
    await ctx.respond(f"Created and populated pool {ID}")
    #return ID
    
@bot.command
@lightbulb.option("index", "Index of the pool to delete", int)
@lightbulb.command("delete-pool", "Delete a pool", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def delete_pool(ctx: lightbulb.Context, index: int) -> None:
    if int(index) not in pools:
        await ctx.respond("delete-pool failed due to an invalid index.")
        return
        
    pools.pop(int(index))

@bot.command
@lightbulb.option("index", "Index of the pool to add user to", int)
@lightbulb.option("user", "User to add to pool", hikari.Member)
@lightbulb.command("add-user-to-pool", "Add a user to a pool", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def add_user_to_pool(ctx: lightbulb.Context, index: int, user: hikari.Member) -> None:
    if int(index) not in pools:
        await ctx.respond("add-user-to-pool failed due to an invalid index.")
        return
    
    await add_user_to_pool_backend(index, user)

"""
@bot.command
@lightbulb.option("index", "Index of the pool to view the mapping of", int)
@lightbulb.command("view-pool-mapping", "View the mapping of indices to users for a pool", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def view_pool_mapping(ctx: lightbulb.Context, index: int) -> None:
    if int(index) not in pools:
        await ctx.respond("view-pool-mapping failed due to an invalid index.")
        return
        
    if config["output"] == "console" or config["output"] == "both":
        print(f"Viewing pool mapping #{index}: {user_maps[int(index)]}")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.respond(f"Viewing pool #{index}: {user_maps[int(index)]}")
"""

@bot.command
@lightbulb.option("index", "Index of the pool to view", int)
@lightbulb.command("view-pool", "View a pool", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def view_pool(ctx: lightbulb.Context, index: int) -> None:
    if int(index) not in pools:
        await ctx.respond("view-pool failed due to an invalid index.")
        return
        
    if config["output"] == "console" or config["output"] == "both":
        print(f"Viewing pool #{index}: {pools[int(index)]}")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.respond(f"Viewing pool #{index}: {pools[int(index)]}")

@bot.command
@lightbulb.command("view-all-pools", "View all of the created pools")
@lightbulb.implements(lightbulb.SlashCommand)
async def view_all_pools(ctx: lightbulb.Context) -> None:
    if config["output"] == "console" or config["output"] == "both":
        print(f"{len(pools)} total active pools- Printing them, if applicable:")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.respond(f"{len(pools)} total active pools- Printing them, if applicable:")
    for key in pools.keys():
        if config["output"] == "console" or config["output"] == "both":
            print(f"pool #{key} = {pools[key]}")
        if config["output"] == "channel" or config["output"] == "both":
            await ctx.respond(f"pool #{key} = {pools[key]}")
        
@bot.command
@lightbulb.option("index", "Index of the pool to generate pairings for", int)
@lightbulb.command("generate-pairings-for-pool", "Generate Secret Santa Pairings for a pool", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def generate_pairings_for_pool(ctx: lightbulb.Context, index: int) -> None:
    if int(index) not in pools:
        await ctx.respond("generate-pairings-for-pool failed due to an invalid index.")
        return
        
    if not pools[index]:
        await ctx.respond("generate-pairings-for-pool failed due to an empty pool.")
        return
    
    await generate_pairings_for_pool_backend(index)
    
    if config["output"] == "console" or config["output"] == "both":
        print(f"Generated the following pairings for pool #{index}: {pairings[int(index)]}")
    if config["output"] == "channel" or config["output"] == "both":
        await ctx.respond(f"Generated the following pairings for pool #{index}: {pairings[int(index)]}")

@bot.command
@lightbulb.option("user", "User to message", hikari.User)
@lightbulb.option("user2", "User to message about", hikari.User)
@lightbulb.command("message-test", "Message Test Function", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def message_test(ctx: lightbulb.Context, user: hikari.User, user2: hikari.User) -> None:
    await user.send(f"Test: {user2}")

@bot.command
@lightbulb.option("index", "Index of the pool to report the pairings for", int)
@lightbulb.command("report-pairings-to-users", "Report Generated Pairings to users", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def report_pairings_to_users(ctx: lightbulb.Context, index: int) -> None:
    if int(index) not in pairings:
        await ctx.respond("reportPairingsToUsers failed due to an invalid index")
        return
    
    await report_pairings_to_users_backend(ctx, index)

@bot.command
@lightbulb.option("userlist", "List of users to run the secret santa program on", str)
@lightbulb.command("run-secret-santa", "Run the secret santa pairing generator for provided user list", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def run_secret_santa(ctx: lightbulb.Context, userlist: str) -> None: #Take in all users and do all the back end stuff
    #userlist = [] # Need to parse parameter list into users
    userlist_processed = await process_user_list(userlist)
    ID = await create_and_populate_backend(userlist_processed)
    await generate_pairings_for_pool_backend(ID)
    await report_pairings_to_users_backend(ctx, ID)
       
@bot.command()
@lightbulb.command("exit_", "Shut down the bot")
@lightbulb.implements(lightbulb.SlashCommand)
async def exit_(ctx: lightbulb.Context) -> None:
    await bot.close()
                
bot.run()    