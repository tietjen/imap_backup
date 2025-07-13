import typer
import yaml
from pathlib import Path
import datetime
import json
from core.fetcher import Fetcher
from core.parser import EmailParser
from core.indexer import Indexer

app = typer.Typer()

CONFIG_PATH = Path(__file__).parent / "config.yml"
DB_PATH = Path(__file__).parent / ".state/mail_index.db"
STATE_PATH = Path(__file__).parent / ".state/last_run.json"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def load_state():
    if STATE_PATH.exists():
        with open(STATE_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=4)

@app.command()
def fetch(
    all: bool = typer.Option(False, "--all", help="Fetch all emails."),
    since: str = typer.Option(None, "--since", help="Fetch emails since a specific date (YYYY-MM-DD)."),
    new: bool = typer.Option(False, "--new", help="Fetch new emails since last run."),
):
    """
    Fetch emails from the IMAP server and index them.
    """
    config = load_config()
    server = config["imap_server"]
    port = config["port"]
    use_tls = config.get("tls", True)
    storage_dir = Path(config["storage_directory"])

    fetcher = Fetcher(server, port, use_tls)
    indexer = Indexer(DB_PATH)
    state = load_state()
    
    current_run_time = datetime.datetime.now(datetime.timezone.utc)

    for user in config["users"]:
        username = user["username"]
        password = user["password"]
        
        try:
            fetcher.connect()
            fetcher.login(username, password)
            mailboxes = fetcher.list_mailboxes()
            
            for mailbox in mailboxes:
                print(f"Processing mailbox: {mailbox} for user {username}")
                
                criteria = ""
                if all:
                    criteria = "ALL"
                elif since:
                    try:
                        # Format for IMAP: DD-Mon-YYYY
                        since_date = datetime.datetime.strptime(since, "%Y-%m-%d").strftime("%d-%b-%Y")
                        criteria = f'(SINCE "{since_date}")'
                    except ValueError:
                        print("Error: Invalid date format for --since. Please use YYYY-MM-DD.")
                        continue
                elif new:
                    last_run_str = state.get(username, {}).get(mailbox)
                    if last_run_str:
                        last_run_date = datetime.datetime.fromisoformat(last_run_str).strftime("%d-%b-%Y")
                        criteria = f'(SINCE "{last_run_date}")'
                    else:
                        criteria = "ALL" # First time for this user/mailbox, fetch all
                else:
                    print("No fetch option specified. Use --all, --since, or --new.")
                    continue

                print(f"Fetching emails with criteria: {criteria}")
                fetcher.fetch_emails(username, storage_dir, mailbox, criteria)
                
                user_mailbox_dir = storage_dir / username / mailbox
                for eml_file in user_mailbox_dir.glob("*.eml"):
                    try:
                        parser = EmailParser(eml_file)
                        email_data = parser.get_all_parts()
                        indexer.index_email(email_data)
                    except Exception as e:
                        print(f"Could not parse or index {eml_file}: {e}")

                if username not in state:
                    state[username] = {}
                state[username][mailbox] = current_run_time.isoformat()

        except Exception as e:
            print(f"An error occurred for user {username}: {e}")
        finally:
            fetcher.close()

    indexer.close()
    save_state(state)
    print("Fetch and index process complete.")


@app.command()
def search(
    subject: str = typer.Option(None, "--subject", help="Search by subject."),
    from_sender: str = typer.Option(None, "--from", help="Search by sender."),
    to_recipient: str = typer.Option(None, "--to", help="Search by recipient."),
    content: str = typer.Option(None, "--content", help="Search by email content."),
    attachment: str = typer.Option(None, "--attachment", help="Search by attachment name."),
):
    """
    Search for emails in the local index.
    """
    indexer = Indexer(DB_PATH)
    results = indexer.search(subject, from_sender, to_recipient, content, attachment)
    indexer.close()

    if not results:
        print("No matching emails found.")
        return

    print(f"Found {len(results)} matching emails:")
    for row in results:
        print(f"  Path: {row[0]}\n  Subject: {row[1]}\n  From: {row[2]}\n  To: {row[3]}\n")

if __name__ == "__main__":
    app()