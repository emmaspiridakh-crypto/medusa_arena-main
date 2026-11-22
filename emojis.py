EMOJIS = {
    "notifier": {
        "bell": "<a:notif_bell:0>",
        "hash": "<:notif_hash:0>",
        "person": "<:notif_person:0>",
        "clock": "<:notif_clock:0>",
    },
    "giveaway": {
        "giveaway": "<:giveaway:0>",
        "join": "<:gw_join:0>",
        "leave": "<:gw_leave:0>",
        "info": "<:gw_info:0>",
        "edit": "<:gw_edit:0>",
        "reroll": "<a:gw_reroll:0>",
        "end": "<aa:gw_end:0>",
        "participants": "<:gw_participants:0>",
        "winner": "<a:gw_winner:0>",
        "prize": "<a:gw_prize:0>",
        "host": "<:gw_host:0>",
        "winners_count": "<:gw_winners:0>",
        "entries": "<:gw_entries:0>",
        "time": "<:gw_time:0>",
        "role": "<:gw_role:0>",
        "add_member": "<:gw_add_member:0>",
    },
    "invites": {
        "invites": "<:invites:0>",
        "joined": "<:inv_joined:0>",
        "left": "<:inv_left:0>",
        "leaderboard": "<:inv_board:0>",
    },
}


def emoji(category: str, name: str) -> str:
    try:
        return EMOJIS[category][name]
    except KeyError:
        return ""
