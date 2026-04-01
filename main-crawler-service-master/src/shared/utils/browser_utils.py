import logging
import os
import shutil
import time

from selenium import webdriver
from selenium.common import ElementClickInterceptedException, NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


class BrowserUtils:
    def __init__(self, driver=None):
        self.driver = driver

    def _resolve_firefox_binary(self, firefox_binary: str | None = None) -> str | None:
        """Resolve o caminho do executável do Firefox."""
        candidates = []

        if firefox_binary:
            candidates.append(firefox_binary)

        env_binary = os.getenv('FIREFOX_BINARY') or os.getenv('MOZ_FIREFOX_BINARY')
        if env_binary:
            candidates.append(env_binary)

        which_firefox = shutil.which('firefox')
        if which_firefox:
            candidates.append(which_firefox)

        if os.name == 'nt':
            windows_defaults = [
                os.path.join(os.getenv('PROGRAMFILES', ''), 'Mozilla Firefox', 'firefox.exe'),
                os.path.join(os.getenv('PROGRAMFILES(X86)', ''), 'Mozilla Firefox', 'firefox.exe'),
                os.path.join(os.getenv('LOCALAPPDATA', ''), 'Mozilla Firefox', 'firefox.exe'),
            ]
            candidates.extend(windows_defaults)

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate

        return None

    def _resolve_chrome_binary(self, chrome_binary: str | None = None) -> str | None:
        """Resolve o caminho do executável do Chrome/Chromium."""
        candidates = []

        if chrome_binary:
            candidates.append(chrome_binary)

        env_binary = os.getenv('CHROME_BINARY') or os.getenv('GOOGLE_CHROME_BIN')
        if env_binary:
            candidates.append(env_binary)

        which_candidates = [
            shutil.which('chrome'),
            shutil.which('google-chrome'),
            shutil.which('chromium'),
            shutil.which('chromium-browser'),
        ]
        candidates.extend([path for path in which_candidates if path])

        if os.name == 'nt':
            windows_defaults = [
                os.path.join(os.getenv('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
                os.path.join(os.getenv('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
                os.path.join(os.getenv('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            ]
            candidates.extend(windows_defaults)

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate

        return None

    def _open_firefox(self, browser_path, headless=False, firefox_binary=None):
        options = webdriver.FirefoxOptions()

        resolved_firefox_binary = self._resolve_firefox_binary(firefox_binary)
        if not resolved_firefox_binary:
            raise FileNotFoundError(
                "Firefox não encontrado. Instale o Mozilla Firefox ou defina FIREFOX_BINARY."
            )

        options.binary_location = resolved_firefox_binary

        if headless:
            options.add_argument('-headless')

        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.dir", browser_path)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        profile.set_preference("pdfjs.disabled", True)

        logging.info(
            f"Iniciando navegador Firefox com pasta de downloads em: {browser_path} "
            f"(binário: {resolved_firefox_binary})"
        )
        self.driver = webdriver.Firefox(options=options, firefox_profile=profile)

    def _open_chrome(self, browser_path, headless=False, chrome_binary=None):
        options = webdriver.ChromeOptions()

        resolved_chrome_binary = self._resolve_chrome_binary(chrome_binary)
        if resolved_chrome_binary:
            options.binary_location = resolved_chrome_binary

        if headless:
            options.add_argument('--headless=new')

        options.add_experimental_option('prefs', {
            'download.default_directory': os.path.abspath(browser_path),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'plugins.always_open_pdf_externally': True,
        })
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        logging.info(
            f"Iniciando navegador Chrome com pasta de downloads em: {browser_path}"
            + (f" (binário: {resolved_chrome_binary})" if resolved_chrome_binary else "")
        )
        self.driver = webdriver.Chrome(options=options)

    def open_browser(self, browser_path, headless=False, firefox_binary=None, browser='chrome', chrome_binary=None):
        """Inicia navegador (Chrome ou Firefox) configurado para download automático."""
        try:
            chosen_browser = (browser or 'chrome').lower()

            if chosen_browser == 'firefox':
                self._open_firefox(browser_path, headless=headless, firefox_binary=firefox_binary)
                return

            if chosen_browser == 'chrome':
                self._open_chrome(browser_path, headless=headless, chrome_binary=chrome_binary)
                return

            if chosen_browser == 'auto':
                try:
                    self._open_chrome(browser_path, headless=headless, chrome_binary=chrome_binary)
                except Exception:
                    self._open_firefox(browser_path, headless=headless, firefox_binary=firefox_binary)
                return

            raise ValueError("BROWSER inválido. Use: chrome, firefox ou auto")
        except Exception as e:
            logging.error(f"Erro ao abrir o navegador: {str(e)}")
            raise

    def close_browser(self):
        """Fecha todas as abas e o navegador."""
        try:
            if self.driver:
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
                logging.info("Navegador fechado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao tentar fechar o navegador: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

    def wait_for_page_load(self, timeout=20):
        """Aguarda até que todos os elementos sejam carregados na tela."""
        try:
            logging.info("Aguarda a tela carregar")
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            logging.info("Tela carregada com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao aguardar o carregamento da tela: {str(e)}")
            raise

    def open_page(self, url):
        """Navega para a URL especificada e aguarda o carregamento completo."""
        try:
            self.driver.get(url)
            logging.info(f"Abrindo a página: {url}")
            self.wait_for_page_load()
        except Exception as e:
            logging.error(f"Erro ao abrir a página {url}: {str(e)}")
            raise

    def click_button(self, by_type, identifier, timeout=10):
        """Clica em um botão especificado por seu tipo e identificador."""
        try:
            # Aguarda até que o botão seja clicável
            button = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by_type, identifier))
            )

            # Verifica se há obstruções antes de clicar
            try:
                button.click()
                logging.info(f"Botão {identifier} clicado com sucesso.")
            except ElementClickInterceptedException:
                # Scroll para o botão caso esteja obstruído
                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                self.driver.execute_script("arguments[0].click();", button)
                logging.info(f"Botão {identifier} clicado via JavaScript.")
        except Exception as e:
            logging.error(f"Erro ao clicar no botão {identifier}: {str(e)}")
            raise

    def fill_text_field(self, by, identifier, value):
        """
        Preenche um campo de texto localizado por um tipo de localizador.

        :param by: Tipo de localizador (por exemplo, By.ID, By.NAME, By.XPATH, etc.)
        :param identifier: Valor do localizador (por exemplo, "username", "email", "//input[@name='email']", etc.)
        :param value: Valor a ser preenchido no campo de texto
        """
        try:
            text_field = self.driver.find_element(by, identifier)
            text_field.clear()
            text_field.send_keys(value)
        except Exception as e:
            logging.error(f"Erro ao preencher o campo de texto com {by}='{identifier}': {e}")

    def select_dropdown_option(self, by, identifier, value):
        """
        Seleciona uma opção de um dropdown localizado por um tipo de localizador.

        :param by: Tipo de localizador (por exemplo, By.ID, By.NAME, By.XPATH, etc.)
        :param identifier: Valor do localizador (por exemplo, "companies", "//select[@name='companies']", etc.)
        :param value: Valor a ser selecionado no dropdown
        """
        try:
            dropdown_field = self.driver.find_element(by, identifier)
            select = Select(dropdown_field)
            select.select_by_value(value)
        except Exception as e:
            logging.warning(f"Erro ao selecionar a opção no dropdown com {by}='{identifier}': {e}")

    def check_text_in_html(self, text, timeout=60, interval=5):
        """
        Verifica se o texto desejado aparece no HTML da página dentro de um limite de tempo.

        :param text: Texto a ser procurado no HTML da página.
        :param timeout: Tempo limite (em segundos) para a busca antes de retornar um erro. Padrão: 60 segundos.
        :param interval: Intervalo (em segundos) entre as verificações. Padrão: 5 segundos.
        :return: Retorna True se o texto for encontrado; levanta uma exceção se o tempo expirar.
        """
        result = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Verifica o HTML da página
            if text in self.driver.page_source:
                result = True
                return True
            # Espera um intervalo antes de verificar novamente
            time.sleep(interval)

        # Se o tempo limite for atingido sem encontrar o texto, lança uma exceção
        logging.warning(f"O texto '{text}' não foi encontrado no HTML após {timeout} segundos.")
        return result

    def check_text_in_element(self, by, value, expected_text, timeout=60):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element((by, value), expected_text)
            )
            return True
        except TimeoutException:
            return False

    def switch_to_iframe_by_id(self, id):
        self.driver.switch_to.frame(id)

    def switch_to_default_content(self):
        self.driver.switch_to.default_content()

    def find_tables_by_headers(self, headers: list[str], timeout=10):
        """
        Busca todas as tabelas no DOM que possuem os cabeçalhos fornecidos.

        :param headers: Lista de cabeçalhos esperados (por exemplo, ['Data', 'Tipo']).
        :param timeout: Tempo máximo de espera para elementos serem encontrados.
        :return: Lista de tabelas contendo os dados.
        """
        found_tables = []

        # Encontra todas as tabelas na página
        tables = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'table'))
        )

        for table in tables:
            try:
                # Verifica se a tabela possui os cabeçalhos fornecidos
                thead = table.find_element(By.TAG_NAME, 'thead')
                columns = [th.text.strip() for th in thead.find_elements(By.TAG_NAME, 'th')]

                if all(header in columns for header in headers):
                    # Extrai os dados do <tbody>
                    tbody = table.find_element(By.TAG_NAME, 'tbody')
                    rows = []
                    for tr in tbody.find_elements(By.TAG_NAME, 'tr'):
                        # Extrai o texto das células
                        cells = [td.text.strip() for td in tr.find_elements(By.TAG_NAME, 'td')]
                        if len(cells) == len(headers):  # Garante que a linha tenha o número correto de colunas
                            rows.append(dict(zip(headers, cells)))
                    found_tables.append(rows)
            except Exception as e:
                # Ignora tabelas mal formatadas ou incompletas
                continue

        return found_tables

    def wait_for_elements_visible(self, by, value: str, timeout: int = 10):
        """
        Aguarda até que elementos estejam visíveis na página.
        :param by: Tipo de seletor (By.ID, By.CLASS_NAME, etc.)
        :param value: Valor do seletor
        :param timeout: Tempo máximo de espera
        :return: Lista de elementos encontrados ou uma lista vazia se nenhum elemento for encontrado
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_all_elements_located((by, value))
            )
        except Exception as e:
            logging.warning(f"Erro ao aguardar elementos visíveis ({by}, {value}): {str(e)}")
            return []

    def get_element_text_or_empty(self, by, element_id: str):
        try:
            return self.driver.find_element(by, element_id).text
        except NoSuchElementException:
            logging.warning(f"Não foi encontrado valor para ({by}, {element_id})")
            return ""

    def collect_field_text(self, by, identifier: str, timeout: int = 10, use_innertext: bool = True):
        """
        Coleta o texto de um campo identificado por classe, ID ou outro seletor.
        
        :param by: Tipo de localizador (By.CLASS_NAME, By.ID, By.CSS_SELECTOR, etc.)
        :param identifier: Valor do localizador (nome da classe, ID, seletor CSS, etc.)
        :param timeout: Tempo máximo de espera para o elemento aparecer (padrão: 10 segundos)
        :param use_innertext: Se True, usa innerText via JavaScript; se False, usa .text do Selenium
        :return: Texto coletado do elemento ou string vazia se não encontrado
        """
        try:
            # Aguardar elemento estar presente na página
            logging.info(f"Aguardando elemento ({by}, {identifier}) aparecer...")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, identifier))
            )
            
            # Coletar texto
            if use_innertext:
                # Usar innerText via JavaScript (mais confiável para elementos dinâmicos)
                text = self._collect_text_via_javascript(by, identifier)
                if not text:
                    # Fallback para .text do Selenium
                    text = element.text
            else:
                # Usar .text do Selenium diretamente
                text = element.text
            
            collected_text = text.strip() if text else ""
            logging.info(f"Texto coletado do campo ({by}, {identifier}): {collected_text[:100]}...")
            return collected_text
            
        except TimeoutException:
            logging.warning(f"Timeout: Elemento ({by}, {identifier}) não encontrado após {timeout} segundos")
            return ""
        except NoSuchElementException:
            logging.warning(f"Elemento ({by}, {identifier}) não encontrado")
            return ""
        except Exception as e:
            logging.error(f"Erro ao coletar texto do campo ({by}, {identifier}): {str(e)}")
            return ""

    def _collect_text_via_javascript(self, by, identifier: str) -> str:
        """
        Método auxiliar para coletar texto usando innerText via JavaScript.
        
        :param by: Tipo de localizador
        :param identifier: Valor do localizador
        :return: Texto coletado ou string vazia
        """
        try:
            # Construir seletor CSS baseado no tipo de By
            selector = self._build_css_selector(by, identifier)
            
            if selector:
                # Executar JavaScript para coletar innerText
                text = self.driver.execute_script(
                    f"return document.querySelector('{selector}')?.innerText || ''"
                )
                return text if text else ""
            else:
                # Se não conseguir construir seletor CSS, retorna vazio
                return ""
        except Exception as e:
            logging.warning(f"Erro ao coletar texto via JavaScript: {str(e)}")
            return ""

    def _build_css_selector(self, by, identifier: str) -> str:
        """
        Constrói um seletor CSS baseado no tipo de By fornecido.
        
        :param by: Tipo de localizador
        :param identifier: Valor do localizador
        :return: Seletor CSS ou string vazia se não suportado
        """
        if by == By.CLASS_NAME:
            return f".{identifier.replace(' ', '.')}"
        elif by == By.ID:
            return f"#{identifier}"
        elif by == By.CSS_SELECTOR:
            return identifier
        elif by == By.TAG_NAME:
            return identifier
        else:
            # Para outros tipos de By, retorna vazio (será usado fallback)
            logging.warning(f"Tipo de By não suportado para seletor CSS: {by}")
            return ""