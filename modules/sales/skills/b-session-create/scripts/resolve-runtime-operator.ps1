param(
    [ValidateSet("feishu_self", "manual_confirmed", "external_runtime", "unknown")]
    [string]$IdentitySource = "unknown",

    [string]$SalesId = "",

    [string]$SalesName = "",

    [string]$IdentityRef = "",

    [ValidateSet("user", "bot")]
    [string]$As = "user",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($IdentitySource -eq "feishu_self") {
    $argsList = @(
        "contact", "+search-user",
        "--user-ids", "me",
        "--format", "json",
        "--as", $As
    )
    if ($DryRun) {
        $argsList += "--dry-run"
        & lark-cli @argsList
        return
    }

    $raw = & lark-cli @argsList
    $data = $raw | ConvertFrom-Json
    $user = $null
    if ($data.users -and $data.users.Count -gt 0) {
        $user = $data.users[0]
    }
    elseif ($data.data -and $data.data.users -and $data.data.users.Count -gt 0) {
        $user = $data.data.users[0]
    }

    if ($null -eq $user) {
        throw "Unable to resolve Feishu self identity from lark-cli output."
    }

    $openId = [string]$user.open_id
    $displayName = [string]$user.localized_name
    if ([string]::IsNullOrWhiteSpace($displayName)) {
        $displayName = [string]$user.name
    }
    if ([string]::IsNullOrWhiteSpace($SalesId)) {
        $SalesId = $openId
    }
    if ([string]::IsNullOrWhiteSpace($SalesName)) {
        $SalesName = $displayName
    }
    $IdentityRef = "feishu_open_id=$openId"

    [ordered]@{
        identity_verified = $true
        identity_source = $IdentitySource
        identity_ref = $IdentityRef
        sales_id = $SalesId
        sales_name = $SalesName
    } | ConvertTo-Json -Depth 4
    return
}

if ($IdentitySource -eq "unknown") {
    [ordered]@{
        identity_verified = $false
        identity_source = $IdentitySource
        identity_ref = ""
        sales_id = $SalesId
        sales_name = $SalesName
        required_session_status = "need_confirm"
        reason = "Codex session id does not prove operator identity."
    } | ConvertTo-Json -Depth 4
    return
}

if ([string]::IsNullOrWhiteSpace($SalesId)) {
    throw "SalesId is required for manual_confirmed or external_runtime."
}
if ([string]::IsNullOrWhiteSpace($SalesName)) {
    throw "SalesName is required for manual_confirmed or external_runtime."
}
if ([string]::IsNullOrWhiteSpace($IdentityRef)) {
    throw "IdentityRef is required for manual_confirmed or external_runtime."
}

[ordered]@{
    identity_verified = $true
    identity_source = $IdentitySource
    identity_ref = $IdentityRef
    sales_id = $SalesId
    sales_name = $SalesName
} | ConvertTo-Json -Depth 4
