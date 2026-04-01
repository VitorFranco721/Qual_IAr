import logging
import os
import re
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from src.infrastructure.config.config import config
from src.presentation.schemas.iqair.iqair_schema import IQAirDataSchema
from src.shared.utils.browser_utils import BrowserUtils
from src.persistence.repositories.iqair.iqair_repository import IQAirRepository
from src.business.mappers.iqair_mapper import iqair_schema_to_entity, iqair_entity_to_schema
from src.shared.constants.screen_elements.iqair_elements import IQAirElements
from selenium.webdriver.common.by import By


class IQAirController:
    NOT_FOUND_VALUE = "não encontrado"

    def __init__(self, iqair_repository: IQAirRepository):
        self.browser_utils = BrowserUtils()
        self.headless = config.HEADLESS
        self.browser = config.BROWSER
        self.firefox_binary = config.FIREFOX_BINARY
        self.chrome_binary = config.CHROME_BINARY
        self.iqair_repository = iqair_repository
        # Default IQAir URL (can be adjusted)
        self.default_url = "https://www.iqair.com/br/brazil/sao-paulo"

    def collect_aqi_data(self) -> IQAirDataSchema:
        """
        Coleta dados do campo .aqi-box-shadow-green do site IQAir
        
        Args:
            url: URL do site IQAir. Se não fornecida, usa a URL padrão.
            
        Returns:
            IQAirDataSchema com o texto coletado do campo AQI
        """
        target_url = IQAirElements.DEFAULT_TARGET_URL.value
        collection_unit = self._extract_collection_unit(target_url)
        browser_open = False

        try:
            logging.info(f"Iniciando coleta de dados do IQAir: {target_url}")

            # Criar diretório temporário para o navegador (se necessário)
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)

            # Abrir navegador
            self.browser_utils.open_browser(
                temp_dir,
                headless=self.headless,
                browser=self.browser,
                firefox_binary=self.firefox_binary,
                chrome_binary=self.chrome_binary,
            )
            browser_open = True
            logging.info("Navegador aberto com sucesso")

            # Abrir página
            self.browser_utils.open_page(target_url)
            logging.info(f"Página {target_url} carregada")

            # Wait for element to appear and collect text
            aqi_text = self._collect_aqi_text()
            wind_direction_dom, wind_direction_degree_dom = self._extract_wind_direction_from_dom()
            has_rain_dom, rain_chance_dom = self._extract_rain_data_from_dom()

            logging.debug(f"Dados coletados...")

            # Process and structure the data (returns even if empty)
            structured_data = self._process_aqi_data(
                aqi_text or "",
                wind_direction_override=wind_direction_dom,
                wind_direction_degree_override=wind_direction_degree_dom,
                has_rain_override=has_rain_dom,
                rain_chance_override=rain_chance_dom,
            )
            structured_data['sensor_location'] = collection_unit
            
            # Create schema from structured data
            schema = IQAirDataSchema(**structured_data)
            
            # Save to database
            try:
                entity = iqair_schema_to_entity(schema)
                setattr(entity, "collection_unit", collection_unit)
                saved_entity = self.iqair_repository.create(entity)
                logging.info(f"Dados IQAir salvos no banco de dados com ID: {saved_entity.id}")
                
                # Return updated schema
                return iqair_entity_to_schema(saved_entity)
            except Exception as e:
                logging.error(f"Erro ao salvar dados IQAir no banco de dados: {str(e)}")
                # Return schema even if save fails
                return schema

        except Exception as e:
            logging.error(f"Erro ao coletar dados do IQAir: {str(e)}")
            raise
        finally:
            # Fechar navegador
            if browser_open:
                try:
                    self.browser_utils.close_browser()
                    logging.info("Navegador fechado")
                except Exception as e:
                    logging.error(f"Erro ao fechar navegador: {str(e)}")

    def collect_aqi_data_for_session(self) -> list[IQAirDataSchema]:
        """
        Coleta dados de múltiplas unidades/sensores em uma única sessão de scraping.
        """
        browser_open = False
        collected_items: list[IQAirDataSchema] = []

        try:
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)

            self.browser_utils.open_browser(
                temp_dir,
                headless=self.headless,
                browser=self.browser,
                firefox_binary=self.firefox_binary,
                chrome_binary=self.chrome_binary,
            )
            browser_open = True
            logging.info("Navegador aberto com sucesso para coleta por sessão")

            targets = self._build_targets_for_session()
            logging.info(f"Iniciando coleta por sessão para {len(targets)} unidade(s)")

            for collection_unit, target_url in targets:
                try:
                    self.browser_utils.open_page(target_url)
                    aqi_text = self._collect_aqi_text()
                    wind_direction_dom, wind_direction_degree_dom = self._extract_wind_direction_from_dom()
                    has_rain_dom, rain_chance_dom = self._extract_rain_data_from_dom()
                    structured_data = self._process_aqi_data(
                        aqi_text or "",
                        wind_direction_override=wind_direction_dom,
                        wind_direction_degree_override=wind_direction_degree_dom,
                        has_rain_override=has_rain_dom,
                        rain_chance_override=rain_chance_dom,
                    )
                    structured_data['sensor_location'] = collection_unit
                    schema = IQAirDataSchema(**structured_data)

                    try:
                        entity = iqair_schema_to_entity(schema)
                        setattr(entity, "collection_unit", collection_unit)
                        self.iqair_repository.create(entity)
                    except Exception as save_error:
                        logging.error(
                            f"Erro ao salvar dados da unidade '{collection_unit}': {save_error}"
                        )

                    collected_items.append(schema)
                    logging.info(
                        f"Unidade '{collection_unit}' coletada com sucesso - AQI: {schema.aqi_score}"
                    )
                except Exception as collect_error:
                    logging.error(
                        f"Falha ao coletar unidade '{collection_unit}' ({target_url}): {collect_error}"
                    )

            return collected_items
        finally:
            if browser_open:
                try:
                    self.browser_utils.close_browser()
                    logging.info("Navegador fechado após coleta por sessão")
                except Exception as close_error:
                    logging.error(f"Erro ao fechar navegador após sessão: {close_error}")

    def _build_targets_for_session(self) -> list[tuple[str, str]]:
        default_url = IQAirElements.DEFAULT_TARGET_URL.value
        self.browser_utils.open_page(default_url)

        discovered_targets = self._discover_sensor_targets_from_page(default_url)
        if not discovered_targets:
            return [(self._extract_collection_unit(default_url), default_url)]

        return discovered_targets

    def _discover_sensor_targets_from_page(self, default_url: str) -> list[tuple[str, str]]:
        targets: list[tuple[str, str]] = []
        seen_urls: set[str] = set()

        def append_target(url: str, label: str):
            normalized_url = url.strip().rstrip('/')
            if not normalized_url or normalized_url in seen_urls:
                return
            seen_urls.add(normalized_url)
            targets.append((label, normalized_url))

        append_target(default_url, self._extract_collection_unit(default_url))

        if not self.browser_utils.driver:
            return targets

        try:
            city_path = urlparse(default_url).path.rstrip('/')
            hrefs = self.browser_utils.driver.execute_script("""
                return Array.from(document.querySelectorAll('a[href]'))
                    .map((anchor) => (anchor.getAttribute('href') || '').trim())
                    .filter((href) => href.length > 0);
            """) or []

            for href_raw in hrefs:
                href = str(href_raw or "").strip()
                if not href:
                    continue

                if href.startswith('/'):
                    base = IQAirElements.BASE_URL.value.rstrip('/')
                    href = f"{base}{href}"

                parsed_href = urlparse(href)
                href_path = parsed_href.path.rstrip('/')
                if not href_path.startswith(city_path + "/"):
                    continue

                if "/map" in href_path or "/news" in href_path or "/world-air-quality" in href_path:
                    continue

                collection_unit = self._extract_collection_unit(href)
                append_target(href, collection_unit)

        except Exception as discover_error:
            logging.warning(f"Não foi possível descobrir sensores automaticamente: {discover_error}")

        return targets

    def _extract_collection_unit(self, target_url: str) -> str:
        path = urlparse(target_url).path.strip("/")
        slug = path.split("/")[-1] if path else "sensor"
        normalized = slug.replace("-", " ").strip()
        return normalized.title() if normalized else "Sensor"

    def _collect_aqi_text(self, timeout: int = 30) -> str:
        """
        Collects text from element with class .aqi-box-shadow-green
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            Collected text from element
        """
        # Use the new collect_field_text method from BrowserUtils
        aqi_text = self.browser_utils.collect_field_text(
            by=By.CSS_SELECTOR,
            identifier=IQAirElements.AQI_BOX_SHADOW_GREEN.value,
            timeout=timeout,
            use_innertext=True
        )

        # If main selector fails, try alternatives
        if not aqi_text:
            return self._try_alternative_selectors()

        return aqi_text

    def _try_alternative_selectors(self) -> str:
        """
        Tries to collect data using alternative selectors if main one fails
        """
        alternative_selectors = [
            IQAirElements.AQI_BOX_SHADOW_GREEN.value,
            IQAirElements.AQI_BOX.value,
            IQAirElements.AQI_ELEMENT.value,
            IQAirElements.AQI_VALUE.value,
            IQAirElements.AQI_NUMBER.value
        ]

        for selector in alternative_selectors:
            text = self.browser_utils.collect_field_text(
                by=By.CSS_SELECTOR,
                identifier=selector,
                timeout=5,
                use_innertext=True
            )
            if text:
                logging.info(f"Texto coletado usando seletor alternativo '{selector}': {text}")
                return text

        return ""

    def _normalize_wind_direction(self, raw_direction: str) -> str:
        if not raw_direction:
            return ""

        normalized = raw_direction.upper().strip()
        replacements = {
            "NORTE": "N",
            "SUL": "S",
            "LESTE": "E",
            "L": "E",
            "OESTE": "W",
            "O": "W",
            "NORDESTE": "NE",
            "NOROESTE": "NW",
            "SUDESTE": "SE",
            "SUDOESTE": "SW",
            "NO": "NW",
            "SO": "SW",
        }
        normalized = replacements.get(normalized, normalized)

        if normalized.startswith("O") and normalized != "O":
            normalized = "W" + normalized[1:]
        elif normalized == "O":
            normalized = "W"

        multi_direction_match = re.search(
            r'\b(NNE|NNW|ENE|ESE|SSE|SSW|WNW|WSW|NE|NW|SE|SW)\b',
            normalized,
            re.IGNORECASE,
        )
        if multi_direction_match:
            return multi_direction_match.group(1).upper()

        single_direction = normalized.strip().upper()
        if single_direction in {"N", "S", "E", "W"}:
            return single_direction

        return ""

    def _explicit_not_found(self, value: str) -> str:
        normalized = str(value or "").strip()
        return normalized if normalized else self.NOT_FOUND_VALUE

    def _degrees_to_cardinal(self, degrees: float) -> str:
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round((degrees % 360) / 22.5) % 16
        return directions[index]

    def _normalize_wind_degree(self, raw_degree) -> str:
        if raw_degree is None:
            return ""

        if isinstance(raw_degree, (int, float)):
            numeric = float(raw_degree)
        else:
            degree_match = re.search(r'-?\d+(?:[\.,]\d+)?', str(raw_degree))
            if not degree_match:
                return ""
            numeric = float(degree_match.group(0).replace(',', '.'))

        normalized = numeric % 360
        if normalized.is_integer():
            return str(int(normalized))
        return f"{normalized:.1f}".rstrip('0').rstrip('.')

    def _extract_numeric_temperature(self, value: str) -> str:
        if not value:
            return ""
        match = re.search(r'-?\d+(?:[\.,]\d+)?', str(value))
        if not match:
            return ""
        numeric = float(match.group(0).replace(',', '.'))
        if numeric.is_integer():
            return str(int(numeric))
        return f"{numeric:.1f}".rstrip('0').rstrip('.')

    def _cardinal_to_degrees(self, cardinal: str) -> str:
        mapping = {
            "N": 0,
            "NNE": 22.5,
            "NE": 45,
            "ENE": 67.5,
            "E": 90,
            "ESE": 112.5,
            "SE": 135,
            "SSE": 157.5,
            "S": 180,
            "SSW": 202.5,
            "SW": 225,
            "WSW": 247.5,
            "W": 270,
            "WNW": 292.5,
            "NW": 315,
            "NNW": 337.5,
        }
        value = mapping.get((cardinal or "").upper().strip())
        return self._normalize_wind_degree(value) if value is not None else ""

    def _extract_wind_direction_from_dom(self) -> tuple[str, str]:
        if not self.browser_utils.driver:
            return "", ""

        try:
            state_result = self.browser_utils.driver.execute_script(r"""
                const directionRegex = /\b(N|S|E|W|NE|NW|SE|SW|NNE|NNW|ENE|ESE|SSE|SSW|WNW|WSW|NORTE|SUL|LESTE|OESTE|NORDESTE|NOROESTE|SUDESTE|SUDOESTE|NO|SO)\b/i;
                const numberRegex = /-?\d+(?:[\.,]\d+)?/;

                const isObject = (value) => value && typeof value === 'object' && !Array.isArray(value);

                const parseNumber = (value) => {
                    if (typeof value === 'number' && Number.isFinite(value)) return value;
                    if (typeof value === 'string') {
                        const match = value.match(numberRegex);
                        if (match) {
                            const parsed = Number(match[0].replace(',', '.'));
                            return Number.isFinite(parsed) ? parsed : null;
                        }
                    }
                    return null;
                };

                const collectFromObject = (obj) => {
                    let direction = '';
                    let degrees = null;
                    let score = 0;

                    for (const [rawKey, rawValue] of Object.entries(obj || {})) {
                        const key = String(rawKey || '').toLowerCase();
                        const value = rawValue;

                        const isWindKey = /wind|vento/.test(key);
                        const isDirectionKey = /direction|direc|bearing|cardinal/.test(key);
                        const isDegreeKey = /deg|degree|grau|angle|angulo|bearing/.test(key);
                        const isSpeedKey = /speed|velocity|velocidade/.test(key) && isWindKey;

                        if ((isDirectionKey || (isWindKey && typeof value === 'string')) && typeof value === 'string') {
                            const directionMatch = value.match(directionRegex);
                            if (directionMatch) {
                                direction = directionMatch[1];
                                score += 5;
                            }
                        }

                        if (isDegreeKey || (isWindKey && (typeof value === 'number' || typeof value === 'string'))) {
                            const numeric = parseNumber(value);
                            if (numeric !== null && Math.abs(numeric) <= 720) {
                                degrees = numeric;
                                score += isWindKey ? 6 : 3;
                            }
                        }

                        if (isSpeedKey && parseNumber(value) !== null) {
                            score += 2;
                        }
                    }

                    if (direction || degrees !== null) {
                        return { direction, degrees, score };
                    }

                    return null;
                };

                const seen = new Set();
                const queue = [];
                const push = (value) => {
                    if (!isObject(value) && !Array.isArray(value)) return;
                    if (seen.has(value)) return;
                    seen.add(value);
                    queue.push(value);
                };

                const nextDataNode = document.querySelector('#__NEXT_DATA__');
                if (nextDataNode && nextDataNode.textContent) {
                    try {
                        const parsed = JSON.parse(nextDataNode.textContent);
                        push(parsed);
                    } catch {}
                }

                const weatherCandidates = Array.from(document.querySelectorAll('script[type="application/json"], script[type="application/ld+json"]'));
                for (const scriptNode of weatherCandidates) {
                    const payload = (scriptNode.textContent || '').trim();
                    if (!payload) continue;
                    try {
                        const parsed = JSON.parse(payload);
                        push(parsed);
                    } catch {}
                }

                const results = [];
                while (queue.length) {
                    const current = queue.shift();
                    if (Array.isArray(current)) {
                        for (const item of current) push(item);
                        continue;
                    }

                    const extracted = collectFromObject(current);
                    if (extracted) results.push(extracted);

                    for (const value of Object.values(current)) {
                        if (isObject(value) || Array.isArray(value)) push(value);
                    }
                }

                if (!results.length) return null;

                results.sort((a, b) => b.score - a.score);
                return { ...results[0], source: '__NEXT_DATA__' };
            """)

            if isinstance(state_result, dict):
                direction_raw = state_result.get("direction")
                degree_raw = state_result.get("degrees")

                direction = self._normalize_wind_direction(str(direction_raw)) if direction_raw else ""
                degree = self._normalize_wind_degree(degree_raw)

                if degree and not direction:
                    try:
                        direction = self._degrees_to_cardinal(float(degree))
                    except ValueError:
                        direction = ""

                if direction and degree:
                    return direction, degree

            compass_result = self.browser_utils.driver.execute_script(r"""
                const xpath = '//*[@id="main-content"]/div[3]/div[2]/div[1]/div[2]/div[2]/div/div[2]/div[2]/img';

                const evaluateXPath = (expression) => {
                    try {
                        return document.evaluate(
                            expression,
                            document,
                            null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE,
                            null
                        ).singleNodeValue;
                    } catch {
                        return null;
                    }
                };

                const extractDegreeFromText = (value) => {
                    const text = String(value || '').trim();
                    if (!text) return null;

                    const rotatePropertyMatch = text.match(/rotate\s*:\s*(-?\d+(?:[\.,]\d+)?)deg/i);
                    if (rotatePropertyMatch) return Number(rotatePropertyMatch[1].replace(',', '.'));

                    const rotateMatch = text.match(/rotate\(\s*(-?\d+(?:[\.,]\d+)?)deg\s*\)/i);
                    if (rotateMatch) return Number(rotateMatch[1].replace(',', '.'));

                    const degreeMatch = text.match(/(-?\d+(?:[\.,]\d+)?)\s*°/);
                    if (degreeMatch) return Number(degreeMatch[1].replace(',', '.'));

                    const plainNumeric = text.match(/^\s*-?\d+(?:[\.,]\d+)?\s*$/);
                    if (plainNumeric) return Number(text.replace(',', '.'));

                    return null;
                };

                const normalize = (deg) => {
                    if (typeof deg !== 'number' || Number.isNaN(deg)) return null;
                    let value = deg % 360;
                    if (value < 0) value += 360;
                    return value;
                };

                const extractFromNode = (node) => {
                    if (!node) return null;

                    const style = window.getComputedStyle(node);
                    const candidates = [
                        node.getAttribute('style') || '',
                        node.style?.rotate || '',
                        node.getAttribute('transform') || '',
                        style?.rotate || '',
                        style?.transform || '',
                        node.getAttribute('aria-label') || '',
                        node.getAttribute('title') || '',
                        node.getAttribute('alt') || '',
                        node.getAttribute('data-degree') || '',
                        node.getAttribute('data-degrees') || '',
                        node.getAttribute('data-angle') || '',
                        node.getAttribute('aria-valuenow') || ''
                    ];

                    for (const candidate of candidates) {
                        const degree = extractDegreeFromText(candidate);
                        if (degree !== null) {
                            const normalized = normalize(degree);
                            if (normalized !== null) return { degrees: normalized, source: 'compass-xpath' };
                        }
                    }

                    return null;
                };

                const node = evaluateXPath(xpath);
                const byAlt = document.querySelector('img[alt="wind direction icon"]');
                const target = node || byAlt;
                if (!target) return null;

                const direct = extractFromNode(target);
                if (direct) return direct;

                const descendants = target.querySelectorAll ? target.querySelectorAll('*') : [];
                for (const child of descendants) {
                    const parsed = extractFromNode(child);
                    if (parsed) return parsed;
                }

                return null;
            """)

            if isinstance(compass_result, dict):
                compass_degree = self._normalize_wind_degree(compass_result.get("degrees"))
                if compass_degree:
                    try:
                        compass_direction = self._degrees_to_cardinal(float(compass_degree))
                    except ValueError:
                        compass_direction = ""
                    if compass_direction:
                        return compass_direction, compass_degree
                    return "", compass_degree

            dom_result = self.browser_utils.driver.execute_script(r"""
                const directionRegex = /\b(N|S|E|W|NE|NW|SE|SW|NNE|NNW|ENE|ESE|SSE|SSW|WNW|WSW|NORTE|SUL|LESTE|OESTE|NORDESTE|NOROESTE|SUDESTE|SUDOESTE|NO|SO)\b/i;
                const degreeRegex = /(-?\d+(?:[\.,]\d+)?)\s?°/i;
                const speedRegex = /\d+(?:[\.,]\d+)?\s?(km\/h|m\/s|mph)/i;
                const windHintRegex = /(wind|vento|dire[cç][aã]o|direction|compass|b[uú]ssola|bearing|arrow|seta|ponteiro|needle)/i;
                const nonWindDegreeRegex = /(temp|temperatura|feels\s*like|sensa[cç][aã]o\s*t[ée]rmica|dew\s*point|ponto\s*de\s*orvalho|umidade|humidity)/i;

                const normalizeAngle = (deg) => {
                    const value = Number(deg);
                    if (Number.isNaN(value)) return null;
                    let normalized = value % 360;
                    if (normalized < 0) normalized += 360;
                    return normalized;
                };

                const extractFromElement = (el) => {
                    if (!el) return null;

                    const contextText = [
                        el.getAttribute?.('aria-label') || '',
                        el.getAttribute?.('title') || '',
                        el.getAttribute?.('class') || '',
                        el.getAttribute?.('data-testid') || '',
                        el.parentElement?.textContent || '',
                        el.textContent || ''
                    ].join(' ');

                    const hasWindHint = windHintRegex.test(contextText);
                    const hasNonWindHint = nonWindDegreeRegex.test(contextText);

                    const texts = [
                        el.getAttribute?.('aria-label') || '',
                        el.getAttribute?.('title') || '',
                        el.getAttribute?.('data-testid') || '',
                        el.getAttribute?.('data-degree') || '',
                        el.getAttribute?.('data-degrees') || '',
                        el.getAttribute?.('data-angle') || '',
                        el.getAttribute?.('aria-valuenow') || '',
                        el.getAttribute?.('value') || '',
                        el.textContent || ''
                    ];

                    for (const txt of texts) {
                        const value = String(txt);

                        const degreeMatch = value.match(degreeRegex);
                        if (degreeMatch && hasWindHint && !hasNonWindHint) {
                            return { degrees: parseFloat(degreeMatch[1].replace(',', '.')), source: 'text/attr' };
                        }

                        const dirMatch = value.match(directionRegex);
                        if (dirMatch && hasWindHint) {
                            return { direction: dirMatch[1], source: 'text-direction' };
                        }
                    }

                    return null;
                };

                const candidates = Array.from(document.querySelectorAll('*'));
                const scored = [];

                for (const el of candidates) {
                    const text = [
                        el.getAttribute?.('aria-label') || '',
                        el.getAttribute?.('title') || '',
                        el.getAttribute?.('class') || '',
                        el.getAttribute?.('data-testid') || '',
                        el.textContent || ''
                    ].join(' ').toLowerCase();

                    const hasWindContext = /wind|vento|dire[cç][aã]o|direction|compass|bearing|arrow|seta|ponteiro|needle/.test(text);
                    const hasSpeedContext = speedRegex.test(text) || speedRegex.test(el.parentElement?.textContent || '');
                    if (!hasWindContext && !hasSpeedContext) {
                        continue;
                    }

                    const result = extractFromElement(el);
                    if (!result) continue;

                    let score = 0;
                    if (/wind|vento|dire[cç][aã]o|direction|compass|b[uú]ssola|bearing|arrow|seta|ponteiro|needle/.test(text)) score += 5;
                    if (/°/.test(text)) score += 3;
                    if ((el.tagName || '').toLowerCase() === 'svg') score += 2;
                    if (String(el.className || '').toLowerCase().includes('wind')) score += 4;

                    const nearbyText = (el.parentElement?.textContent || '') + ' ' + (el.textContent || '');
                    if (speedRegex.test(nearbyText)) score += 3;
                    if (/temp|temperatura|humidity|umidade|dew point|orvalho/.test(text)) score -= 5;

                    scored.push({
                        score,
                        tag: el.tagName,
                        className: String(el.className || ''),
                        result,
                    });
                }

                scored.sort((a, b) => b.score - a.score);
                return scored.slice(0, 15);
            """)

            if not dom_result:
                return "", ""

            if isinstance(dom_result, list):
                preview = dom_result[:3]
                logging.debug(f"Top candidatos de direção do vento: {preview}")

                for candidate in dom_result:
                    if not isinstance(candidate, dict):
                        continue
                    result = candidate.get("result")
                    if not isinstance(result, dict):
                        continue

                    if result.get("degrees") is not None:
                        degree = self._normalize_wind_degree(result.get("degrees"))
                        if not degree:
                            continue
                        direction_raw = result.get("direction")
                        direction = self._normalize_wind_direction(str(direction_raw)) if direction_raw else ""
                        return direction, degree

                    if result.get("direction"):
                        direction = self._normalize_wind_direction(str(result.get("direction")))
                        if direction:
                            return direction, self._cardinal_to_degrees(direction)

                return "", ""

            if isinstance(dom_result, dict):
                if dom_result.get("direction"):
                    direction = self._normalize_wind_direction(str(dom_result.get("direction")))
                    degree = self._normalize_wind_degree(dom_result.get("degrees"))
                    return direction, degree
                if dom_result.get("degrees") is not None:
                    degree = self._normalize_wind_degree(dom_result.get("degrees"))
                    if degree:
                        return "", degree

            if isinstance(dom_result, str):
                direction = self._normalize_wind_direction(dom_result)
                return direction, ""

            return "", ""
        except Exception as error:
            logging.warning(f"Falha ao extrair direção do vento do DOM: {error}")
            return "", ""

    def _normalize_has_rain(self, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized in {"sim", "yes", "true", "1", "rain", "chuva", "rainy", "showers", "drizzle", "thunderstorm"}:
            return "sim"
        if normalized in {"não", "nao", "no", "false", "0", "sem chuva", "clear", "sunny", "cloudy", "partly cloudy"}:
            return "não"
        return ""

    def _normalize_rain_chance(self, value: str) -> str:
        if not value:
            return ""
        match = re.search(r"\d+(?:[\.,]\d+)?", str(value))
        if not match:
            return ""
        numeric = match.group(0).replace(',', '.')
        return f"{numeric}%"

    def _extract_rain_data_from_dom(self) -> tuple[str, str]:
        if not self.browser_utils.driver:
            return "", ""

        try:
            dom_result = self.browser_utils.driver.execute_script(r"""
                const chanceRegex = /(\d+(?:[\.,]\d+)?)\s?%/;
                const rainyKeywords = /(rain|rainy|showers|drizzle|precip|storm|chuva|chuvoso|garoa|tempestade)/i;

                const selectors = [
                    '[class*="weather"]',
                    '[class*="forecast"]',
                    '[class*="condition"]',
                    '[class*="rain"]',
                    '[class*="precip"]',
                    '[class*="icon"]',
                    '[aria-label]'
                ];

                let hasRain = '';
                let rainChance = '';

                const collectFromElement = (element) => {
                    if (!element) return;

                    const safeText = (value) => {
                        if (value === null || value === undefined) return '';
                        if (typeof value === 'string') return value;
                        if (typeof value === 'number' || typeof value === 'boolean') return String(value);
                        if (typeof value === 'object') {
                            if (typeof value.baseVal === 'string') return value.baseVal;
                            if (typeof value.value === 'string') return value.value;
                            try { return String(value); } catch { return ''; }
                        }
                        return '';
                    };

                    const chunks = [
                        safeText(element.getAttribute('aria-label')),
                        safeText(element.getAttribute('title')),
                        safeText(element.getAttribute('alt')),
                        safeText(element.className),
                        safeText(element.textContent)
                    ];

                    for (const chunk of chunks) {
                        if (!chunk) continue;
                        if (!rainChance) {
                            const chanceMatch = chunk.match(chanceRegex);
                            if (chanceMatch) rainChance = `${chanceMatch[1].replace(',', '.')}%`;
                        }
                        if (!hasRain && rainyKeywords.test(chunk)) {
                            hasRain = 'sim';
                        }
                    }
                };

                for (const selector of selectors) {
                    const nodes = document.querySelectorAll(selector);
                    for (const node of nodes) {
                        collectFromElement(node);
                        if (!rainChance) {
                            const nested = node.querySelectorAll('*');
                            for (const child of nested) collectFromElement(child);
                        }
                    }
                }

                if (rainChance && !hasRain) {
                    hasRain = parseFloat(rainChance) > 0 ? 'sim' : 'não';
                }

                return { hasRain, rainChance };
            """)

            if not isinstance(dom_result, dict):
                return "", ""

            has_rain = self._normalize_has_rain(str(dom_result.get("hasRain", "")))
            rain_chance = self._normalize_rain_chance(str(dom_result.get("rainChance", "")))

            if rain_chance and not has_rain:
                has_rain = "sim" if float(rain_chance.replace('%', '')) > 0 else "não"

            return has_rain, rain_chance
        except Exception as error:
            logging.warning(f"Falha ao extrair dados de chuva do DOM: {error}")
            return "", ""

    def _process_aqi_data(
        self,
        text: str,
        wind_direction_override: str = "",
        wind_direction_degree_override: str = "",
        has_rain_override: str = "",
        rain_chance_override: str = "",
    ) -> dict:
        """
        Processa o texto coletado do IQAir, separando por \\n\\n e extraindo os campos.
        Retorna apenas o que conseguiu capturar, sem validações.
        
        Args:
            text: Texto bruto coletado do elemento
            
        Returns:
            Dicionário com os dados estruturados (pode conter campos vazios)
        """
        if not text or not text.strip():
            # Se texto vazio, retorna todos os campos vazios
            return {
                'aqi_score': 0,
                'aqi_category': self.NOT_FOUND_VALUE,
                'local_time': datetime.now().strftime('%H:%M:%S'),
                'main_pollutant': self.NOT_FOUND_VALUE,
                'pollutant_concentration': self.NOT_FOUND_VALUE,
                'temperature': self.NOT_FOUND_VALUE,
                'wind_speed': self.NOT_FOUND_VALUE,
                'wind_direction': self.NOT_FOUND_VALUE,
                'wind_direction_degree': self.NOT_FOUND_VALUE,
                'humidity': self.NOT_FOUND_VALUE,
                'has_rain': self.NOT_FOUND_VALUE,
                'rain_chance': self.NOT_FOUND_VALUE,
                'pressure': self.NOT_FOUND_VALUE,
                'feels_like': self.NOT_FOUND_VALUE,
                'visibility': self.NOT_FOUND_VALUE,
                'dew_point': self.NOT_FOUND_VALUE
            }

        # Separar por \n\n
        parts = [p.strip() for p in text.split('\n\n') if p.strip()]

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        def extract_by_labels(labels: list[str]) -> str:
            labels_lower = [label.lower() for label in labels]

            for index, line in enumerate(lines):
                normalized_line = line.lower().replace('：', ':')

                for label in labels_lower:
                    if normalized_line.startswith(f"{label}:"):
                        return line.split(':', 1)[1].strip()

                    if normalized_line == label and index + 1 < len(lines):
                        return lines[index + 1].strip()

                    if normalized_line.startswith(f"{label} "):
                        return line[len(label):].strip()

            return ""

        # Extrair aqi_score (primeiro item, tenta extrair número)
        aqi_score = 0
        if len(parts) > 0:
            aqi_score_string = parts[0].strip()
            match = re.search(r'\d+', aqi_score_string)
            if match:
                try:
                    aqi_score = int(match.group())
                except ValueError:
                    aqi_score = 0

        # Extrair aqi_category (terceiro item, após "US AQI⁺")
        aqi_category = parts[2].strip().lower() if len(parts) > 2 else ""
        aqi_category = extract_by_labels(["aqi category", "category", "categoria"]) or aqi_category

        # Extrair main_pollutant (quinto item, após "Main pollutant:")
        main_pollutant = parts[4].strip() if len(parts) > 4 else ""
        main_pollutant = extract_by_labels(["main pollutant", "poluente principal"]) or main_pollutant

        # Extrair pollutant_concentration (sexto item)
        pollutant_concentration = parts[5].strip() if len(parts) > 5 else ""
        pollutant_concentration = extract_by_labels(["pollutant concentration", "concentração do poluente", "concentracao do poluente"]) or pollutant_concentration

        if not pollutant_concentration and main_pollutant:
            for line in lines:
                if main_pollutant.lower() in line.lower() and re.search(r'\d', line):
                    pollutant_concentration = line.strip()
                    break

        # Extrair temperature (sétimo item)
        temperature_raw = parts[6].strip() if len(parts) > 6 else ""
        # Garantir que tenha °C
        if temperature_raw:
            if '°C' in temperature_raw:
                temperature = temperature_raw
            elif '°' in temperature_raw:
                temperature = temperature_raw.replace('°', '°C')
            else:
                temperature = f"{temperature_raw} °C"
        else:
            temperature = ""

        # Extrair wind_speed (oitavo item)
        wind_speed = parts[7].strip() if len(parts) > 7 else ""

        # Extrair humidity (último item ou nono)
        humidity = parts[8].strip() if len(parts) > 8 else (parts[-1].strip() if parts else "")
        # Garantir que tenha %
        if humidity and not humidity.endswith('%'):
            humidity = f"{humidity} %"

        # Complementar/ajustar com extração por rótulos, quando disponível
        temperature = extract_by_labels(["temperature", "temperatura"]) or temperature
        wind_speed = extract_by_labels(["wind", "wind speed", "velocidade do vento"]) or wind_speed
        humidity = extract_by_labels(["humidity", "umidade"]) or humidity

        wind_direction = wind_direction_override
        wind_direction_degree = wind_direction_degree_override
        pressure = extract_by_labels(["pressure", "pressão", "pressao", "atmospheric pressure", "barometric pressure"])
        feels_like = extract_by_labels(["feels like", "sensação térmica", "sensacao termica"])
        visibility = extract_by_labels(["visibility", "visibilidade"])
        dew_point = extract_by_labels(["dew point", "ponto de orvalho"])
        has_rain = has_rain_override
        rain_chance = rain_chance_override

        wind_direction = self._normalize_wind_direction(wind_direction)
        wind_direction_degree = self._normalize_wind_degree(wind_direction_degree)

        temperature_numeric = self._extract_numeric_temperature(temperature)
        if wind_direction_degree and not wind_direction and temperature_numeric:
            try:
                degree_value = float(wind_direction_degree)
                temperature_value = float(temperature_numeric)
                if abs(degree_value - temperature_value) < 0.01:
                    logging.warning(
                        "Grau de vento descartado por possível confusão com temperatura: "
                        f"grau='{wind_direction_degree}', temperatura='{temperature}'"
                    )
                    wind_direction_degree = ""
            except ValueError:
                pass

        rain_chance = self._normalize_rain_chance(rain_chance)
        has_rain = self._normalize_has_rain(has_rain)
        if rain_chance and not has_rain:
            has_rain = "sim" if float(rain_chance.replace('%', '')) > 0 else "não"

        if wind_speed and not wind_direction_degree:
            logging.warning(
                f"Direção do vento em graus não identificada para wind_speed='{wind_speed}'"
            )
        elif wind_direction and wind_direction_degree:
            logging.info(
                f"Direção do vento identificada: {wind_direction} ({wind_direction_degree}°)"
            )

        logging.info(f"Dados processados: AQI={aqi_score}, Category={aqi_category}")

        return {
            'aqi_score': aqi_score,
            'aqi_category': self._explicit_not_found(aqi_category),
            'local_time': datetime.now().strftime('%H:%M:%S'),
            'main_pollutant': self._explicit_not_found(main_pollutant),
            'pollutant_concentration': self._explicit_not_found(pollutant_concentration),
            'temperature': self._explicit_not_found(temperature),
            'wind_speed': self._explicit_not_found(wind_speed),
            'wind_direction': self._explicit_not_found(wind_direction),
            'wind_direction_degree': self._explicit_not_found(wind_direction_degree),
            'humidity': self._explicit_not_found(humidity),
            'has_rain': self._explicit_not_found(has_rain),
            'rain_chance': self._explicit_not_found(rain_chance),
            'pressure': self._explicit_not_found(pressure),
            'feels_like': self._explicit_not_found(feels_like),
            'visibility': self._explicit_not_found(visibility),
            'dew_point': self._explicit_not_found(dew_point)
        }
