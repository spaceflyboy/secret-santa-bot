import lightbulb
import hikari
import random
import tokenfile

bot = lightbulb.BotApp(token=tokenfile.token, prefix=".")

pools = {}
pairings = {}

user_maps = {} # Map pool id to a map of user id to user objects (complicated but necessary, I think)


#output options: console, discord channel where command sent, both
config = {"output": "both"}

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
      
@bot.command
@lightbulb.option("userlist", "List of users to run the secret santa program on", str)
@lightbulb.command("run-secret-santa", "Run the secret santa pairing generator for provided user list", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def run_secret_santa(ctx: lightbulb.Context, userlist: str) -> None: #Take in all users and do all the back end stuff
    #userlist = [] # Need to parse parameter list into users
    userlist_processed = await process_user_list(userlist)
    ID = await create_and_populate_backend(userlist_processed)
    await generate_pairings_for_pool_backend(ID)
    await report_pairings_to_users_backend(ID)

async def create_and_populate_backend(userlist: list) -> int:
    ID = await create_new_pool_backend()
    await populate_pool_backend(ID, userlist)
    return ID

async def generate_pairings_for_pool_backend(index: int) -> None:
    local_pairs = {}
    
    cur_pool = pools[int(index)]
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

async def create_new_pool_backend() -> int:
    returnPool = len(pools)
    pools[returnPool] = list()
    user_maps[returnPool] = dict()
    return returnPool

async def add_user_to_pool_backend(index: int, user) -> None:
    cur_pool = pools[int(index)].copy()
    newID = len(cur_pool)
    user_maps[int(index)][newID] = user
    cur_pool.append(newID)
    pools[int(index)] = cur_pool

async def populate_pool_backend(index: int, userlist: list) -> None:
    for user in userlist:
        await add_user_to_pool_backend(index, user)
        
async def process_user_list(ctx: lightbulb.Context, userlist: str) -> list[hikari.User]:
    result = []
    for user_id in userlist.split(" "):
        memberObject = await lightbulb.converters.special.MemberConverter(ctx).convert(user_id)
        result.append(memberObject)
    return result

#async def report_pairings_to_users_backend(index: int):

# Make sure that the userlist provided only contains actual user objects
# async def user_list_sanity_check(userlist: list):

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
@lightbulb.option("index", "Pool index for population operation", int)
@lightbulb.option("userlist", "List of users to populate pool with", str)
@lightbulb.command("populate-pool", "Fill a created pool with users", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def populate_pool(ctx: lightbulb.Context, index: int, userlist: str) -> None:
    
    if int(index) not in pools:
        await ctx.respond("Command populate-pool failed due to an invalid index.")
        return
    
    userlist_processed = await process_user_list(ctx, userlist)
    await populate_pool_backend(int, userlist_processed)
    
    
@bot.command
@lightbulb.option("userlist", "List of users to populate created pool with", str)
@lightbulb.command("create-and-populate", "Wrapper command for create-new-pool and populate-pool together", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def create_and_populate(ctx: lightbulb.Context, userlist: str) -> int:
    userlist_processed = await process_user_list(ctx, userlist)
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
@lightbulb.option("user", "User to add to pool", hikari.User)
@lightbulb.command("add-user-to-pool", "Add a user to a pool", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def add_user_to_pool(ctx: lightbulb.Context, index: int, user: hikari.User) -> None:
    if int(index) not in pools:
        await ctx.respond("add-user-to-pool failed due to an invalid index.")
        return
    
    await add_user_to_pool_backend(index, user)

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
        
    #cur_pool = pools[index]
    local_pairs = pairings[int(index)]
    #converter = MemberConverter()
   
    for user_id in local_pairs.keys():
        print(f"user_id = {user_id}")
        print(f"receiver_id = {local_pairs[user_id]}")
        user = user_maps[int(index)][user_id]
        
        #print(f"local_pairs = {local_pairs}")
        #print(f"user = {user}")
        #print(f"receiver_id = {local_pairs[user_id]}")
        #print(f"user_maps[{index}] = {user_maps[index]}")
        #report local_pairs[user] to each user
        #giver = await converter.convert(ctx, user)
        #receiver = await converter.convert(ctx, local_pairs[user])
        #channel = await giver.create_dm()
        await user.send(f"You are secret santa for {user_maps[int(index)][local_pairs[user_id]]}")
        
@bot.command()
@lightbulb.command("exit_", "Shut down the bot")
@lightbulb.implements(lightbulb.SlashCommand)
async def exit_(ctx: lightbulb.Context) -> None:
    await bot.close()
                
bot.run()    