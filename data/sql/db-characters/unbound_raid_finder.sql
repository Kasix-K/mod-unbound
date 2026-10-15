-- mod-unbound: Raid Finder (src/unbound_raid_finder.cpp). Where "Leave Raid" sends a player who entered a raid
-- through the Raid Finder: the spot they joined from (or their hearthstone location).
CREATE TABLE IF NOT EXISTS `character_unbound_raid_finder` (
  `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid',
  `raid_map` SMALLINT UNSIGNED NOT NULL COMMENT 'the raid entered',
  `map` SMALLINT UNSIGNED NOT NULL,
  `x` FLOAT NOT NULL,
  `y` FLOAT NOT NULL,
  `z` FLOAT NOT NULL,
  `o` FLOAT NOT NULL,
  PRIMARY KEY (`guid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-unbound Raid Finder return spots';
