param(
    [Parameter(Mandatory = $true)]
    [string]$Keyword,

    [ValidateSet("All", "Alias", "SourceId", "Master")]
    [string]$SearchMode = "All",

    [string]$MasterBaseToken = "TqVmbOv2faej8MsJtkSccIv2nKb",
    [string]$MasterTableId = "tblT0pxNirTRQw9H",

    [string]$SourceBaseToken = "IJK4bY3HhaWFcnsqwUncAV9rnje",
    [string]$SourceTableId = "tbl2fHDgqP7f4gyq",

    [string]$AliasBaseToken = "H5A7bXQtJaCVd0sqIircwepYnYf",
    [string]$AliasTableId = "tbl86wHfHgKpjfJp",

    [int]$Limit = 20,

    [ValidateSet("user", "bot")]
    [string]$As = "bot",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($Keyword)) {
    throw "Keyword is required."
}
if ($Limit -lt 1 -or $Limit -gt 200) {
    throw "Limit must be between 1 and 200."
}

$Contracts = [ordered]@{
    Master = [ordered]@{
        line = "A"
        table_name = "All_customer_files|A-line all customer files"
        base_token = $MasterBaseToken
        table_id = $MasterTableId
        field_ids = [ordered]@{
            customer_id = "fld3zQdj2W"
            customer_name = "fldCXrp4EA"
            company_name = "fldn06FZxa"
            phone = "fld8SKqgSv"
            wecom_id = "fldUHaTdCD"
            wechat_id = "fldoKLamfO"
            source_id = "fldwwN3g9g"
            latest_snapshot_text = "fldX0yjRMb"
            latest_snapshot_json = "fldpzf6zst"
            individual_customer_table_url = "fldaLCJY97"
        }
        search_fields = @("customer_id", "customer_name", "company_name", "phone", "wecom_id", "wechat_id", "source_id")
        select_fields = @("customer_id", "customer_name", "company_name", "phone", "wecom_id", "wechat_id", "source_id", "current_stage", "current_status", "customer_rating", "latest_snapshot_text", "latest_snapshot_json", "individual_customer_table_url")
    }
    SourceId = [ordered]@{
        line = "A"
        table_name = "source_id_mapping"
        base_token = $SourceBaseToken
        table_id = $SourceTableId
        field_ids = [ordered]@{
            source_id = "fldWa3J7CZ"
            linked_customer_id = "fld1YjyVai"
            candidate_customer_ids = "fldIStQwyg"
            raw_customer_name = "fld0v1zjA9"
            raw_phone = "fldY4ZgNxG"
        }
        search_fields = @("source_id", "raw_customer_name", "raw_phone", "linked_customer_id", "candidate_customer_ids")
        select_fields = @("source_map_id", "source_id", "raw_customer_name", "raw_phone", "linked_customer_id", "candidate_customer_ids", "mapping_status", "source_type", "source_department")
    }
    Alias = [ordered]@{
        line = "A"
        table_name = "customer_alias_mapping"
        base_token = $AliasBaseToken
        table_id = $AliasTableId
        field_ids = [ordered]@{
            alias_value = "fldvJB2XZ5"
            normalized_alias = "fldiBLwK1U"
            customer_id = "fldbTJ7xWS"
            confidence_score = "fldyBuDQYc"
            conflict_status = "fldWsjfsxj"
        }
        search_fields = @("alias_value", "normalized_alias", "customer_id")
        select_fields = @("alias_id", "alias_value", "normalized_alias", "customer_id", "alias_type", "source_type", "confidence_score", "conflict_status", "status")
    }
}

function Invoke-RecordSearch {
    param(
        [string]$Mode
    )

    $contract = $Contracts[$Mode]
    $payload = [ordered]@{
        keyword = $Keyword
        search_fields = $contract.search_fields
        select_fields = $contract.select_fields
        limit = $Limit
    }

    $json = $payload | ConvertTo-Json -Compress -Depth 8
    $tmpDirName = ".lark-tmp"
    $tmpDir = Join-Path (Get-Location).Path $tmpDirName
    $jsonFileName = "$([System.Guid]::NewGuid().ToString('N')).json"
    $jsonFile = Join-Path $tmpDir $jsonFileName
    $jsonFileArg = "@$tmpDirName/$jsonFileName"

    try {
        if (-not (Test-Path -LiteralPath $tmpDir)) {
            New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
        }
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($jsonFile, $json, $utf8NoBom)

        $argsList = @(
            "base", "+record-search",
            "--base-token", $contract.base_token,
            "--table-id", $contract.table_id,
            "--json", $jsonFileArg,
            "--format", "json",
            "--as", $As
        )
        if ($DryRun) {
            $argsList += "--dry-run"
        }

        Write-Output "=== $Mode : $($contract.line) / $($contract.table_name) / $($contract.table_id) ==="
        & lark-cli @argsList
    }
    finally {
        if (Test-Path -LiteralPath $jsonFile) {
            Remove-Item -LiteralPath $jsonFile -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -LiteralPath $tmpDir) {
            $remaining = @(Get-ChildItem -LiteralPath $tmpDir -Force -ErrorAction SilentlyContinue)
            if ($remaining.Count -eq 0) {
                Remove-Item -LiteralPath $tmpDir -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

if ($SearchMode -eq "All") {
    Invoke-RecordSearch -Mode "Alias"
    Invoke-RecordSearch -Mode "SourceId"
    Invoke-RecordSearch -Mode "Master"
}
else {
    Invoke-RecordSearch -Mode $SearchMode
}
