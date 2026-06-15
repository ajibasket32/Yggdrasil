param(
    [ValidateSet("all", "integration", "regression")]
    [string] $Suite = "all",
    [switch] $SkipBuild,
    [switch] $KeepServices,
    [switch] $NoSeedCheck
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$ComposeBase = @("compose", "--env-file", ".env.test", "-f", "compose.test.yaml")

function Invoke-Compose {
    param([string[]] $ComposeArgs)

    Write-Host "docker $($ComposeBase + $ComposeArgs -join ' ')"
    & docker @ComposeBase @ComposeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose failed: $($ComposeArgs -join ' ')"
    }
}

function Invoke-TestRunner {
    param([Parameter(Mandatory = $true)][string] $Command)

    Invoke-Compose @("run", "--rm", "backend-test", "sh", "-lc", $Command)
}

$pytestTargets = switch ($Suite) {
    "integration" { "../tests/integration" }
    "regression" { "../tests/regression" }
    default { "../tests/integration ../tests/regression" }
}

try {
    if ($SkipBuild) {
        Invoke-Compose @("up", "-d", "postgres", "redis", "qdrant")
    } else {
        Invoke-Compose @("up", "-d", "--build", "postgres", "redis", "qdrant")
        Invoke-Compose @("build", "backend-test")
    }

    Invoke-TestRunner "poetry run alembic -c alembic.ini upgrade head"

    if (-not $NoSeedCheck) {
        Invoke-TestRunner "python /tools/verify_test_seed_data.py"
    }

    Invoke-TestRunner "poetry run pytest -c pyproject.toml $pytestTargets"
} finally {
    if (-not $KeepServices) {
        & docker @ComposeBase down -v --remove-orphans
    }
}
