-- mod-unbound: choices inside a perk, per character (src/unbound_perks.cpp), e.g. Crusader's Oath's oath
-- (perk 1001: 1 = Oath of Vengeance, 2 = Oath of the Crusade). Characters without a row get choice 1.
CREATE TABLE IF NOT EXISTS `character_unbound_perk_choices` (
  `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid',
  `perk` SMALLINT UNSIGNED NOT NULL COMMENT 'perk id from addon/UnboundPerks/PerkData.lua',
  `choice` TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (`guid`, `perk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-unbound perk choices';
