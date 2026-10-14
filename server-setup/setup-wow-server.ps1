<#
  Unbound server (AzerothCore 3.3.5a + mod-playerbots + Unbound modules) - Windows setup script
  -----------------------------------------------------------------------------------------------
  Installs everything into -Root (default "E:\WoW Solo Server"), with the same AzerothCore and module
  versions and the same server settings as the original Unbound server.

  What it does (each step is skipped if it is already done, so it is safe to re-run):
    0. Pre-flight checks (drive, free space, git, curl, tar)
    1. Visual Studio Build Tools 2022: makes sure the C++ tools are present
    2. CMake 3.31.8 (portable, unzipped into deps\)
    3. Ninja 1.12.1 (portable)  -> lets the build use exactly 4 parallel jobs
    4. Boost 1.83.0 (prebuilt MSVC 14.3 x64, from archives.boost.io)
    5. OpenSSL 3.5 LTS (FireDaemon ZIP)
    6. MySQL 8.4 LTS (portable ZIP, own data folder, NOT a Windows service)
       + root password, 'acore' user and the acore_ databases
    7. Clone mod-playerbots/azerothcore-wotlk (branch Playerbot) and every module the Unbound
       server uses (including mod-unbound), each at the version listed in $Modules below
    8. Configure + build (4 parallel jobs) + install
    9. Client data: wowgaming/client-data release v20.0 (Data.zip)
   10. Config files (.conf) with the Unbound settings (apply-unbound-settings.ps1), DLLs,
       Start/Stop/Rebuild scripts
   11. Your game client (optional): the Unbound and Transmog addons and the custom client patch

  It never deletes or overwrites anything of yours. If something already exists
  that it did not expect, it stops and asks.

  Run it from a normal PowerShell window (pick any folder for -Root, it is created if needed):
     powershell -ExecutionPolicy Bypass -File setup-wow-server.ps1 -Root "D:\WoW Solo Server"
#>
param(
    [string]$Root = 'E:\WoW Solo Server'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'
$OutputEncoding        = New-Object System.Text.UTF8Encoding($false)

# ---------------------------------------------------------------- settings
$Root      = [IO.Path]::GetFullPath($Root)
$Deps     = Join-Path $Root 'deps'
$Dl        = Join-Path $Root 'downloads'
$Logs      = Join-Path $Root 'logs'
$Src       = Join-Path $Root 'azerothcore'
$Build     = Join-Path $Root 'build'
$Server    = Join-Path $Root 'server'
$DataDir   = Join-Path $Root 'data'
$MyData    = Join-Path $Root 'mysql-data'
$MyIni     = Join-Path $Deps 'my.ini'

$CMakeVer  = '3.31.8'
$NinjaVer  = '1.12.1'
$BoostVer  = '1.83.0'
$OpenSslVer= '3.5.9'
$MySqlVer  = '8.4.11'
$BuildJobs = 4

$CMakeDir  = Join-Path $Deps "cmake-$CMakeVer-windows-x86_64"
$NinjaDir  = Join-Path $Deps 'ninja'
$BoostDir  = Join-Path $Deps 'boost_1_83_0'
$OpenSslDir= Join-Path $Deps "openssl-$OpenSslVer"
$MySqlDir  = Join-Path $Deps "mysql-$MySqlVer-winx64"

$CoreRepo   = 'https://github.com/mod-playerbots/azerothcore-wotlk.git'
$CoreBranch = 'Playerbot'
# The versions the Unbound server runs. Update these when the original server updates a module.
$CoreCommit = '2a2211cd8'
$Modules = [ordered]@{
    'mod-playerbots'      = @('https://github.com/mod-playerbots/mod-playerbots.git',           '79bd4281')
    'mod-transmog-plus'   = @('https://github.com/buildthehomelab/wow-mod-transmog-plus.git',  '860dc5b')
    'mod-aoe-loot'        = @('https://github.com/azerothcore/mod-aoe-loot.git',               '44486b1')
    'mod-autobalance'     = @('https://github.com/azerothcore/mod-autobalance.git',            '1d707cb')
    'mod-solo-lfg'        = @('https://github.com/azerothcore/mod-solo-lfg.git',               '3821fe1')
    'mod-multibot-bridge' = @('https://github.com/Wishmaster117/mod-multibot-bridge.git',      '8f703da')
    'mod-unbound'         = @('https://github.com/Kasix-K/mod-unbound.git',                    '')  # latest
}

$Databases = @('acore_auth','acore_characters','acore_world','acore_playerbots')

# ---------------------------------------------------------------- helpers
function Write-Step($n, $text) {
    Write-Host ''
    Write-Host ('=' * 70) -ForegroundColor DarkCyan
    Write-Host ("STEP $n - $text") -ForegroundColor Cyan
    Write-Host ('=' * 70) -ForegroundColor DarkCyan
}
function Say($text)  { Write-Host "  $text" }
function Ok($text)   { Write-Host "  [OK]   $text" -ForegroundColor Green }
function Skip($text) { Write-Host "  [SKIP] $text" -ForegroundColor DarkGray }
function Warn($text) { Write-Host "  [!]    $text" -ForegroundColor Yellow }
function YouDo($text){ Write-Host ''; Write-Host "  >>> YOUR TURN: $text" -ForegroundColor Magenta }

function Ask-YesNo($question) {
    while ($true) {
        $a = Read-Host "  $question [y/n]"
        if ($a -match '^(y|yes)$') { return $true }
        if ($a -match '^(n|no)$')  { return $false }
    }
}
function Stop-Setup($why) {
    Write-Host ''
    Write-Host "  SETUP STOPPED: $why" -ForegroundColor Red
    Write-Host "  Nothing was deleted. Fix the issue (or ask Claude) and run the script again;" -ForegroundColor Red
    Write-Host "  finished steps will be skipped." -ForegroundColor Red
    try { Stop-Transcript | Out-Null } catch {}
    exit 1
}
function Fwd($p) { return ($p -replace '\\','/') }

# Runs a native program, shows output live, appends it to a log, throws on failure.
function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments, [string]$Log)
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Exe @Arguments 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $Log -Append | Out-Host
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $old }
    if ($code -ne 0) { throw "'$(Split-Path $Exe -Leaf)' failed with exit code $code. Log: $Log" }
}

# Downloads a file (tries each URL), checks type/size/hash. Falls back to asking you to download it.
function Get-File {
    param([string[]]$Urls, [string]$Dest, [string]$Kind, [long]$MinBytes,
          [string]$HashAlgo = '', [string]$Hash = '', [string]$ManualPage = '')
    function Test-Download($path) {
        if (-not (Test-Path $path)) { return $false }
        $fi = Get-Item $path
        if ($fi.Length -lt $MinBytes) { return $false }
        $fs = [IO.File]::OpenRead($path); $b = New-Object byte[] 2
        [void]$fs.Read($b, 0, 2); $fs.Close()
        $sig = [Text.Encoding]::ASCII.GetString($b)
        if ($Kind -eq 'zip' -and $sig -ne 'PK') { return $false }
        if ($Kind -eq 'exe' -and $sig -ne 'MZ') { return $false }
        return $true
    }
    if (Test-Download $Dest) {
        Skip "$(Split-Path $Dest -Leaf) already downloaded"
    } else {
        $got = $false
        foreach ($u in $Urls) {
            Say "Downloading $u"
            $part = "$Dest.part"
            & curl.exe -L --fail --retry 3 --progress-bar -o $part $u
            if ($LASTEXITCODE -eq 0 -and (Test-Download $part)) {
                Move-Item -Force $part $Dest; $got = $true; break
            }
            Warn "That link did not give a valid file."
            if (Test-Path $part) { Remove-Item -Force $part }   # our own partial download only
        }
        while (-not $got) {
            YouDo "Please download this file yourself:"
            if ($ManualPage) { Say "  From: $ManualPage" } else { Say "  From: $($Urls[0])" }
            Say "  Save it EXACTLY as: $Dest"
            Read-Host '  Press Enter once the file is saved there'
            $got = Test-Download $Dest
            if (-not $got) { Warn 'Still not found (or the file looks wrong).' }
        }
    }
    if ($Hash) {
        Say "Verifying $HashAlgo checksum..."
        $h = (Get-FileHash -Algorithm $HashAlgo $Dest).Hash
        if ($h -ne $Hash.ToUpper()) {
            Rename-Item $Dest "$Dest.bad-checksum" -Force
            Stop-Setup "Checksum mismatch for $(Split-Path $Dest -Leaf) (renamed to .bad-checksum). Re-run to download again."
        }
        Ok 'Checksum matches'
    }
}

function Expand-Zip($zip, $dest) {
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Say "Extracting $(Split-Path $zip -Leaf) ..."
    & tar.exe -xf $zip -C $dest
    if ($LASTEXITCODE -ne 0) { throw "Extracting $zip failed" }
}

function Test-PortListening($port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

# Runs SQL as MySQL root. Password goes in a temp option file (never on the command line).
function Invoke-MySql([string]$Sql, [string]$RootPw) {
    $mysql = Join-Path $MySqlDir 'bin\mysql.exe'
    $cnf = Join-Path $env:TEMP ("acore-setup-" + [guid]::NewGuid().ToString() + '.cnf')
    $content = "[client]`nuser=root`nhost=localhost`nport=3306`n"
    if ($RootPw) {
        $esc = $RootPw.Replace('\','\\').Replace('"','\"')
        $content += "password=`"$esc`"`n"
    }
    [IO.File]::WriteAllText($cnf, $content, (New-Object System.Text.UTF8Encoding($false)))
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        $out = $Sql | & $mysql "--defaults-extra-file=$cnf" --batch 2>&1 | ForEach-Object { "$_" }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $old
        Remove-Item -Force $cnf -ErrorAction SilentlyContinue
    }
    if ($code -ne 0) { throw "MySQL command failed: $($out -join ' ')" }
    return $out
}

function Read-Password($prompt) {
    $s = Read-Host -AsSecureString "  $prompt"
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}

function Set-ConfValue($file, $key, $value) {
    $text = [IO.File]::ReadAllText($file)
    $pattern = "(?m)^(\s*)" + [regex]::Escape($key) + "\s*=.*$"
    if ([regex]::IsMatch($text, $pattern)) {
        $text = [regex]::Replace($text, $pattern, { param($m) $m.Groups[1].Value + "$key = $value" })
        [IO.File]::WriteAllText($file, $text, (New-Object System.Text.UTF8Encoding($false)))
        Ok "$(Split-Path $file -Leaf): $key = $value"
    } else {
        Warn "$(Split-Path $file -Leaf): key '$key' not found, left unchanged"
    }
}

# ================================================================ START
foreach ($d in @($Root, $Deps, $Dl, $Logs)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BuildLog = Join-Path $Logs "build-$stamp.log"
Start-Transcript -Path (Join-Path $Logs "setup-$stamp.log") -Append | Out-Null

try {

# ---------------------------------------------------------------- 0
Write-Step 0 'Pre-flight checks'
$drive = $Root.Substring(0, 1)
$freeGB = [math]::Round((Get-PSDrive $drive).Free / 1GB)
if ($freeGB -lt 60) { Stop-Setup "Only $freeGB GB free on ${drive}:. Need at least 60 GB." }
Ok "${drive}: has $freeGB GB free"

foreach ($tool in @('curl.exe','tar.exe')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { Stop-Setup "$tool not found (it ships with Windows 10/11)." }
}
$git = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $git) {
    foreach ($p in @("$env:ProgramFiles\Git\cmd", "${env:ProgramFiles(x86)}\Git\cmd")) {
        if (Test-Path (Join-Path $p 'git.exe')) { $env:Path = "$p;$env:Path"; break }
    }
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
}
if (-not $git) { Stop-Setup 'git was not found. Install Git for Windows, then re-run.' }
Ok ("git: " + (& git --version))

Say ''
Say 'This script will now install the missing pieces into:'
Say "  $Root"
Say 'It does not change your system PATH and does not install Windows services.'
if (-not (Ask-YesNo 'Continue?')) { Stop-Setup 'Cancelled by you.' }

# ---------------------------------------------------------------- 1
Write-Step 1 'Visual Studio Build Tools 2022 (C++ tools)'
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vswhere)) { Stop-Setup 'vswhere.exe not found - is the Visual Studio Installer present?' }
function Find-VS2022Cpp {
    & $vswhere -products * -version '[17.0,18.0)' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath -latest
}
$vsPath = Find-VS2022Cpp
if (-not $vsPath) {
    $bt = & $vswhere -products Microsoft.VisualStudio.Product.BuildTools -version '[17.0,18.0)' -property installationPath -latest
    if (-not $bt) { Stop-Setup 'Visual Studio Build Tools 2022 not found.' }
    Warn 'Build Tools 2022 is installed but the C++ tools (Desktop development with C++) are missing.'
    if (-not (Ask-YesNo 'Add the C++ workload to Build Tools 2022 now? (adds ~6-8 GB on C:, removes nothing)')) {
        Stop-Setup 'C++ tools are required. Add "Desktop development with C++" in the Visual Studio Installer, then re-run.'
    }
    YouDo 'Windows may ask for admin permission (UAC). Click Yes. A Visual Studio Installer window will show progress.'
    $setup = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\setup.exe"
    $p = Start-Process -FilePath $setup -Wait -PassThru -ArgumentList @(
        'modify', '--installPath', "`"$bt`"",
        '--add', 'Microsoft.VisualStudio.Workload.VCTools', '--includeRecommended',
        '--passive', '--norestart')
    $vsPath = Find-VS2022Cpp
    if (-not $vsPath) { Stop-Setup "Adding the C++ workload did not finish (installer exit code $($p.ExitCode))." }
}
Ok "VS 2022 C++ tools: $vsPath"
$vcvars = Join-Path $vsPath 'VC\Auxiliary\Build\vcvars64.bat'
if (-not (Test-Path $vcvars)) { Stop-Setup "vcvars64.bat not found under $vsPath" }

# ---------------------------------------------------------------- 2
Write-Step 2 "CMake $CMakeVer (portable)"
$cmake = Join-Path $CMakeDir 'bin\cmake.exe'
if (Test-Path $cmake) { Skip 'CMake already in deps' } else {
    $zip = Join-Path $Dl "cmake-$CMakeVer-windows-x86_64.zip"
    Get-File -Urls @("https://github.com/Kitware/CMake/releases/download/v$CMakeVer/cmake-$CMakeVer-windows-x86_64.zip") `
             -Dest $zip -Kind zip -MinBytes 20MB
    Expand-Zip $zip $Deps
}
if (-not (Test-Path $cmake)) { Stop-Setup 'cmake.exe not found after extracting.' }
Ok ((& $cmake --version | Select-Object -First 1))

# ---------------------------------------------------------------- 3
Write-Step 3 "Ninja $NinjaVer (build tool that enforces $BuildJobs parallel jobs)"
$ninja = Join-Path $NinjaDir 'ninja.exe'
if (Test-Path $ninja) { Skip 'Ninja already in deps' } else {
    $zip = Join-Path $Dl "ninja-win-$NinjaVer.zip"
    Get-File -Urls @("https://github.com/ninja-build/ninja/releases/download/v$NinjaVer/ninja-win.zip") `
             -Dest $zip -Kind zip -MinBytes 100KB
    Expand-Zip $zip $NinjaDir
}
Ok "Ninja: $ninja"

# ---------------------------------------------------------------- 4
Write-Step 4 "Boost $BoostVer (archives.boost.io, MSVC 14.3 x64)"
$boostLib = Join-Path $BoostDir 'lib64-msvc-14.3'
if ((Test-Path (Join-Path $BoostDir 'boost\version.hpp')) -and (Test-Path $boostLib)) {
    Skip 'Boost 1.83 already installed in deps'
} else {
    $exe = Join-Path $Dl 'boost_1_83_0-msvc-14.3-64.exe'
    Get-File -Urls @('https://archives.boost.io/release/1.83.0/binaries/boost_1_83_0-msvc-14.3-64.exe') `
             -Dest $exe -Kind exe -MinBytes 100MB
    YouDo 'Windows may ask for admin permission (UAC) for the Boost installer. Click Yes. It installs silently (a few minutes).'
    $p = Start-Process -FilePath $exe -Wait -PassThru -ArgumentList @(
        '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-', "/DIR=`"$BoostDir`"")
    if (-not (Test-Path (Join-Path $BoostDir 'boost\version.hpp'))) {
        Stop-Setup "Boost installer did not finish (exit code $($p.ExitCode))."
    }
}
Ok "Boost: $BoostDir"

# ---------------------------------------------------------------- 5
Write-Step 5 "OpenSSL $OpenSslVer LTS (FireDaemon ZIP)"
function Find-OpenSslX64 {
    if (-not (Test-Path $OpenSslDir)) { return $null }
    $lib = Get-ChildItem -Path $OpenSslDir -Recurse -Filter 'libcrypto.lib' -ErrorAction SilentlyContinue |
           Where-Object { $_.FullName -match '\\x64\\' } | Select-Object -First 1
    if ($lib) { return (Split-Path (Split-Path $lib.FullName -Parent) -Parent) }
    return $null
}
$sslRoot = Find-OpenSslX64
if ($sslRoot) { Skip 'OpenSSL already in deps' } else {
    $zip = Join-Path $Dl "openssl-$OpenSslVer.zip"
    Get-File -Urls @("https://download.firedaemon.com/FireDaemon-OpenSSL/openssl-$OpenSslVer.zip",
                     'https://www.firedaemon.com/download-firedaemon-openssl-3-5-zip') `
             -Dest $zip -Kind zip -MinBytes 5MB `
             -HashAlgo SHA256 -Hash '76DA391395BE029B44794857B9FF380255E02A0960A98314CD3F6A6816D82696' `
             -ManualPage 'https://www.firedaemon.com/download-firedaemon-openssl  (pick "OpenSSL 3.5.x LTS ZIP")'
    Expand-Zip $zip $OpenSslDir
    $sslRoot = Find-OpenSslX64
}
if (-not $sslRoot) { Stop-Setup 'Could not find the x64 OpenSSL libraries inside the FireDaemon ZIP.' }
Ok "OpenSSL x64: $sslRoot"

# ---------------------------------------------------------------- 6
Write-Step 6 "MySQL $MySqlVer LTS (portable, data in $MyData)"
$mysqld = Join-Path $MySqlDir 'bin\mysqld.exe'
if (Test-Path $mysqld) { Skip 'MySQL already extracted' } else {
    $zip = Join-Path $Dl "mysql-$MySqlVer-winx64.zip"
    Get-File -Urls @("https://dev.mysql.com/get/Downloads/MySQL-8.4/mysql-$MySqlVer-winx64.zip",
                     "https://cdn.mysql.com/archives/mysql-8.4/mysql-$MySqlVer-winx64.zip") `
             -Dest $zip -Kind zip -MinBytes 100MB -HashAlgo MD5 -Hash '2e833921898a9a030ea6bfe81bd811bc' `
             -ManualPage 'https://dev.mysql.com/downloads/mysql/8.4.html  (Windows (x86, 64-bit), ZIP Archive - not the Debug/Test one)'
    Expand-Zip $zip $Deps
}
if (-not (Test-Path $mysqld)) { Stop-Setup 'mysqld.exe not found after extracting MySQL.' }

if (-not (Test-Path $MyIni)) {
    $ini = @"
[mysqld]
basedir="$(Fwd $MySqlDir)"
datadir="$(Fwd $MyData)"
port=3306
bind-address=127.0.0.1
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
max_allowed_packet=128M
innodb_buffer_pool_size=1G

[client]
port=3306
"@
    [IO.File]::WriteAllText($MyIni, $ini, (New-Object System.Text.UTF8Encoding($false)))
    Ok "Wrote $MyIni"
} else { Skip 'my.ini already exists (left unchanged)' }

$freshDb = $false
if (-not (Test-Path $MyData)) {
    Say 'Initializing a new MySQL data folder...'
    Invoke-Native -Exe $mysqld -Arguments @("--defaults-file=$MyIni", '--initialize-insecure', '--console') -Log $BuildLog
    $freshDb = $true
    Ok 'MySQL data folder initialized'
} else { Skip "MySQL data folder already exists ($MyData)" }

# Start our MySQL if it is not already running
$ours = Get-Process mysqld -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $mysqld }
if (-not $ours) {
    if (Test-PortListening 3306) {
        $owner = (Get-NetTCPConnection -LocalPort 3306 -State Listen | Select-Object -First 1).OwningProcess
        $pname = (Get-Process -Id $owner -ErrorAction SilentlyContinue).Path
        Stop-Setup "Port 3306 is already used by another program ($pname). Stop it first (I will not touch it)."
    }
    Say 'Starting MySQL (minimized window)...'
    Start-Process -FilePath $mysqld -ArgumentList "--defaults-file=`"$MyIni`"" -WindowStyle Minimized | Out-Null
    $t = 0
    while (-not (Test-PortListening 3306)) {
        Start-Sleep 2; $t += 2
        if ($t -ge 90) { Stop-Setup "MySQL did not start within 90 s. Check $MyData\*.err" }
    }
}
Ok 'MySQL is running on 127.0.0.1:3306'

if ($freshDb) {
    YouDo 'Choose a MySQL ROOT password (admin password for the database; you will rarely need it). Write it down.'
    while ($true) {
        $pw1 = Read-Password 'New MySQL root password'
        $pw2 = Read-Password 'Type it again'
        if ($pw1 -and ($pw1 -eq $pw2)) { break }
        Warn 'Empty or not matching - try again.'
    }
    $esc = $pw1.Replace('\','\\').Replace("'","''")
    Invoke-MySql "ALTER USER 'root'@'localhost' IDENTIFIED BY '$esc';" '' | Out-Null
    $RootPw = $pw1
    Ok 'Root password set'
} else {
    YouDo "Enter your existing MySQL ROOT password (for this MySQL in $Root)."
    $RootPw = Read-Password 'MySQL root password'
}

$sql = @"
CREATE USER IF NOT EXISTS 'acore'@'localhost' IDENTIFIED BY 'acore';
CREATE USER IF NOT EXISTS 'acore'@'127.0.0.1' IDENTIFIED BY 'acore';
"@
foreach ($db in $Databases) {
    $sql += "CREATE DATABASE IF NOT EXISTS ``$db`` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`n"
    $sql += "GRANT ALL PRIVILEGES ON ``$db``.* TO 'acore'@'localhost';`n"
    $sql += "GRANT ALL PRIVILEGES ON ``$db``.* TO 'acore'@'127.0.0.1';`n"
}
$sql += "FLUSH PRIVILEGES;`n"
Invoke-MySql $sql $RootPw | Out-Null
Ok "User 'acore' (password 'acore') and databases ready: $($Databases -join ', ')"
Say '(Existing databases were kept as they are; nothing was dropped.)'

# ---------------------------------------------------------------- 7
Write-Step 7 'Source code (Playerbot fork + modules)'
function Get-Origin($dir) {
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $o = & git -C $dir remote get-url origin 2>$null } finally { $ErrorActionPreference = $old }
    return "$o"
}
if (Test-Path $Src) {
    $o = Get-Origin $Src
    if ($o -notmatch 'mod-playerbots/azerothcore-wotlk') {
        Stop-Setup "$Src already exists but is not a clone of $CoreRepo (origin: '$o'). Move or rename it, then re-run."
    }
    Skip "AzerothCore source already cloned (branch: $(& git -C $Src rev-parse --abbrev-ref HEAD))"
} else {
    Invoke-Native -Exe 'git' -Arguments @('-c','core.longpaths=true','clone','--branch',$CoreBranch,'--single-branch',$CoreRepo,$Src) -Log $BuildLog
    & git -C $Src config core.longpaths true
    Invoke-Native -Exe 'git' -Arguments @('-C',$Src,'-c','advice.detachedHead=false','checkout',$CoreCommit) -Log $BuildLog
    Ok "Cloned azerothcore-wotlk (Playerbot) at $CoreCommit"
}
foreach ($name in $Modules.Keys) {
    $repo, $commit = $Modules[$name]
    $dir = Join-Path $Src "modules\$name"
    $repoPath = ([uri]$repo).AbsolutePath.Trim('/') -replace '\.git$',''
    if (Test-Path $dir) {
        $o = Get-Origin $dir
        if ($o -notmatch [regex]::Escape($repoPath)) {
            Stop-Setup "$dir exists but is not a clone of $repo (origin: '$o'). Move or rename it, then re-run."
        }
        Skip "$name already cloned"
        continue
    }
    if ($name -eq 'mod-unbound') {
        Say 'mod-unbound is a private repository: if Git asks you to sign in to GitHub, use the account the owner invited.'
    }
    Invoke-Native -Exe 'git' -Arguments @('-c','core.longpaths=true','clone',$repo,$dir) -Log $BuildLog
    if ($commit) {
        Invoke-Native -Exe 'git' -Arguments @('-C',$dir,'-c','advice.detachedHead=false','checkout',$commit) -Log $BuildLog
        Ok "Cloned $name at $commit"
    } else {
        Ok "Cloned $name (latest)"
    }
}

# ---------------------------------------------------------------- 8
Write-Step 8 "Configure + build ($BuildJobs parallel jobs) + install"
Say 'Loading the Visual Studio 2022 x64 build environment...'
# A tiny helper .bat avoids cmd.exe quoting problems with "Program Files (x86)" in the path.
$helperBat = Join-Path ([IO.Path]::GetTempPath()) ("acore-vcvars-" + [guid]::NewGuid().ToString() + '.bat')
Set-Content -Path $helperBat -Encoding ASCII -Value @(
    '@echo off',
    "call `"$vcvars`" >nul 2>&1",
    'set'
)
try     { $envDump = & $helperBat }
finally { Remove-Item -Force $helperBat -ErrorAction SilentlyContinue }
foreach ($line in $envDump) {
    if ($line -match '^([^=]+)=(.*)$') { Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2] }
}
if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) { Stop-Setup 'The C++ compiler (cl.exe) is not available after loading vcvars64.bat.' }
Ok 'Compiler environment loaded'

$env:BOOST_ROOT = Fwd $BoostDir
$env:Path = "$NinjaDir;$(Split-Path $cmake);$env:Path"

$worldExe = Get-ChildItem -Path $Server -Recurse -Filter 'worldserver.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($worldExe) {
    Skip "Server already built and installed ($($worldExe.FullName))."
    Say  '(To rebuild later, delete the "build" folder yourself or ask Claude for the rebuild command.)'
} else {
    $cfg = @(
        '-S', $Src, '-B', $Build, '-G', 'Ninja',
        "-DCMAKE_MAKE_PROGRAM=$(Fwd $ninja)",
        '-DCMAKE_BUILD_TYPE=RelWithDebInfo',
        "-DCMAKE_INSTALL_PREFIX=$(Fwd $Server)",
        '-DTOOLS_BUILD=none', '-DSCRIPTS=static', '-DMODULES=static', '-DWITH_WARNINGS=0',
        "-DBOOST_ROOT=$(Fwd $BoostDir)",
        "-DBOOST_LIBRARYDIR=$(Fwd $boostLib)",
        "-DOPENSSL_ROOT_DIR=$(Fwd $sslRoot)",
        "-DMYSQL_INCLUDE_DIR=$(Fwd (Join-Path $MySqlDir 'include'))",
        "-DMYSQL_LIBRARY=$(Fwd (Join-Path $MySqlDir 'lib\libmysql.lib'))",
        "-DMYSQL_EXECUTABLE=$(Fwd (Join-Path $MySqlDir 'bin\mysql.exe'))"
    )
    Say 'Configuring with CMake...'
    Invoke-Native -Exe $cmake -Arguments $cfg -Log $BuildLog
    Ok 'Configured'

    Say "Building with $BuildJobs parallel jobs. This usually takes 30-90 minutes. Leave this window open."
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Invoke-Native -Exe $cmake -Arguments @('--build', $Build, '--parallel', "$BuildJobs") -Log $BuildLog
    Ok ("Build finished in {0:N0} minutes" -f $sw.Elapsed.TotalMinutes)

    Invoke-Native -Exe $cmake -Arguments @('--install', $Build) -Log $BuildLog
    $worldExe = Get-ChildItem -Path $Server -Recurse -Filter 'worldserver.exe' | Select-Object -First 1
    if (-not $worldExe) { Stop-Setup "Install finished but worldserver.exe was not found under $Server." }
    Ok "Installed to $Server"
}
$BinDir = $worldExe.DirectoryName

# ---------------------------------------------------------------- 9
Write-Step 9 'Client data (wowgaming/client-data v20.0)'
function Find-DataRoot {
    if (-not (Test-Path $DataDir)) { return $null }
    if (Test-Path (Join-Path $DataDir 'dbc')) { return $DataDir }
    $d = Get-ChildItem -Path $DataDir -Recurse -Depth 2 -Directory -Filter 'dbc' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($d) { return $d.Parent.FullName }
    return $null
}
$dataRoot = Find-DataRoot
if ($dataRoot) { Skip "Client data already present ($dataRoot)" } else {
    $zip = Join-Path $Dl 'Data-v20.0.zip'
    Get-File -Urls @('https://github.com/wowgaming/client-data/releases/download/v20.0/Data.zip') `
             -Dest $zip -Kind zip -MinBytes 500MB `
             -HashAlgo SHA256 -Hash 'a3d4df635ae6c2c8f08052c32a79e0f806955150ad36b014a823dd08a32a4610'
    Expand-Zip $zip $DataDir
    $dataRoot = Find-DataRoot
    if (-not $dataRoot) { Stop-Setup "Extracted Data.zip but found no 'dbc' folder under $DataDir." }
}
foreach ($sub in @('dbc','maps','vmaps','mmaps')) {
    if (Test-Path (Join-Path $dataRoot $sub)) { Ok "data\$sub" } else { Warn "data\$sub is missing" }
}

# ---------------------------------------------------------------- 10
Write-Step 10 'Config files, DLLs, start/stop scripts'
$worldDist = Get-ChildItem -Path $Server -Recurse -Filter 'worldserver.conf.dist' | Select-Object -First 1
$authDist  = Get-ChildItem -Path $Server -Recurse -Filter 'authserver.conf.dist'  | Select-Object -First 1
if (-not $worldDist -or -not $authDist) { Stop-Setup "Could not find worldserver/authserver .conf.dist under $Server" }

$newConfs = @()
foreach ($dist in @($worldDist, $authDist) + @(Get-ChildItem -Path $Server -Recurse -Filter '*.conf.dist' |
         Where-Object { $_.FullName -match '\\modules\\' })) {
    $conf = $dist.FullName -replace '\.dist$',''
    if (Test-Path $conf) { Skip "$(Split-Path $conf -Leaf) exists (kept your version)" }
    else { Copy-Item $dist.FullName $conf; $newConfs += $conf; Ok "Created $(Split-Path $conf -Leaf)" }
}
$worldConf = $worldDist.FullName -replace '\.dist$',''
$authConf  = $authDist.FullName  -replace '\.dist$',''
$mysqlExeQ = '"' + (Fwd (Join-Path $MySqlDir 'bin\mysql.exe')) + '"'
$srcQ      = '"' + (Fwd $Src) + '"'
if ($newConfs -contains $worldConf) {
    Set-ConfValue $worldConf 'DataDir'         ('"' + (Fwd $dataRoot) + '"')
    Set-ConfValue $worldConf 'MySQLExecutable' $mysqlExeQ
    Set-ConfValue $worldConf 'SourceDirectory' $srcQ
}
if ($newConfs -contains $authConf) {
    Set-ConfValue $authConf 'MySQLExecutable' $mysqlExeQ
    Set-ConfValue $authConf 'SourceDirectory' $srcQ
}
# The Unbound server's settings (cross-faction, level 60, scaling, ...), only on freshly created files.
if ($newConfs.Count) {
    Say 'Applying the Unbound server settings to the new config files...'
    & (Join-Path $Src 'modules\mod-unbound\server-setup\apply-unbound-settings.ps1') -ConfigDir (Split-Path $worldConf) -Only $newConfs
}

# Runtime DLLs next to the .exe files (only copied if missing)
$dlls = @(
    (Join-Path $MySqlDir 'lib\libmysql.dll'),
    (Get-ChildItem -Path $sslRoot -Recurse -Filter 'libssl-3-x64.dll'    | Select-Object -First 1).FullName,
    (Get-ChildItem -Path $sslRoot -Recurse -Filter 'libcrypto-3-x64.dll' | Select-Object -First 1).FullName,
    (Join-Path $sslRoot 'lib\ossl-modules\legacy.dll')   # required by OpenSSLCrypto.cpp on Windows
)
foreach ($dll in $dlls) {
    if (-not $dll -or -not (Test-Path $dll)) { Warn "DLL not found: $dll"; continue }
    $target = Join-Path $BinDir (Split-Path $dll -Leaf)
    if (Test-Path $target) { Skip "$(Split-Path $dll -Leaf) already next to worldserver.exe" }
    else { Copy-Item $dll $target; Ok "Copied $(Split-Path $dll -Leaf)" }
}

# Start / stop helpers
$startBat = Join-Path $Root 'Start Server.bat'
$stopBat  = Join-Path $Root 'Stop MySQL.bat'
if (-not (Test-Path $startBat)) {
@"
@echo off
title WoW Solo Server launcher
tasklist /FI "IMAGENAME eq mysqld.exe" | find /I "mysqld.exe" >nul
if errorlevel 1 (
  echo Starting MySQL...
  start "MySQL" /min "$mysqld" --defaults-file="$MyIni"
  timeout /t 8 /nobreak >nul
) else (
  echo MySQL already running.
)
echo Starting authserver...
start "authserver" /d "$BinDir" "$BinDir\authserver.exe"
timeout /t 3 /nobreak >nul
echo Starting worldserver...
start "worldserver" /d "$BinDir" "$BinDir\worldserver.exe"
"@ | Set-Content -Path $startBat -Encoding ASCII
    Ok "Created '$startBat'"
} else { Skip "'Start Server.bat' exists (kept)" }
if (-not (Test-Path $stopBat)) {
@"
@echo off
echo First type  server shutdown 5  in the worldserver window and close authserver.
echo Then enter the MySQL root password here to stop MySQL cleanly.
"$(Join-Path $MySqlDir 'bin\mysqladmin.exe')" -u root -p --host=localhost shutdown
pause
"@ | Set-Content -Path $stopBat -Encoding ASCII
    Ok "Created '$stopBat'"
} else { Skip "'Stop MySQL.bat' exists (kept)" }
$rebuildBat = Join-Path $Root 'Rebuild Server.bat'
if (-not (Test-Path $rebuildBat)) {
@"
@echo off
rem Rebuilds AzerothCore (picks up new modules and code changes in azerothcore\modules) and installs into server\.
rem Stop worldserver and authserver first. Log goes to logs\rebuild-<timestamp>.log
setlocal
set ROOT=$Root
call "$vcvars" >nul 2>&1 || (echo Could not load the Visual Studio build environment & exit /b 1)
set BOOST_ROOT=%ROOT%/deps/boost_1_83_0
set PATH=%ROOT%\deps\ninja;$(Split-Path $cmake);%PATH%
for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set TS=%%t
set LOG=%ROOT%\logs\rebuild-%TS%.log
echo Rebuilding... log: %LOG%
cmake -S "%ROOT%\azerothcore" -B "%ROOT%\build" > "%LOG%" 2>&1 || goto fail
cmake --build "%ROOT%\build" --parallel $BuildJobs >> "%LOG%" 2>&1 || goto fail
cmake --install "%ROOT%\build" >> "%LOG%" 2>&1 || goto fail
echo Rebuild finished OK.
pause
exit /b 0
:fail
echo Rebuild FAILED - see %LOG%
pause
exit /b 1
"@ | Set-Content -Path $rebuildBat -Encoding ASCII
    Ok "Created '$rebuildBat'"
} else { Skip "'Rebuild Server.bat' exists (kept)" }
$sheet = Join-Path $Root 'Server Cheat Sheet.md'
if (-not (Test-Path $sheet)) {
    Copy-Item (Join-Path $Src 'modules\mod-unbound\server-setup\Server Cheat Sheet.md') $sheet
    Ok "Created '$sheet'"
}

# ---------------------------------------------------------------- 11
Write-Step 11 'Game client (optional): addons and the custom client patch'
Say 'Your 3.3.5a client must be a copy of the Unbound client (with its visual patch packs).'
$client = Read-Host '  Path to your WoW 3.3.5a client folder (the one with Wow.exe), or Enter to skip'
if (-not $client) {
    Skip 'Client step skipped. See the mod-unbound README (Setting up the client) to do it later.'
} elseif (-not (Test-Path (Join-Path $client 'Wow.exe'))) {
    Warn "No Wow.exe in '$client'. Skipped; see the mod-unbound README (Setting up the client)."
} else {
    $addons = Join-Path $client 'Interface\AddOns'
    New-Item -ItemType Directory -Force -Path $addons | Out-Null
    foreach ($a in @((Join-Path $Src 'modules\mod-unbound\addon\Unbound'),
                     (Join-Path $Src 'modules\mod-transmog-plus\addon\Transmog'))) {
        Copy-Item -Recurse -Force $a $addons
        Ok "Installed addon $(Split-Path $a -Leaf)"
    }
    $py = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $py) {
        Warn 'Python 3 was not found, so the client patch (patch-Z.MPQ) was not built. Install Python 3 and run:'
        Say "  python `"$Src\modules\mod-unbound\tools\custom_dbc.py`" --client `"$client`" --dbc `"$dataRoot\dbc`""
    } else {
        Invoke-Native -Exe $py.Source -Arguments @((Join-Path $Src 'modules\mod-unbound\tools\custom_dbc.py'),
            '--client', $client, '--dbc', (Join-Path $dataRoot 'dbc')) -Log $BuildLog
        Ok 'Built the client patch (Data\patch-Z.MPQ)'
    }
}

# ---------------------------------------------------------------- done
Write-Host ''
Write-Host ('=' * 70) -ForegroundColor Green
Write-Host '  SETUP COMPLETE' -ForegroundColor Green
Write-Host ('=' * 70) -ForegroundColor Green
Say "Server programs : $BinDir"
Say "Config files    : $(Split-Path $worldConf)"
Say "Client data     : $dataRoot"
Say "Databases       : $($Databases -join ', ')  (user acore / acore)"
Say "Logs            : $Logs"
Say ''
Say "Next: double-click 'Start Server.bat' in $Root."
Say 'The FIRST worldserver start fills the databases and takes several minutes.'

} catch {
    Write-Host ''
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Nothing was deleted. Send Claude the newest files in $Logs" -ForegroundColor Red
    try { Stop-Transcript | Out-Null } catch {}
    exit 1
}
try { Stop-Transcript | Out-Null } catch {}
