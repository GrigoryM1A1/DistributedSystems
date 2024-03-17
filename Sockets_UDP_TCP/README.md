# Chat
Prosty chat napisany w Pythonie z wykorzystaniem socketów UDP i TCP przewidziany do ewentualnego
korzystania na Windowsie - na innych platformach mogą pojawić się jakieś problemy,
ale też nie muszą (nietestowane).

### Klient
Wchodzimy w katalog z plikiem client.py i wpisujemy poniższą komendę:
`python client.py`

### Serwer
Wchodzimy w katalog z plikiem server.py i wpisujemy poniższą komendę:
`python server.py`

## Interakcje
### Klient
- po włączeniu klienta, ustawiamy swój nick
- wprowadzając "U" wyślemy prostego ASCII_ARTa poprzez UDP do wszystkich użytkowników przez serwer
- wprowadzając "M" wyślemy prostego ASCII_ARTa poprzez Multicast do wszystkich użtkowników bezpośrednio
- w każdym innym przypadku wiadomości będą wysyłane to wszystki przez serwer przy pomocy TCP
- wychodzimy wproawdzając "Q" lub Ctrl+C

### Serwer
- poza włączeniem jedyną interakcją jest wyłączenie go poprzez Ctrl+C
