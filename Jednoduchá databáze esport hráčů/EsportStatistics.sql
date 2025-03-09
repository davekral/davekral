CREATE DATABASE Esport_statistics;
USE Esport_statistics;

CREATE TABLE `players` (
  `id` integer PRIMARY KEY,
  `player_name` varchar(255),
  `role` varchar(255),
  `country` varchar(255),
  `team_id` integer,
  `created_at` timestamp
);

CREATE TABLE `teams` (
  `id` integer PRIMARY KEY,
  `team_name` varchar(255),
  `league_id` integer,
  `created_at` timestamp
);

CREATE TABLE `leagues` (
  `id` integer PRIMARY KEY,
  `league_name` varchar(255),
  `region` varchar(255),
  `created_at` timestamp
);

CREATE TABLE `matches` (
  `id` integer PRIMARY KEY,
  `match_date` timestamp,
  `duration` integer,
  `game_mode` varchar(255),
  `winner_team_id` integer,
  `loser_team_id` integer,
  `league_id` integer,
  `created_at` timestamp
);

CREATE TABLE `player_statistics` (
  `id` integer PRIMARY KEY,
  `player_id` integer,
  `games_played` integer,
  `win_rate` float,
  `kda` float,
  `avg_kills` float,
  `avg_deaths` float,
  `avg_assists` float
);

CREATE TABLE `team_awards` (
  `id` integer PRIMARY KEY,
  `team_id` integer,
  `award_name` varchar(255),
  `award_date` date,
  `created_at` timestamp
);

ALTER TABLE `players` ADD FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`);

ALTER TABLE `teams` ADD FOREIGN KEY (`league_id`) REFERENCES `leagues` (`id`);

ALTER TABLE `matches` ADD FOREIGN KEY (`winner_team_id`) REFERENCES `teams` (`id`);

ALTER TABLE `matches` ADD FOREIGN KEY (`loser_team_id`) REFERENCES `teams` (`id`);

ALTER TABLE `matches` ADD FOREIGN KEY (`league_id`) REFERENCES `leagues` (`id`);

ALTER TABLE `player_statistics` ADD FOREIGN KEY (`player_id`) REFERENCES `players` (`id`);

ALTER TABLE `team_awards` ADD FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`);