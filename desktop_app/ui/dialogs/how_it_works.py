# file: desktop_app/ui/dialogs/how_it_works.py
from PySide6.QtWidgets import QMessageBox

def show_info(parent=None):
    QMessageBox.information(
        parent,
        "How it works",
        (
            "🧭 **How WoW Arena Notify works:**\n\n"
            "The 'QueuePopNotify' addon triggers an in-game event when your arena queue pops.\n"
            "This desktop app listens for that event and starts a visual countdown timer.\n\n"
            "It uses WoW’s built-in screenshot system internally, limited to the game window.\n"
            "Default countdown is 40 seconds (minus 4 for quicker entry), "
            "but you can adjust it if your server uses a different timer."
        ),
    )
