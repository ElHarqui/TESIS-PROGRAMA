import requests
import json

cookies = {
    "JSESSIONID": "1DA424482E11CB22B8FD5F1C250E7CBB",
    "2e4302301d994214b74f1c6e9c6e2763": "WyIxNTg0NjA1ODA5Il0",
    "_ga": "GA1.1.2092739237.1721236380",
    "_ga_MD7V62YMSH": "GS2.3.s1750693277$o1$g0$t1750693277$j60$l0$h0",
    "HWWAFSESID": "08d877303822411e75",
    "HWWAFSESTIME": "1777513278205",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Referer": "https://sum.unmsm.edu.pe/alumnoWebSum/v2/matricula/programacion",
    "X-Requested-With": "AlumnoWebSum2026Q1",  # <-- la clave
    "Accept": "*/*",
    "Accept-Language": "es-ES,es;q=0.9",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

url = "https://sum.unmsm.edu.pe/alumnoWebSum/v2/matricula/programacion"
params = {"accion": "obtenerProgramacionAsignaturas"}

response = requests.get(url, cookies=cookies, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(f"Error {response.status_code}: {response.text}")