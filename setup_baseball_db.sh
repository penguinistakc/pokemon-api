#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="baseball-mysql"
MYSQL_ROOT_PASSWORD="password"
MYSQL_PORT=3306
DATA_DIR="./data/mysql_data"
RAW_DIR="./data/raw"

# ── Pull image ────────────────────────────────────────────────────────
echo "Pulling mysql:latest..."
docker pull mysql:latest

# ── Create persistent storage directory ───────────────────────────────
mkdir -p "$DATA_DIR"

# ── Remove existing container if present ──────────────────────────────
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Removing existing container '${CONTAINER_NAME}'..."
    docker rm -f "$CONTAINER_NAME"
fi

# ── Start MySQL container ─────────────────────────────────────────────
echo "Starting MySQL container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
    -p "${MYSQL_PORT}:3306" \
    -v "$(pwd)/${DATA_DIR#./}:/var/lib/mysql" \
    -v "$(pwd)/${RAW_DIR#./}:/var/lib/mysql-files/raw" \
    mysql:latest

# ── Wait for MySQL to be ready ────────────────────────────────────────
echo -n "Waiting for MySQL to be ready"
until docker exec "$CONTAINER_NAME" mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1" &>/dev/null; do
    echo -n "."
    sleep 2
done
echo " ready!"

# ── Create database and table, then load CSV ──────────────────────────
echo "Creating database and loading data..."
docker exec -i "$CONTAINER_NAME" mysql -uroot -p"$MYSQL_ROOT_PASSWORD" <<'SQL'
CREATE DATABASE IF NOT EXISTS baseball;
USE baseball;

DROP TABLE IF EXISTS Master;

CREATE TABLE Master (
    ID              INT PRIMARY KEY,
    playerID        VARCHAR(20),
    birthYear       INT,
    birthMonth      INT,
    birthDay        INT,
    birthCity       VARCHAR(100),
    birthCountry    VARCHAR(50),
    birthState      VARCHAR(50),
    deathYear       INT,
    deathMonth      INT,
    deathDay        INT,
    deathCountry    VARCHAR(50),
    deathState      VARCHAR(50),
    deathCity       VARCHAR(100),
    nameFirst       VARCHAR(100),
    nameLast        VARCHAR(100),
    nameGiven       VARCHAR(255),
    weight          INT,
    height          INT,
    bats            VARCHAR(5),
    throws          VARCHAR(5),
    debut           DATE,
    bbrefID         VARCHAR(20),
    finalGame       DATE,
    retroID         VARCHAR(20)
);

LOAD DATA INFILE '/var/lib/mysql-files/raw/People.csv'
INTO TABLE Master
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    ID,
    playerID,
    @birthYear, @birthMonth, @birthDay,
    birthCity, birthCountry, birthState,
    @deathYear, @deathMonth, @deathDay,
    deathCountry, deathState, deathCity,
    nameFirst, nameLast, nameGiven,
    @weight, @height,
    bats, throws,
    @debut, bbrefID, @finalGame, retroID
)
SET
    birthYear   = NULLIF(@birthYear, ''),
    birthMonth  = NULLIF(@birthMonth, ''),
    birthDay    = NULLIF(@birthDay, ''),
    deathYear   = NULLIF(@deathYear, ''),
    deathMonth  = NULLIF(@deathMonth, ''),
    deathDay    = NULLIF(@deathDay, ''),
    weight      = NULLIF(@weight, ''),
    height      = NULLIF(@height, ''),
    debut       = NULLIF(@debut, ''),
    finalGame   = NULLIF(@finalGame, '');
SQL

# ── Verify ────────────────────────────────────────────────────────────
COUNT=$(docker exec "$CONTAINER_NAME" mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -e "SELECT COUNT(*) FROM baseball.Master;" 2>/dev/null)
echo "Loaded ${COUNT} rows into baseball.Master"
echo "Done! Connect with: mysql -h 127.0.0.1 -uroot -ppassword baseball"
