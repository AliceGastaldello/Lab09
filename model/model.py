from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi
        self.escursioni_parco = []
        self.max_giorni = None
        self.max_budget = None

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        # TODO

        self.relazioni = EscursioneDAO.get_escursioni_punti_interesse()
        for r in self.relazioni:
            #id_esc = r["id_escursione"]
            #id_punto = r["id_punto_interesse"]

            # Per ogni riga leggo i due id e
            # li trasformo in due oggetti: escursione e punto
            escursione = self.escursioni_map[r["id_escursione"]]
            punto = self.punti_interesse_map[r["id_punto_interesse"]]

            # Vado a riempire i set con le varie relazioni
            escursione.punti_interesse.add(punto)
            punto.escursioni.add(escursione)


    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        # TODO
        if max_budget is not None: # controllo che l'utente abbia inserito il budget
            self.max_budget = float("inf") # nessun limite
        else:
            self.max_budget = max_budget # imposto quel valore

        # Faccio lo stesso per i giorni:
        if max_giorni is not None:
            self.max_giorni = float("inf")
        else:
            self.max_giorni = max_giorni

        for escursione in self.escursioni_map.values():
            if escursione.id_parco == id_parco: # controllo se l'escursione selezionata è valida
                self.escursioni_parco.append(escursione) # se è cosi l'aggiungo alla lista

        parziale = []
        # chiamo la ricorsione e gli passo tutti i parametri richiesti
        self._ricorsione(0,parziale, 0, 0.0,0, set())

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno

        if valore_corrente > self._valore_ottimo: # controllo se il valore corrente è maggiore della soluzione salvata in precedenza
            self._valore_ottimo = valore_corrente  # se sì lo aggiorno
            self._pacchetto_ottimo = pacchetto_parziale.copy()  # copio la lista del pacchetto
            self._costo = costo_corrente  # registro il costo totale

        # condizione di terminazione: se abbiamo esaminato tutte le escursioni del parco
        if start_index >= len(self.escursioni_parco):
            return

        escursione_corrente = self.escursioni_parco[start_index] # seleziono l'escursione corrente in base a all'indice di avanzamento della ricorsione

        # Verifico se l'escursione ha punti di interesse già usati nel pacchetto
        sovrapposizione = False
        for p in escursione_corrente.punti_interesse:
            if p.id in punti_usati:
                sovrapposizione = True
                break # se c'è anche solo una sovrapposizione la scarto

        # Controllo i vincoli: non devo violare il limite dei giorni, il budget massimo e che non creare conflitti sui punti di interesse
        if (durata_corrente + escursione_corrente.durata_giorni <= self.max_giorni) and (costo_corrente + escursione_corrente.costo <= self.max_budget) and (not sovrapposizione):
            pacchetto_parziale.append(escursione_corrente) # aggiungo l'escursione nella soluzione parziale

            nuovi_punti_usati = punti_usati.copy() # aggiorno i punti usati e il valore su una copia del set
            nuovo_valore = valore_corrente
            for p in escursione_corrente.punti_interesse:
                nuovi_punti_usati.add(p.id)
                nuovo_valore += p.voto_visitatori

            # Chiamata ricorsiva aggiornando i contatori
            self._ricorsione(start_index + 1, pacchetto_parziale,
                             durata_corrente + escursione_corrente.durata_giorni,
                             costo_corrente + escursione_corrente.costo,
                             nuovo_valore, nuovi_punti_usati)

            # Backtracking: rimuovo l'ultima escursione per valutare altri percorsi
            pacchetto_parziale.pop()

        # Avanzo all'indice successivo con la ricorsione (la eseguo sempre)
        self._ricorsione(start_index + 1, pacchetto_parziale,
                         durata_corrente, costo_corrente,
                         valore_corrente, punti_usati)
