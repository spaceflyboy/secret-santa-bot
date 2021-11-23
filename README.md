# secret-santa-bot
Secret Santa Discord Bot written in Python. 

._help for list of commands

only undocumented command is setOutput, which can enable output from certain commands going to more than just the default option of the console which you run the bot from. Available options are "channel", "console", or "both". "channel" and "both" require the bot to be given permissions to send messages in a channel or otherwise the await command that does the send to print to that channel will raise a discord.errors.Forbidden: 403 Missing Permissions Error with an error code I can't remember.
