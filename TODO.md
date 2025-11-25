# Task: Improve Dashboard Report Exports and Add Download History

## Steps

- [ ] Add ReportDownloadHistory model to App/models.py to store user downloads with filters and format
- [ ] Create ExportReportView in App/views/dashboard.py to show export form with filters and format selection
- [ ] Create template templates/dashboard/export_report.html for export form UI
- [ ] Update reporte_csv and reporte_pdf views to:
    - Accept POST requests with filters
    - Filter queryset accordingly
    - Log downloads in ReportDownloadHistory
    - Return CSV or PDF file response
- [ ] Modify templates/dashboard/dashboard_report_list.html
    - Replace direct export buttons with link or embed export form component
- [ ] Create DownloadHistoryView in App/views/dashboard.py to display logged downloads
- [ ] Create templates/dashboard/download_history.html for download history page
- [ ] Update App/urls.py with new routes for export form and download history page
- [ ] Thoroughly test
