# Запускает pytest с отчетом покрытия и генерирует HTML-отчет
pytest --maxfail=1 --disable-warnings --cov=src --cov-report=term-missing --cov-report=html
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed or coverage collection failed. Exit code: $LASTEXITCODE"
    exit $LASTEXITCODE
}
Write-Output "Coverage report generated in ./htmlcov/index.html"
