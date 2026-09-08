param(
    [switch]$Plain
)

# AgentShield AI - premium terminal welcome banner (PowerShell).
#
# A boxed, truecolour invocation screen in the house style of the Doctors-CLI
# banner: an auto-padded 78-column frame (Bx/Hr helpers strip ANSI before the
# width maths), a cyan-to-green gradient AGENTSHIELD wordmark with a magenta
# "A I" mark, the security tagline + PREDICT / GOVERN / APPROVE / EXECUTE SAFELY
# / AUDIT workflow line, the numbered 1-8 intake menu, the runtime decision
# badges, and an evidence/authority panel.
#
# Colour is ON by default (24-bit SGR). Opt out with -Plain, or by setting
# NO_COLOR / AGENTSHIELD_NO_COLOR - the box then renders in clean monochrome,
# which is also the canonical layout reference.
#
#   powershell -File scripts/agentshield_banner.ps1 [-Plain]

$useColor = -not ($Plain -or $env:NO_COLOR -or $env:AGENTSHIELD_NO_COLOR)

# Make box-drawing glyphs render on legacy Windows consoles, and turn on ANSI
# escape interpretation (ENABLE_VIRTUAL_TERMINAL_PROCESSING). Both degrade
# gracefully to no-ops on modern terminals / non-Windows hosts.
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}
if ($env:OS -eq 'Windows_NT') {
    try {
        $sig = '[DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr h, uint m); [DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int n);'
        $k = Add-Type -MemberDefinition $sig -Name AgentShieldVT -Namespace Win32 -PassThru -ErrorAction Stop
        $k::SetConsoleMode($k::GetStdHandle(-11), 7) | Out-Null
    } catch {}
}

$e = [char]27
if ($useColor) {
    $P  = "$e[38;2;163;113;247m"  # purple  - frame / headers
    $V  = "$e[38;2;137;87;229m"   # violet  - tagline
    $B  = "$e[38;2;88;166;255m"   # blue    - url
    $C  = "$e[38;2;57;208;216m"   # cyan    - motif / bullets / arrows
    $L  = "$e[38;2;201;209;217m"  # light   - body
    $M  = "$e[38;2;139;148;158m"  # muted   - secondary
    $Y  = "$e[38;2;255;199;30m"   # yellow  - warning
    $Gn = "$e[38;2;63;208;120m"   # green   - ALLOW
    $O  = "$e[38;2;255;150;60m"   # orange  - ESCALATE
    $Rd = "$e[38;2;255;90;90m"    # red     - DENY
    $A  = "$e[38;2;255;199;30m"   # amber   - APPROVE
    $MG = "$e[38;2;200;120;255m"  # magenta - the "A I" mark
    $W  = "$e[38;2;240;244;250m"  # white   - mode names
    # Wordmark gradient, top -> bottom (cyan -> green).
    $G1 = "$e[38;2;57;208;216m"
    $G2 = "$e[38;2;54;210;188m"
    $G3 = "$e[38;2;52;212;160m"
    $G4 = "$e[38;2;55;212;132m"
    $G5 = "$e[38;2;60;210;116m"
    $G6 = "$e[38;2;74;214;120m"
    $BD = "$e[1m"
    $R  = "$e[0m"
} else {
    $P = ''; $V = ''; $B = ''; $C = ''; $L = ''; $M = ''; $Y = ''
    $Gn = ''; $O = ''; $Rd = ''; $A = ''; $MG = ''; $W = ''
    $G1 = ''; $G2 = ''; $G3 = ''; $G4 = ''; $G5 = ''; $G6 = ''
    $BD = ''; $R = ''
}

$WIDTH = 78
$ansi = [regex]'\x1b\[[0-9;]*m'

function Bx($c) {
    $vis = $ansi.Replace($c, '')
    $pad = $WIDTH - $vis.Length
    if ($pad -lt 0) { $pad = 0 }
    [Console]::WriteLine("$P$([char]0x2551)$R$c$R$(' ' * $pad)$P$([char]0x2551)$R")
}
function Hr($left, $right) {
    [Console]::WriteLine("$P$left$([string]([char]0x2550) * $WIDTH)$right$R")
}

# ---- wordmark rows (single-quoted: backslash / backtick / pipe are literal) --
$w0 = '           _____ ______ _   _ _______ _____ _    _ _____ ______ _      _____'
$w1 = '     /\   / ____|  ____| \ | |__   __/ ____| |  | |_   _|  ____| |    |  __ \'
$w2 = '    /  \ | |  __| |__  |  \| |  | | | (___ | |__| | | | | |__  | |    | |  | |'
$w3 = '   / /\ \| | |_ |  __| | . ` |  | |  \___ \|  __  | | | |  __| | |    | |  | |'
$w4 = '  / ____ \ |__| | |____| |\  |  | |  ____) | |  | |_| |_| |____| |____| |__| |'
$w5 = ' /_/    \_\_____|______|_| \_|  |_| |_____/|_|  |_|_____|______|______|_____/'

[Console]::WriteLine("")
Hr ([char]0x2554) ([char]0x2557)                      # top border
Bx ""
Bx ($G1 + $w0 + $R)
Bx ($G2 + $w1 + $R)
Bx ($G3 + $w2 + $R)
Bx ($G4 + $w3 + $R)
Bx ($G5 + $w4 + $R)
Bx ($G6 + $w5 + $R)
Bx ""
Bx ("                                  $MG$BD" + "A  I" + "$R")
Bx ""
Bx ("        $BD$V" + "The Security Control Plane for the Agentic Enterprise" + "$R")
Bx ""
Bx ("        $C" + "PREDICT  " + [char]0x00B7 + "  GOVERN  " + [char]0x00B7 + "  APPROVE  " + [char]0x00B7 + "  EXECUTE SAFELY  " + [char]0x00B7 + "  AUDIT" + "$R")
Bx ""
Bx ("        ${L}Version $BD${P}1.0.0$R$L   $M" + [char]0x00B7 + "$R$L   Deterministic " + [char]0x00B7 + " versioned " + [char]0x00B7 + " fail-closed$R")
Bx ("   $B" + "https://agentshield.calmfield-da2f25f9.centralindia.azurecontainerapps.io" + "$R")
Bx ("        $M" + "github.com/Mausam-00/AgentShield" + "$R")
Bx ""

Hr ([char]0x2560) ([char]0x2563)                      # section rule
Bx ""
Bx ("   $BD$P" + [char]0x2726 + " WHAT IT DOES" + "$R")
Bx ("       $C" + [char]0x25B8 + "$R ${L}ASSESS agents " + [char]0x00B7 + " OBSERVE actions " + [char]0x00B7 + " GOVERN with 7 deterministic gates$R")
Bx ("       $C" + [char]0x25B8 + "$R ${L}RED-TEAM " + [char]0x00B7 + " RESPONSIBLE AI (6 pillars) " + [char]0x00B7 + " VALIDATE " + [char]0x00B7 + " REPORT$R")
Bx ("       $C" + [char]0x25B8 + "$R ${L}Every decision recorded, versioned, and evidence-bound$R")
Bx ""
Bx ("   $BD$P" + [char]0x2699 + " LOADED" + "$R")
Bx ("       ${L}7 gates " + [char]0x00B7 + " 21 controls " + [char]0x00B7 + " 6 RAI pillars " + [char]0x00B7 + " 9 red-team families$R")
Bx ""
Bx ("   ${Gn}[ ALLOW ]$R  $C[ TRANSFORM ]$R  $A[ APPROVE ]$R  $O[ ESCALATE ]$R  $Rd[ DENY ]$R")
Bx ""

Hr ([char]0x2560) ([char]0x2563)                      # section rule
Bx ""
Bx ("   $BD$Y" + [char]0x26A0 + " ASSURANCE " + [char]0x2260 + " AUTHORIZATION" + "$R")
Bx ("       $C" + [char]0x25B8 + "$R ${L}PASS is not certification " + [char]0x00B7 + " WARN is not approval$R")
Bx ("       $C" + [char]0x25B8 + "$R ${L}Missing evidence lowers confidence " + [char]0x2014 + " it is never invented$R")
Bx ("       $C" + [char]0x25B8 + "$R ${L}Fail-closed on unknown identity, unavailable policy, invalid approval$R")
Bx ("       $C" + [char]0x25B8 + "$R ${L}Deterministic, versioned policy is the only authority$R")
Bx ""
Bx ("   $BD$Y" + [char]0x26A1 + " AI advises " + [char]0x2014 + " it never authorizes." + "$R$L  Always verify findings.$R")
Bx ""
Bx ("   ${M}Quick start:$R ${L}Assess ~/.copilot/Agents/dr-dnd.agent.md$R")
Bx ("   $C$BD" + "Describe your goal to begin." + "$R$L" + "  Type 'menu' for the full mode list." + "$R")
Bx ""
Hr ([char]0x255A) ([char]0x255D)                      # bottom border
[Console]::WriteLine("")
