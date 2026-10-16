-- mod-unbound: account-wide currencies (src/unbound_account_currency.cpp; ROADMAP.md "Heroic currency and vendor").
-- The real amount of each shared currency per account. The character a player logs in gets its currency stack set
-- to this amount, and writes it back at every save (and at logout). `holder` is the character that loaded the
-- balance last: only it may write it back, so an alt logged in as a bot can't overwrite the player's balance.
CREATE TABLE IF NOT EXISTS `account_unbound_currency` (
    `account` INT UNSIGNED NOT NULL,
    `item` INT UNSIGNED NOT NULL,
    `amount` INT UNSIGNED NOT NULL DEFAULT 0,
    `holder` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'character guid that loaded the balance last',
    PRIMARY KEY (`account`, `item`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='mod-unbound: account-wide currency balances';

-- Characters whose own stack of a shared currency was already added to their account's balance (once, the first
-- time each character logs in after the currency became shared, so nothing a character already had is lost).
CREATE TABLE IF NOT EXISTS `character_unbound_currency_merged` (
    `guid` INT UNSIGNED NOT NULL,
    `item` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`guid`, `item`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='mod-unbound: characters merged into the account currency balance';
