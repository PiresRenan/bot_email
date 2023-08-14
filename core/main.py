from messenger import Email_getter


class Salesprogram:
    def __init__(self):
        pass

    def get_data(self):
        self.check_email()
        return "ta funfando"

    def check_email(self):
        teste = Email_getter()
        teste.email_catch()
