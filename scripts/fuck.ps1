if ((Get-Command "fuck").CommandType -eq "Function") {
	fuck @args;
	[Console]::ResetColor()
	exit
}

"First time use of fuck detected. "
$app = Get-Command fuck -CommandType Application -ErrorAction SilentlyContinue
if (-not $app) {
	"fuck executable not found in PATH."
	exit 1
}

if ((Get-Content $PROFILE -Raw -ErrorAction Ignore) -like "*fuck --alias*") {
} else {
	"  - Adding fuck initialization to user `$PROFILE"
	$script = "`n`$env:PYTHONIOENCODING='utf-8' `niex `"`$(& `"$($app.Source)`" --alias)`"";
	Write-Output $script | Add-Content $PROFILE
}

"  - Adding fuck() function to current session..."
$env:PYTHONIOENCODING='utf-8'
iex "$((& `"$($app.Source)`" --alias).Replace("function fuck", "function global:fuck"))"

"  - Invoking fuck()`n"
& $app.Source @args;
[Console]::ResetColor()
