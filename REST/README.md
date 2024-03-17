# Sprawdzanie statystyk graczy i pojazdów w grze World of Tanks
Proste RESTful API, które pozwala na sprawdzanie podstawowych statystyk kont graczy w WoT, a także
na sprawdzanie statystyk poszczególnych pojazdów.

Dla urozmaicenia dodany jest też przycisk, który wyświetla nam różne bezużyteczne fakty zupełnie niepowiązane z grą.

Żeby mieć dostęp do możliwości api, najpierwe trzeba się zalogować na przykłądowe konto:
```
Username: grzegorz
Password: 12345
```

# Jak korzystać?
Kiedy mamy już wszystkie pliki projektu w folderze, to tworzymy wirtualne środowisko:

`
python -m venv venv
`

Następnie aktywujemy je:

`
venv/Scripts/activate
`

Instalujemy requirements:

`
pip install -r requirements.txt
`

Odpalamy serwer znajdując się w folderze WotApi:

`
python main.py
`