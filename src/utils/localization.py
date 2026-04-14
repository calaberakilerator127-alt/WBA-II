class Localization:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Localization, cls).__new__(cls)
            cls._instance.lang = "es"
            cls._instance.strings = {
                "es": {
                    "btn_back": "VOLVER",
                    "btn_confirm": "CONFIRMAR",
                    "btn_cancel": "CANCELAR",
                    "msg_insufficient_brawels": "Brawels insuficientes",
                    "msg_level_up": "¡NIVEL UP!",
                    "msg_xp_gained": "XP Ganados",
                    "gym_title": "GIMNASIO DE ÉLITE",
                    "lab_title": "LABORATORIO",
                    "hosp_title": "HOSPITAL CENTRAL",
                    "btn_heal": "CURAR",
                    "btn_buy": "COMPRAR",
                    "menu_play": "JUGAR",
                    "menu_settings": "AJUSTES",
                    "menu_exit": "SALIR"
                },
                "en": {
                    "btn_back": "BACK",
                    "btn_confirm": "CONFIRM",
                    "btn_cancel": "CANCEL",
                    "msg_insufficient_brawels": "Insufficient Brawels",
                    "msg_level_up": "LEVEL UP!",
                    "msg_xp_gained": "XP Gained",
                    "gym_title": "ELITE GYM",
                    "lab_title": "LABORATORY",
                    "hosp_title": "CENTRAL HOSPITAL",
                    "btn_heal": "HEAL",
                    "btn_buy": "BUY",
                    "menu_play": "PLAY",
                    "menu_settings": "SETTINGS",
                    "menu_exit": "EXIT"
                }
            }
        return cls._instance

    def get(self, key):
        return self.strings[self.lang].get(key, key)

    def set_language(self, lang):
        if lang in self.strings:
            self.lang = lang

lang = Localization()
