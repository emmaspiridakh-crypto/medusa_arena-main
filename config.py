import os
from dotenv import load_dotenv

load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1569809099351265320
PREFIX = "!"

OWNERSHIP_ROLE_ID        = 1573491553471565955
MANAGER_ROLE_ID          = 1569809099388883004
STAFF_ROLE_ID            = 1569809099368177791
CRIMINAL_MANAGER_ROLE_ID = 1569809099388883002
DONATE_MANAGER_ROLE_ID   = 1569809099393204379
OWNER_ROLE_ID          =  1569809099393204382
STAFF_MANAGER_ID         = 1569809099388883003
EVENT_MANAGER_ID = 1569809099388882998
GENERAL_MANAGER_ID = 1569809099393204376
ANTICHEAT_MANAGER_ROLE_ID = 1569809099376304197
STAFF_TEAM_ROLE_IDS = [STAFF_ROLE_ID, MANAGER_ROLE_ID, OWNERSHIP_ROLE_ID]

TICKET_SUPPORT_CHANNEL_ID = 1569809101855264854

# ---------- Tickets ----------
TICKET_SUPPORT_BANNER_URL = "https://i.imgur.com/ldREUJB.jpeg"   # banner του ticket panel
TICKET_PANEL_COLOUR = 0x9500FF
TICKET_THUMBNAIL_URL = "https://i.imgur.com/JcB78UI.png"   # logo μέσα στο ticket (medusa_logo)
MAX_OPEN_TICKETS_PER_USER = 1   # πόσα ανοιχτά tickets μπορεί να έχει ο κάθε χρήστης

# Category (Discord) που θα μπαίνουν τα tickets κάθε τύπου.
# Όπου έχει 0 -> ΒΑΛΕ το ID του category. Μέχρι τότε πέφτουν στο category του "other".
TICKET_CATEGORY_IDS = {
    "owner":            1569809101545017354,
    "ban_appeal":       1569809101545017357,   # TODO: βάλε category ID
    "staff_report":     1569809101545017356,
    "bug_report":       1569809101545017359,   # TODO: βάλε category ID
    "other":            1569809101545017355,
    "criminal_support": 1573837602145046681,   # TODO: βάλε category ID
}

# Ποιοι ρόλοι βλέπουν τα tickets κάθε τύπου.
TICKET_VIEW_ROLE_IDS = {
    "owner":            [OWNERSHIP_ROLE_ID],
    "ban_appeal":       [MANAGER_ROLE_ID, OWNERSHIP_ROLE_ID],
    "staff_report":     [STAFF_MANAGER_ID, OWNERSHIP_ROLE_ID],
    "bug_report":       [DEVELOPER_ROLE_ID, OWNERSHIP_ROLE_ID],
    "other":            STAFF_TEAM_ROLE_IDS,
    "criminal_support": [CRIMINAL_MANAGER_ROLE_ID, OWNERSHIP_ROLE_ID],
}

TEMP_VOICE_COOLDOWN_SECONDS = 30   # ανά χρήστη, για να μην γίνεται spam με μπαινοβγαίνουν

TEMP_VOICE_TYPES = {
    "support": {
        "label": "Support",
        "hub_channel_id": 1569809101855264853,
        "category_id": 1573492525891592343,           # TODO: category όπου φτιάχνονται τα temp voices (0 = ίδιο category με το hub)
        "notify_channel_id": 1569809101855264855,
        "ping_role_id": STAFF_ROLE_ID,
    },
    "donate": {
        "label": "Donate",
        "hub_channel_id": 1569809101343555792,        # TODO
        "category_id": 1573876024352186468,           # TODO: category όπου φτιάχνονται τα temp voices (0 = ίδιο category με το hub)
        "notify_channel_id": 1569809101343555796,     # TODO
        "ping_role_id": DONATE_MANAGER_ROLE_ID,
    },
    "anticheat": {
        "label": "Anticheat",
        "hub_channel_id": 1569809102157258863,        # TODO
        "category_id": 1573875614107046018,           # TODO: category όπου φτιάχνονται τα temp voices (0 = ίδιο category με το hub)
        "notify_channel_id": 1573876283555971074,     # TODO
        "ping_role_id": ANTICHEAT_MANAGER_ROLE_ID,
    },
    "event": {
        "label": "Event",
        "hub_channel_id": 1569809102157258863,        # TODO
        "category_id": 1573875501112762378,           # TODO: category όπου φτιάχνονται τα temp voices (0 = ίδιο category με το hub)
        "notify_channel_id": 1573876283555971074,     # TODO
        "ping_role_id": EVENT_MANAGER_ROLE_ID,
    },
}
STAFF_PING_CHANNEL_ID = 1569809101855264855

LOG_TICKETS_CHANNEL_ID =  1569809100416487632
TICKET_NOTIFIER_CHANNEL_ID = 1573866150968819822

SUGGESTIONS_CHANNEL_ID = 1569809101687357446

SUPPORT_VOICE_CHANNEL_ID = 1569809101855264856

SUPPORT_VOICE_NOTIFIER_CHANNEL_ID = 1569809101855264855
SUPPORT_VOICE_PING_ROLE_ID = 1569809099368177791

INVITE_LOG_CHANNEL_ID =  1569809100416487628

LOG_GIVEAWAY_CHANNEL_ID =  1573866659200897034
GIVEAWAY_BANNER_URL = "https://i.imgur.com/ldREUJB.jpeg" 

EMBED_COLOR = int(os.getenv("EMBED_COLOR", "A600FF"), 16)
