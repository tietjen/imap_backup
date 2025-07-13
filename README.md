
# Email Fetcher and Search Tool

This is a command-line tool for fetching emails from an IMAP server and searching them locally.

## Features

- Fetch emails from one or more accounts on an IMAP server using TLS.
- Store emails locally in the EML format, mirroring the IMAP folder structure.
- Fetch all emails, emails since a specific date, or only new emails since the last fetch.
- Search for emails by subject, sender, recipient, content, and attachment name.
- Configuration is managed through a `config.yml` file.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd email_tool
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## Configuration

1.  Rename `config.example.yml` to `config.yml`.
2.  Edit `config.yml` with your IMAP server details and user credentials.

    ```yaml
    imap_server: "imap.example.com"
    port: 993
    tls: true
    storage_directory: "./emails"
    users:
      - username: "user1@example.com"
        password: "your_password"
      - username: "user2@example.com"
        password: "another_password"
    ```

## Usage

### Fetching Emails

-   **Fetch all emails for all users:**
    ```bash
    python main.py fetch --all
    ```

-   **Fetch emails received since a specific date:**
    ```bash
    python main.py fetch --since "2023-01-01"
    ```

-   **Fetch new emails since the last run:**
    ```bash
    python main.py fetch --new
    ```

### Searching Emails

You must fetch emails at least once before you can search.

-   **Search by subject:**
    ```bash
    python main.py search --subject "Important"
    ```

-   **Search by sender:**
    ```bash
    python main.py search --from "boss@example.com"
    ```

-   **Search by recipient:**
    ```bash
    python main.py search --to "me@example.com"
    ```

-   **Search by content:**
    ```bash
    python main.py search --content "project update"
    ```

-   **Search by attachment filename:**
    ```bash
    python main.py search --attachment "report.pdf"
    ```

-   **Combine search criteria:**
    ```bash
    python main.py search --from "boss@example.com" --subject "urgent"
    ```

