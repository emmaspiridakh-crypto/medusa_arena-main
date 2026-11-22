EMOJIS = {
    "notifier": {
        "bell": "<:notif_bell:1573740024061501563>",
        "hash": "<:notif_hash:1573362868899024966>",
        "person": "<:notif_person:1573453974063816876>",
        "clock": "<:notif_clock:1573362872363385003>",
    },
    "giveaway": {
        "giveaway": "<:giveaway:1573364428504563753>",
        "join": "<:gw_join:1574115300239085578>",
        "leave": "<:gw_leave:1574115328001314957>",
        "info": "<:gw_info:1573362868899024966>",
        "edit": "<:gw_edit:1573362885181177926>",
        "reroll": "<:gw_reroll:1573490238955724840>",
        "end": "<a:gw_end:1572697810254438451>",
        "participants": "<:gw_participants:1573453974063816876>",
        "winner": "<:gw_winner:1573740034887000176>",
        "prize": "<:gw_prize:1573364431084191857>",
        "host": "<:gw_host:1573454146017824779>",
        "winners_count": "<:gw_winners:1572698303810904114>",
        "entries": "<:gw_entries:1574115300239085578>",
        "time": "<:gw_time:>1573362872363385003",
        "role": "<:gw_role:1573362858635427992>",
        "add_member": "<:gw_add_member:1573868557031444581>",
    },
    "invites": {
        "invites": "<a:invites:1572696336195919943>",
        "joined": "<:inv_joined:1574115300239085578>",
        "left": "<:inv_left:1574115328001314957>",
        "leaderboard": "<:inv_board:1573362858635427992>",
    },
}


def emoji(category: str, name: str) -> str:
    try:
        return EMOJIS[category][name]
    except KeyError:
        return ""
