#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

MYSQLD="/opt/homebrew/opt/mysql/bin/mysqld"
MYSQL_DATA="/tmp/mysql_data"
MYSQL_PORT=3307
MYSQL_SOCKET="/tmp/mysql_evs.sock"

# Start MySQL if not already running on port 3307
if ! lsof -P -iTCP:$MYSQL_PORT -sTCP:LISTEN &>/dev/null; then
    echo "Starting MySQL on port $MYSQL_PORT..."
    if [ ! -d "$MYSQL_DATA/mysql" ]; then
        echo "Initializing MySQL data directory..."
        "$MYSQLD" --initialize-insecure --basedir=/opt/homebrew/opt/mysql \
            --datadir="$MYSQL_DATA" --user=mubashirali
    fi
    nohup "$MYSQLD" --basedir=/opt/homebrew/opt/mysql --datadir="$MYSQL_DATA" \
        --port=$MYSQL_PORT --socket="$MYSQL_SOCKET" --skip-mysqlx \
        > /tmp/mysql_evs.log 2>&1 &
    sleep 3
    echo "MySQL started."
fi

# Run the app
echo "Starting Electronic Voting System..."
/usr/local/bin/python3 "$DIR/app.py"
