-- mod-unbound: perk ranks set by a GM with ".perk rank <perk id> <rank>" (src/unbound_perks.cpp).
-- Characters without a row here get the rank their level gives.
CREATE TABLE IF NOT EXISTS `character_unbound_perk_ranks` (
  `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid',
  `perk` SMALLINT UNSIGNED NOT NULL COMMENT 'perk id from addon/UnboundPerks/PerkData.lua',
  `rank` TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (`guid`, `perk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-unbound perk ranks';
