-- mod-unbound: open-world elites of the Bulletin Board's weekly elite bounty, brought to normal elite strength.
-- mod-autobalance only scales dungeons and raids, so these keep their full stats in the open world. Most bounty
-- camps are normal elites (HealthModifier about 3); these were tuned for raid groups (7-25, Lord Lakmaeran 100).
-- Their DamageModifier (4.6) is already that of normal elites such as the Scalebanes, so it stays.
-- This changes these creatures for everyone in the open world, not only for the bounty.
-- To undo, set HealthModifier back to the original value in each comment.

-- Emerald Dream portal guardians: Seradane (The Hinterlands), Jademir Lake (Feralas), Bough Shadow (Ashenvale); were 25
UPDATE `creature_template` SET `HealthModifier` = 3 WHERE `entry` IN (
    12477, 12478, 12479,   -- Verdantine Boughguard, Oracle, Tree Warder
    5320, 5317, 5319,      -- Jademir Boughguard, Oracle, Tree Warder
    12474, 12476, 12475);  -- Emeraldon Boughguard, Oracle, Tree Warder

-- The Tainted Scar (Blasted Lands)
UPDATE `creature_template` SET `HealthModifier` = 3 WHERE `entry` IN (
    8717,    -- Felguard Elite, was 18
    8718,    -- Manahound, was 16
    12396,   -- Doomguard Commander, was 20
    8716);   -- Dreadlord, was 20

-- The Isle of Dread (Feralas)
UPDATE `creature_template` SET `HealthModifier` = 3 WHERE `entry` IN (
    12800,   -- Chimaerok, was 10
    12801,   -- Arcane Chimaerok, was 10
    12802);  -- Chimaerok Devourer, was 7
-- Lord Lakmaeran, the isle's lord: like the tougher Hederine elites rather than a normal elite; was 100
UPDATE `creature_template` SET `HealthModifier` = 6 WHERE `entry` = 12803;
