import asyncio
import socket
from copy import copy

from cloudbot import hook

socket.setdefaulttimeout(10)


# Auto-join on Invite (Configurable, defaults to True)
@hook.irc_raw('INVITE')
@asyncio.coroutine
def invite(irc_paramlist, conn):
    """
    :type irc_paramlist: list[str]
    :type conn: cloudbot.client.Client
    """
    invite_join = conn.config.get('invite_join', True)
    chan = irc_paramlist[-1]
    if chan.startswith(':'):
        chan = chan[1:]

    if invite_join:
        conn.join(chan)


@hook.irc_raw('JOIN')
def on_join(chan, conn, nick):
    if conn.nick.casefold() == nick.casefold():
        conn.cmd("MODE", chan)


@hook.irc_raw('324')
def check_mode(irc_paramlist, conn, message):
    # message(", ".join(irc_paramlist), "bloodygonzo")
    mode = irc_paramlist[2]
    require_reg = conn.config.get('require_registered_channels', False)
    if "r" not in mode and require_reg:
        message("I do not stay in unregistered channels", irc_paramlist[1])
        conn.part(irc_paramlist[1])


@hook.irc_raw('MODE')
def on_mode_change(conn, irc_paramlist, message):
    require_reg = conn.config.get('require_registered_channels', False)
    chan = irc_paramlist[0]
    modes = irc_paramlist[1]
    new_modes = {}
    adding = True
    for c in modes:
        if c == '+':
            adding = True
        elif c == '-':
            adding = False
        else:
            new_modes[c] = adding

    if chan[0] == '#' and require_reg and not new_modes.get("r", True):
        message("I do not stay in unregistered channels", chan)
        conn.part(chan)


# Identify to NickServ (or other service)
@hook.irc_raw('004')
@asyncio.coroutine
def onjoin(conn, bot):
    """
    :type conn: cloudbot.clients.clients.IrcClient
    :type bot: cloudbot.bot.CloudBot
    """
    bot.logger.info("[{}|misc] Bot is sending join commands for network.".format(conn.name))
    nickserv = conn.config.get('nickserv')
    if nickserv and nickserv.get("enabled", True):
        bot.logger.info("[{}|misc] Bot is authenticating with NickServ.".format(conn.name))
        nickserv_password = nickserv.get('nickserv_password', '')
        nickserv_name = nickserv.get('nickserv_name', 'nickserv')
        nickserv_account_name = nickserv.get('nickserv_user', '')
        nickserv_command = nickserv.get('nickserv_command', 'IDENTIFY')
        if nickserv_password:
            if "censored_strings" in bot.config and nickserv_password in bot.config['censored_strings']:
                bot.config['censored_strings'].remove(nickserv_password)
            if nickserv_account_name:
                conn.message(nickserv_name, "{} {} {}".format(nickserv_command,
                                                              nickserv_account_name, nickserv_password))
            else:
                conn.message(nickserv_name, "{} {}".format(nickserv_command, nickserv_password))
            if "censored_strings" in bot.config:
                bot.config['censored_strings'].append(nickserv_password)
            yield from asyncio.sleep(1)

    # Should we oper up?
    oper_pw = conn.config.get('oper_pw', False)
    oper_user = conn.config.get('oper_user', False)
    if oper_pw and oper_user:
        out = "oper {} {}".format(oper_user, oper_pw)
        conn.send(out)

    # Set bot modes
    mode = conn.config.get('mode')
    if mode:
        bot.logger.info("[{}|misc] Bot is setting mode on itself: {}".format(conn.name, mode))
        conn.cmd('MODE', conn.nick, mode)

    conn.ready = True
    bot.logger.info("[{}|misc] Bot has finished sending join commands for network.".format(conn.name))


@hook.irc_raw('376')
@asyncio.coroutine
def do_joins(logger, conn):
    chans = copy(conn.channels)

    # Join config-defined channels
    join_throttle = conn.config.get('join_throttle', 0.4)
    logger.info("[%s|misc] Bot is joining channels for network.", conn.name)
    for channel in chans:
        conn.join(channel)
        yield from asyncio.sleep(join_throttle)


@hook.irc_raw('004')
@asyncio.coroutine
def keep_alive(conn):
    """
    :type conn: cloudbot.clients.clients.IrcClient
    """
    keepalive = conn.config.get('keep_alive', False)
    if keepalive:
        while True:
            conn.cmd('PING', conn.nick)
            yield from asyncio.sleep(60)


@hook.irc_raw('433')
def on_nick_in_use(conn, irc_paramlist):
    conn.nick = irc_paramlist[1] + '_'
    conn.cmd("NICK", conn.nick)


@hook.irc_raw('432', singlethread=True)
@asyncio.coroutine
def on_invalid_nick(conn):
    nick = conn.config['nick']
    conn.nick = nick
    conn.cmd("NICK", conn.nick)
    yield from asyncio.sleep(30)  # Just in case, we make sure to wait at least 30 seconds between sending this
