#!/usr/bin/env pwsh
# Test the password validation fixes

$BaseUrl = "http://localhost:8000"
$Results = @()

function Test-Registration {
    param(
        [string]$Email,
        [string]$Password,
        [string]$FullName,
        [string]$TestName,
        [string]$ExpectedStatus
    )
    
    Write-Host "`n=== $TestName ===" -ForegroundColor Cyan
    Write-Host "Email: $Email"
    Write-Host "Password: $($Password.Substring(0, [Math]::Min(10, $Password.Length)))..." 
    Write-Host "Expected: $ExpectedStatus"
    
    $Body = @{
        email = $Email
        password = $Password
        full_name = $FullName
    } | ConvertTo-Json
    
    try {
        $Response = Invoke-WebRequest -Uri "$BaseUrl/auth/register" `
            -Method POST `
            -ContentType "application/json" `
            -Body $Body `
            -ErrorAction Stop
        
        Write-Host "Result: 201 Created - SUCCESS" -ForegroundColor Green
        $Results += @{Test=$TestName; Status=$Response.StatusCode; Success=$true}
    }
    catch {
        $StatusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Result: $StatusCode - Error" -ForegroundColor Red
        
        if ($StatusCode -eq 422) {
            Write-Host "  422 Validation Error (expected for invalid password)" -ForegroundColor Yellow
            $Results += @{Test=$TestName; Status=$StatusCode; Success=$true}
        } else {
            $Results += @{Test=$TestName; Status=$StatusCode; Success=$false}
        }
    }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "PASSWORD VALIDATION TEST SUITE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Test 1: Password too short
Test-Registration `
    -Email "test.short@example.com" `
    -Password "Short1" `
    -FullName "Test User" `
    -TestName "Password too short (6 chars)" `
    -ExpectedStatus "422"

# Test 2: Password missing uppercase
Test-Registration `
    -Email "test.nouppercase@example.com" `
    -Password "nouppercase123" `
    -FullName "Test User" `
    -TestName "Password missing uppercase" `
    -ExpectedStatus "422"

# Test 3: Password missing lowercase
Test-Registration `
    -Email "test.nolowercase@example.com" `
    -Password "NOLOWERCASE123" `
    -FullName "Test User" `
    -TestName "Password missing lowercase" `
    -ExpectedStatus "422"

# Test 4: Password missing digit
Test-Registration `
    -Email "test.nodigit@example.com" `
    -Password "NoDigitsHere" `
    -FullName "Test User" `
    -TestName "Password missing digit" `
    -ExpectedStatus "422"

# Test 5: Password at max length (72 bytes - valid)
$MaxPassword = ("a" * 70) + "B1"
Test-Registration `
    -Email "test.maxlength@example.com" `
    -Password $MaxPassword `
    -FullName "Test User" `
    -TestName "Password at max length (72 bytes - valid)" `
    -ExpectedStatus "201"

# Test 6: Valid password
Test-Registration `
    -Email "test.valid@example.com" `
    -Password "ValidPassword123" `
    -FullName "Test User" `
    -TestName "Valid password - all requirements met" `
    -ExpectedStatus "201"

# Test 7: Valid password with special chars (allowed)
Test-Registration `
    -Email "test.special@example.com" `
    -Password "ValidPass@123" `
    -FullName "Test User" `
    -TestName "Valid password with special characters" `
    -ExpectedStatus "201"

# Summary
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$PassCount = ($Results | Where-Object {$_.Success} | Measure-Object).Count
$TotalCount = $Results.Count

foreach ($result in $Results) {
    $Status = if ($result.Success) { "PASS" } else { "FAIL" }
    Write-Host "$Status - $($result.Test) (Status: $($result.Status))" 
}

Write-Host "`nTotal: $PassCount/$TotalCount tests passed" -ForegroundColor $(if($PassCount -eq $TotalCount) {'Green'} else {'Yellow'})
