// TaskToAgent invoice logger -> Google Sheet (optional).
// 1. Open your Google Sheet > Extensions > Apps Script, paste this, Save.
// 2. Deploy > New deployment > Web app. Execute as: Me. Who has access: Anyone. Deploy, then copy the /exec URL.
// 3. Put that URL in SHEET_WEBHOOK_URL. Keep it private: anyone with it can add rows.
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  if (sheet.getLastRow() === 0) sheet.appendRow(["date","vendor","amount","currency","invoice_no","subject","from","attachments","source","key"]);
  var rows = JSON.parse(e.postData.contents).rows || [];
  rows.forEach(function (r) { sheet.appendRow(r); });
  return ContentService.createTextOutput(JSON.stringify({ ok: true, added: rows.length })).setMimeType(ContentService.MimeType.JSON);
}
