import requests

url = "https://bibliaapi.com.br/api/v2/versions/ACF/books/mt/chapters/5/verses/6"

headers = {
    "Authorization": "Bearer bapi_awv4y0a9sxv1iqstzy47elxutixydzit9aga278srdtl3z6n"
}

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.json())