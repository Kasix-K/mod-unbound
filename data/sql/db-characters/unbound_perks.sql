-- mod-unbound: active toggled perks per character (src/unbound_perks.cpp, addon/UnboundPerks).
CREATE TABLE IF NOT EXISTS `character_unbound_perks` (
  `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid',
  `perk` SMALLINT UNSIGNED NOT NULL COMMENT 'perk id from addon/UnboundPerks/PerkData.lua',
  PRIMARY KEY (`guid`, `perk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-unbound perks';
