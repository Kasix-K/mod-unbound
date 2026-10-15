<#
  Applies the Unbound server's settings to an AzerothCore config folder (worldserver.conf and modules\*.conf).
  These are all the settings the original server changed from the defaults (paths and passwords aside).
  setup-wow-server.ps1 runs this on new config files; to run it on an existing server (stop it first):

     powershell -ExecutionPolicy Bypass -File apply-unbound-settings.ps1 -ConfigDir "D:\WoW Solo Server\server\configs"

  A .conf file that doesn't exist yet is created from its .conf.dist first. When a setting changes on the
  original server, change it here too (and in the table in the README).
#>
param(
    [Parameter(Mandatory)][string]$ConfigDir,
    [string[]]$Only = @()   # limit to these .conf files (full paths)
)

$ErrorActionPreference = 'Stop'

$Settings = [ordered]@{
    'worldserver.conf' = [ordered]@{
        # Classic only for now (see mod_unbound.conf): level cap 60, no new Death Knights except on GM accounts
        'MaxPlayerLevel'                       = '60'
        'CharacterCreating.Disabled.ClassMask' = '32'
        # Faster leveling
        'Rate.XP.Kill'                         = '3'
        'Rate.XP.Quest'                        = '4'
        'Rate.XP.Quest.DF'                     = '4'
        'Rate.XP.Explore'                      = '2'
        'Rate.XP.Pet'                          = '3'
        # Enter raids without a raid group; no limit on instances per hour
        'Instance.IgnoreRaid'                  = '1'
        'AccountInstancesPerHour'              = '1000000'
        # Cross-faction everything except battlegrounds
        'AllowTwoSide.Interaction.Calendar'    = '1'
        'AllowTwoSide.Interaction.Chat'        = '1'
        'AllowTwoSide.Interaction.Channel'     = '1'
        'AllowTwoSide.Interaction.Group'       = '1'
        'AllowTwoSide.Interaction.Guild'       = '1'
        'AllowTwoSide.Interaction.Arena'       = '1'
        'AllowTwoSide.Interaction.Auction'     = '1'
        # Permanent perks: No Resurrection Sickness, No Daze (Rapid Recovery is in src/unbound_perks.cpp)
        'Death.SicknessLevel'                  = '255'
        'Daze.Enabled'                         = '0'
    }
    'modules\AutoBalance.conf' = [ordered]@{
        # Solo scaling never goes below 40% of the normal strength
        'AutoBalance.InflectionPoint.CurveFloor'           = '0.4'
        'AutoBalance.InflectionPointHeroic.CurveFloor'     = '0.4'
        'AutoBalance.InflectionPointRaid.CurveFloor'       = '0.4'
        'AutoBalance.InflectionPointRaidHeroic.CurveFloor' = '0.4'
        # Classic raids solo: about 3 players' worth for one player, full strength for a full raid
        # (ROADMAP.md, Power budget). 20-player: Zul'Gurub, Ruins of Ahn'Qiraj; 40-player: Molten Core,
        # Blackwing Lair, Temple of Ahn'Qiraj.
        'AutoBalance.InflectionPointRaid20M.CurveFloor'    = '0.1'
        'AutoBalance.InflectionPointRaid40M.CurveFloor'    = '0.03'
        # Keep creature levels, XP and gold as they are
        'AutoBalance.LevelScaling'                         = '0'
        'AutoBalance.RewardScaling.XP'                     = '0'
        'AutoBalance.RewardScaling.Money'                  = '0'
        'AutoBalanceAnnounce.enable'                       = '0'
    }
    'modules\mod_aoe_loot.conf' = [ordered]@{
        'AOELoot.Message' = '0'
    }
    'modules\mod_transmog_plus.conf' = [ordered]@{
        'Transmog.PriceCopper'                  = '0'
        'Transmog.AllowMixedArmorTypes'         = '1'
        'Transmog.AllowMixedOffhandArmorTypes'  = '1'
        'Transmog.Backpacks.Enable'             = '0'
        'Transmog.Backpacks.Mail.Enable'        = '0'
    }
    'modules\playerbots.conf' = [ordered]@{
        # Bots stay in classic content and out of the dungeon finder
        'Playerbots.RandomBotMaxLevel'       = '60'
        'Playerbots.RandomBotJoinLfg'        = '0'
        'Playerbots.DisableDeathKnightLogin' = '1'
        'Playerbots.RandomBotMaps'           = '0,1'
    }
    'modules\SoloLfg.conf' = [ordered]@{
        'SoloLFG.Announce' = '0'
        'SoloLFG.FixedXP'  = '0'
    }
}

$utf8 = New-Object System.Text.UTF8Encoding($false)
foreach ($file in $Settings.Keys) {
    $path = Join-Path $ConfigDir $file
    if ($Only.Count -and ($Only | ForEach-Object { [IO.Path]::GetFullPath($_) }) -notcontains [IO.Path]::GetFullPath($path)) {
        continue
    }
    if (-not (Test-Path $path)) {
        if (-not (Test-Path "$path.dist")) {
            Write-Host "  [!]    $file not found (is its module installed?), skipped" -ForegroundColor Yellow
            continue
        }
        Copy-Item "$path.dist" $path
    }
    $text = [IO.File]::ReadAllText($path)
    foreach ($key in $Settings[$file].Keys) {
        $value = $Settings[$file][$key]
        $pattern = "(?m)^(\s*)" + [regex]::Escape($key) + "\s*=.*$"
        if ([regex]::IsMatch($text, $pattern)) {
            $text = [regex]::Replace($text, $pattern, { param($m) $m.Groups[1].Value + "$key = $value" })
            Write-Host "  [OK]   ${file}: $key = $value" -ForegroundColor Green
        } else {
            Write-Host "  [!]    ${file}: $key not found, left unchanged" -ForegroundColor Yellow
        }
    }
    [IO.File]::WriteAllText($path, $text, $utf8)
}
