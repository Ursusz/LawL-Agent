## Configurare Locala

### Cerinte

* **Python >= 3.12**
* **Node.js** de [aici](https://nodejs.org/en/download)
* **uv** - Se poate instala cu `pipx` pentru a evita conflictele de sistem:
    ```bash
    pipx install uv
    ```
* **antiword** - sudo apt-get update && sudo apt-get install antiword

***

### 1. Configure Backend

#### Google Gemini API KEY -> https://aistudio.google.com/app/apikey

#### Brave Search API KEY -> https://brave.com/search/api/

#### Google Drive API KEY -> https://developers.google.com/workspace/drive/api/guides/about-sdk

 > In folderul backend se va crea un fisier **.env** cu urmatorul continut:

```
GEMINI_API_KEY=your_api_key
BRAVE_SEARCH_API_KEY=your_api_key
```

 ### Tutorial Google Drive API KEY: TODO
```

1. 
    ```bash
    cd backend
    ```
2. 
    ```bash
    uv venv lawl
    source lawl/bin/activate
    ```
3. 
    ```bash
    uv pip install -r requirements.lock
    ```
4.
    ```bash
    uv run python -m uvicorn src.main:app --reload
    ```
    Serverul va porni pe `http://127.0.0.1:8000`.

***

### 2. Configurare Frontend

1. 
    ```bash
    cd ../frontend
    ```
2.
    ```bash
    npm install
    ```
3.
    ```bash
    npm start
    ```
    Aplicatia se va deschide pe `http://localhost:3000`.

***

### 3. Rulare Teste

#### Backend

1. Navigheaza in folderul `backend`:
    ```bash
    cd backend
    ```
2. Activeaza mediul virtual (daca nu este deja activat):
    ```bash
    source lawl/bin/activate
    ```
3. Ruleaza testele:
    ```bash
    uv run python -m unittest discover tests
    ```

#### Frontend

1. Navigheaza in folderul `frontend`:
    ```bash
    cd frontend
    ```
2. Ruleaza testele unitare:
    ```bash
    npm test
    ```
    (Pentru a rula o singura data fara watch mode: `npm test -- --watchAll=false`)

3. Ruleaza testele end-to-end (Playwright):
    ```bash
    npm run test:e2e
    ```

4. Ruleaza toate testele cu coverage:
    ```bash
    npm run test:coverage:all
    ```
