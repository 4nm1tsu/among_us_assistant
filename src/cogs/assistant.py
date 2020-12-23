from typing import List, Optional

import discord
import matplotlib.pyplot as plt
import networkx as nx
from discord.ext import commands
from error import DuplicateRoleError, NotAttendeeError, NoSuchRelationError, SpecifyYourselfError
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


def get_error_embed(error: str) -> discord.Embed:
    embed = discord.Embed(title=":x:Error", description=error, color=0xFF0000)
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
    if not second_role:
        # 引数1つかつ自分がnot attendee → author
        if not source:
            role = [i for i in ctx.author.roles if i.name !=
                    "@everyone" and i.name != "attendees"][0]
            raise NotAttendeeError(role.name)
    # 引数1つかつ相手がnot attendee → first_role
        if not target:
            raise NotAttendeeError(first_role.name)
    else:
        # 引数2つかつ自分がnot attendee → first_role
        if not source:
            raise NotAttendeeError(first_role.name)
    # 引数2つかつ相手がnot attendee → second_role
        if not target:
            raise NotAttendeeError(second_role.name)
    if source == target:
        raise SpecifyYourselfError()
    return [source, target]


def create_statistics(ctx, limit=3):
    result = []
    for i, player in enumerate(G.nodes):
        result.append({
            "name": player.name,
            "role": player.color,
            "doubt": 0,
            "trust": 0
        })
        for e in G.in_edges(player):
            if relations[e] == DOUBT:
                result[i]["doubt"] += 1
            else:
                result[i]["trust"] += 1
    doubt_sorted = sorted(result, key=lambda x: x["doubt"], reverse=True)
    trust_sorted = sorted(result, key=lambda x: x["trust"], reverse=True)
    doubt_formatted = []
    trust_formatted = []
    for i, d in enumerate(doubt_sorted):
        if i >= limit:
            break
        emoji = discord.utils.get(ctx.guild.emojis, name=d['role'])
        doubt_formatted.append(f"{i+1}:{emoji}{d['name']}[{d['doubt']}]")
    for i, t in enumerate(trust_sorted):
        if i >= limit:
            break
        emoji = discord.utils.get(ctx.guild.emojis, name=t['role'])
        trust_formatted.append(f"{i+1}:{emoji}{t['name']}[{t['trust']}]")
    return [doubt_formatted, trust_formatted]


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

    @commands.command(brief="take stats.")
    async def stat(self, ctx, *args):
        [doubt_formatted, trust_formatted] = create_statistics(ctx)
        embed = discord.Embed(
            title=":chart_with_upwards_trend:statistics", color=0x359cad)
        embed.add_field(name=":detective:doubtful",
                        value="\n".join(doubt_formatted), inline=True)
        embed.add_field(name=":man_tipping_hand:innocent",
                        value="\n".join(trust_formatted), inline=True)
        await ctx.send(embed=embed)
        return

    @commands.group(pass_context=True, invoke_without_command=True, brief="remove arrow from graph.")
    async def clear(self, ctx, first_role: discord.Role, second_role: discord.Role = None):
        [source, target] = await parse_attendee(ctx, first_role, second_role)
        try:
            del relations[(players[source], players[target])]
        except:
            raise NoSuchRelationError
        await ctx.send(file=draw_graph())
        return

    @clear.group(brief="remove all nodes and arrows.")
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

    @commands.command(brief="draw trust arrow to specified target.")
    async def trust(
        self, ctx: commands.Context, first_role: discord.Role, second_role: discord.Role = None
    ):
        try:
            await draw_relation(ctx, first_role, second_role, TRUST)
        except Exception as e:
            raise e
        return

    @commands.command(brief="draw doubt arrow to specified target.")
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
        else:
            await ctx.send(embed=get_error_embed(str(error)))
            print(ctx.invoked_with)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Assistant(bot))
