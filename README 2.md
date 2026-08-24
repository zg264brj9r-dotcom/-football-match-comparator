# ⚽ Football Match Comparator

Mobile-first Streamlit app for comparing football matches.

## Deploy
1. Create a GitHub repository.
2. Upload `streamlit_app.py`, `requirements.txt`, `.gitignore`, `.streamlit/config.toml`, and `README.md`.
3. Open Streamlit Community Cloud and create an app from the repository.
4. Select branch `main` and file `streamlit_app.py`.
5. Deploy.
6. Open the generated `streamlit.app` URL in Safari and add it to the Home Screen.

## API key
The current app asks for the API-Football key in the app interface. Do not commit the key to GitHub.
For a production deployment, move the key to Streamlit Secrets and read it from `st.secrets`.
