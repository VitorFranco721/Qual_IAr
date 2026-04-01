from datetime import datetime


class DataUtils:

    def convert_to_date(self, date_string: str) -> datetime.date:
        """
        Converte uma string de data no formato DD/MM/AAAA para um objeto datetime.date.

        :param date_string: String de data no formato 'DD/MM/AAAA'.
        :return: Objeto datetime.date.
        """
        try:
            return datetime.strptime(date_string, "%d/%m/%Y").date()
        except ValueError as e:
            raise ValueError(f"Erro ao converter data '{date_string}': {e}")

    def convert_to_datetime(self, datetime_string: str) -> datetime:
        """
        Converte uma string de data e hora no formato 'DD/MM/AAAA às HH:MM' para um objeto datetime.
        Ignora texto adicional após a hora.

        :param datetime_string: String de data e hora no formato 'DD/MM/AAAA às HH:MM - ...'.
        :return: Objeto datetime.
        """
        try:
            # Remove qualquer texto após o padrão 'HH:MM'
            cleaned_datetime = datetime_string.split(' às ')[0] + ' ' + datetime_string.split(' às ')[1].split(' -')[0]
            return datetime.strptime(cleaned_datetime, "%d/%m/%Y %H:%M")
        except ValueError as e:
            raise ValueError(f"Erro ao converter data e hora '{datetime_string}': {e}")