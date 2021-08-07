DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS words;
DROP TABLE IF EXISTS active_words;
DROP TABLE IF EXISTS players;

CREATE TABLE games (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  value TEXT UNIQUE NOT NULL
);

CREATE TABLE active_words (
  game_id INTEGER NOT NULL,
  word_id INTEGER NOT NULL,
  color INTEGER NOT NULL
);

CREATE TABLE moves (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  game_id INTEGER NOT NULL,
  word_id INTEGER NOT NULL,
  selected_at INTEGER NOT NULL
);

CREATE TABLE hints (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  game_id INTEGER NOT NULL,
  hint TEXT,
  num INTEGER,
  color INTEGER,
  created_at INTEGER NOT NULL
);

CREATE TABLE players (
  game_id INTEGER NOT NULL,
  session_id TEXT NOT NULL,
  color INTEGER NOT NULL,
  role INTEGER NOT NULL
);

CREATE TABLE turns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hint_id INTEGER,
  game_id INTEGER NOT NULL,
  condition INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);
