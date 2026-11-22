EMOJIS = {
    "tickets": {
        "close": "<:close:1548269230435209267>",
        "ticket": "<:ticket:1547991426497773688>",
    },
    "voice": {
        "join": "<:voice_join:1548270949739139093>",
        "leave": "<:voice_leave:1548270996287660072>",
        "temp": "<:temp_voice:1548269174453829712>",
        "support_join": "<:support_voice_join:1548270949739139093>",
    },
    "notifier": {
        "bell": "<a:notif_bell:1548269105642209291>",    
        "hash": "<:notif_hash:1548269195844915201>",    
        "person": "<:notif_person:1548269516675620965>",  
        "clock": "<:notif_clock:1548284144025473054>",    
        "check": "<:notif_check:1548269957039525918>",  
    },
"giveaway": {
    "giveaway":      "<:giveaway:1548270051973660713>",
    "join":          "<:gw_join:1548270949739139093>",
    "leave":         "<:gw_leave:1548270996287660072>",
    "info":          "<:gw_info:1548269461575041054>",
    "edit":          "<:gw_edit:1548269333170491432>",
    "reroll":        "<a:gw_reroll:1547988405647052821>",
    "end":           "<aa:gw_end:1548269566659002479>",
    "participants":  "<:gw_participants:1548269516675620965>",
    "winner":        "<a:gw_winner:1548269804647874651>",
    "prize":         "<a:gw_prize:1547988783138603108>",
    "host":          "<:gw_host:1548269195844915201>",
    "winners_count": "<:gw_winners:1548270973285957662>",
    "entries":       "<:gw_entries:1548270949739139093>",
    "time":          "<:gw_time:1548284144025473054>",
    "id":            "<:gw_id:1548269398287192084>",
    "role":          "<:gw_role:1548271024410198056>",
    "add_member":    "<:gw_add_member:1548269852748152922>",  
    },
    "invites": {
        "invites":  "<:invites:1548270973285957662>",  
        "joined":   "<:inv_joined:1548270949739139093>", 
        "left":     "<:inv_left:1548270996287660072>",   
        "leaderboard": "<:inv_board:1548269426506465340>", 
    },
}


def emoji(category: str, name: str) -> str:
    try:
        return EMOJIS[category][name]
    except KeyError:
        return ""
