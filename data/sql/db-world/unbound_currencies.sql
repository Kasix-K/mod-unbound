-- mod-unbound: account-wide currencies (ROADMAP.md "Heroic currency and vendor"), items 912000-912099.
-- The client side (Item.dbc, the icon's ItemDisplayInfo.dbc row, the Currency tab's CurrencyTypes.dbc and
-- CurrencyCategory.dbc rows, and the ItemExtendedCost.dbc prices) comes from tools/custom_dbc.py.
--
-- 912000 Heroic Sigil: modelled on Emblem of Heroism (40752). Class 10 (currency), epic, Flags 2048
-- (ITEM_FLAG_MULTI_DROP: every group member gets their own from a loot table), stacks to 2147483647, bag family
-- 8192 (the hidden currency token bag, so it shows in the Currency tab and takes no bag space), soulbound on
-- pickup (bonding 1: can't be traded or mailed) and no sell price. Display 70000: the
-- Spell_Holy_SealOfRighteousness icon.
DELETE FROM `item_template` WHERE `entry` = 912000;
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`,
    `Flags`, `BuyCount`, `BuyPrice`, `SellPrice`, `InventoryType`, `AllowableClass`, `AllowableRace`, `ItemLevel`,
    `RequiredLevel`, `stackable`, `bonding`, `description`, `Material`, `BagFamily`, `VerifiedBuild`) VALUES
(912000, 10, 0, -1, 'Heroic Sigil', 70000, 4,
    2048, 1, 0, 0, 0, 262143, 32767, 60,
    0, 2147483647, 1, 'Earned from Heroic dungeon bosses. Spent at the Heroic Quartermaster.', 4, 8192, 12340);
