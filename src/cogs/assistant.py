from typing import List, Optional

import discord
import matplotlib.pyplot as plt
import networkx as nx
from discord.ext import commands
from error import DuplicateRoleError, NotAttendeeError, NoSuchRelationError
from networkx.drawing.nx_agraph import graphviz_layout


class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Player):
            return NotImplemented
        return self is other


USAGE_DOUBT = "/doubt {source(optional)} {target}"
USAGE_TRUST = "/trust {source(optional)} {target}"
USAGE_CLEAR = "/clear [all|{source (optional)} {target}]"

ERROR_ROLE_NOT_FOUND = "role not found."
ERROR_DUPLICATE_ROLE = "duplicate role."
ERROR_TOO_FEW_ARGUMENTS = "too few arguments."
ERROR_TOO_MANY_ARGUMENTS = "too many arguments."
ERROR_NOT_ATTENDEE = "specified member is not attendee."
ERROR_BAD_ARGUMENT = "bad argument."
ERROR_COMMAND_INVOKE = "command invoke error."

TRUST = 0
DOUBT = 1

G = nx.DiGraph()
players = {}  # {discord.Member: Player}
relations = {}  # {(Player, Player): int}
members = []
attendees = []
plt.style.use("grey")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Hiragino Maru Gothic Pro",
    "Yu Gothic",
    "Meirio",
    "Takao",
    "IPAexGothic",
    "IPAPGothic",
    "VL PGothic",
    "Noto Sans CJK JP",
]


def node_color(player: Player) -> str:
    """
    ノードカラーのマッピング
    """
    if player.color == "red":
        return "red"
    if player.color == "blue":
        return "blue"
    if player.color == "yellow":
        return "yellow"
    if player.color == "pink":
        return "fuchsia"
    if player.color == "green":
        return "green"
    if player.color == "lime":
        return "lime"
    if player.color == "brown":
        return "saddlebrown"
    if player.color == "white":
        return "whitesmoke"
    if player.color == "purple":
        return "purple"
    if player.color == "cyan":
        return "cyan"
    if player.color == "black":
        return "dimgrey"
    if player.color == "orange":
        return "orange"
    return "black"


def edge_color(relation: int) -> str:
    """
    エッジカラーのマッピング
    """
    if relation == DOUBT:
        return "red"
    if relation == TRUST:
        return "cyan"
    return "black"


def draw_graph() -> discord.File:
    """
    グラフ描画
    """
    plt.clf()
    edges = []
    for r in relations.keys():
        edges.append(r)
    nodes = []
    for p in players.values():
        nodes.append(p)
    G.add_nodes_from(nodes)
    for p in players.values():
        if len([i for i in nx.neighbors(G, p)]) == 0:
            G.remove_node(p)
    G.add_edges_from(edges)
    options = {
        "node_color": [node_color(player) for player in G.nodes()],
        "edge_color": [edge_color(relation) for relation in relations.values()],
        "node_size": 800,
        "width": 2,
        "arrowstyle": "-|>",
        "arrowsize": 20,
    }
    pos = graphviz_layout(G, prog="fdp")
    nx.draw_networkx(
        G, pos, connectionstyle="arc3, rad=0.1", arrows=True, **options, font_size=14
    )
    plt.tight_layout(pad=0)
    plt.savefig("figure.png")
    return discord.File("figure.png")


def get_usage(usage: str, error: str = None) -> discord.Embed:
    if error:
        embed = discord.Embed(title="Error", description=error, color=0xFF0000)
        embed.add_field(name="usage", value=usage)
    else:
        embed = discord.Embed(title="usage", description=usage, color=0x00FF00)
    return embed


def is_attendee(member: discord.Member) -> bool:
    for r in member.roles:
        if r.name == "attendees":
            return True
    return False


def add_relation(
    source: Optional[discord.Member], target: Optional[discord.Member], type: int
) -> None:
    s = players[source]
    t = players[target]
    relations[(s, t)] = type


def find_attendee_by_role(
    attendees: List[discord.Member], role_name: str
) -> Optional[discord.Member]:
    attendee = None
    for a in attendees:
        for r in a.roles:
            if role_name == r.name:
                attendee = a
    return attendee


async def parse_attendee(
    ctx: commands.Context,
    first_role: discord.Role,
    second_role: Optional[discord.Role] = None
):
    if first_role == second_role:
        raise DuplicateRoleError
    members = [i async for i in ctx.guild.fetch_members(limit=150) if not i.bot]
    attendees = [i for i in members if is_attendee(i)]
    for a in attendees:
        role = [i for i in a.roles if i.name !=
                "@everyone" and i.name != "attendees"][0]
        if not players.get(a):
            players[a] = Player(a.name, role.name)
    if not second_role:
        source: Optional[discord.Member] = discord.utils.find(
            lambda m: m.name == ctx.author.name, attendees
        )
        target: Optional[discord.Member] = find_attendee_by_role(
            attendees, first_role.name
        )
    else:
        source: Optional[discord.Member] = find_attendee_by_role(
            attendees, first_role.name
        )
        target: Optional[discord.Member] = find_attendee_by_role(
            attendees, second_role.name
        )
    if not source or not target:
        raise NotAttendeeError
    return [source, target]


async def draw_relation(
    ctx: commands.Context,
    first_role: discord.Role,
    second_role: Optional[discord.Role],
    relation_type: int,
):
    try:
        [source, target] = await parse_attendee(ctx, first_role, second_role)
    except Exception as e:
        raise e
    add_relation(source, target, relation_type)
    await ctx.send(file=draw_graph())
    return


class Assistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def name(self, ctx, *args):
        pass

    @commands.group(pass_context=True, invoke_without_command=True)
    async def clear(self, ctx, first_role: discord.Role, second_role: discord.Role = None):
        [source, target] = await parse_attendee(ctx, first_role, second_role)
        try:
            del relations[(players[source], players[target])]
        except:
            raise NoSuchRelationError
        await ctx.send(file=draw_graph())
        return

    @clear.group()
    async def all(self, ctx):
        global players
        global relations
        G.clear()
        plt.clf()
        players = {}
        relations = {}
        embed = discord.Embed(
            title="clear", description="graph has been cleared", color=0x00FF00
        )
        await ctx.send(embed=embed)
        return

    @commands.command()
    async def trust(
        self, ctx: commands.Context, first_role: discord.Role, second_role: discord.Role = None
    ):
        try:
            await draw_relation(ctx, first_role, second_role, TRUST)
        except Exception as e:
            raise e
        return

    @commands.command()
    async def doubt(
        self, ctx: commands.Context, first_role: discord.Role, second_role: discord.Role = None
    ):
        try:
            await draw_relation(ctx, first_role, second_role, DOUBT)
        except Exception as e:
            raise e
        return

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send_help()

    @doubt.error
    async def doubt_error(self, ctx: commands.Context, error):
        print(type(error))
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=get_usage(USAGE_DOUBT, str(error)))
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(embed=get_usage(USAGE_DOUBT, str(error)))

    @trust.error
    async def trust_error(self, ctx: commands.Context, error):
        print(type(error))
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=get_usage(USAGE_TRUST, str(error)))
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(embed=get_usage(USAGE_TRUST, str(error)))

    @clear.error
    async def clear_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=get_usage(USAGE_CLEAR, str(error)))
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(embed=get_usage(USAGE_CLEAR, str(error)))
    # MissingRequiredArgument


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Assistant(bot))
