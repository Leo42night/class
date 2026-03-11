# API Classroom
```bash
ppwl\Scripts\activate.bat
```
## Installation
```bash
pip install pandas google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

requirement for `comment.py`
```bash
pip install google-api-python-client google-auth google-auth-oauthlib
```


format credentials (format Service Account) yang benar:
> **IAM & Admin → Service Accounts**
Setelah dibuat Service Accounts, masuk:
```
Keys
→ Add Key
→ Create new key
→ JSON
```
```json
{
  "type": "service_account",
  "project_id": "my-project",
  "private_key_id": "xxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n....\n-----END PRIVATE KEY-----\n",
  "client_email": "my-service@my-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```
Tambahkan email ke file spreadsheet.