-- mod-unbound: gear attunement collection per character (src/unbound_attunement.cpp).
CREATE TABLE IF NOT EXISTS `character_unbound_attunement` (
  `guid` INT UNSIGNED NOT NULL COMMENT 'characters.guid',
  `item` INT UNSIGNED NOT NULL COMMENT 'item_template.entry',
  `progress` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'attunement kills so far (while not attuned)',
  `attuned` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '1 = 100% attuned (or sacrificed): its stats count',
  PRIMARY KEY (`guid`, `item`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-unbound gear attunement';