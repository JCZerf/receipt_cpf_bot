from bot.browser.session import open_page
from bot.captcha.solver import auto_solver
from bot.core.config import settings
from bot.lookup.extract import extract_result
from bot.lookup.fetch import fetch_result_html
from bot.models import CpfQuery, CpfQueryResult


async def lookup_cpf(cpf: str, birth_date: str) -> CpfQueryResult:
    query = CpfQuery(cpf=cpf, birth_date=birth_date)
    async with open_page(headless=settings.HEADLESS) as page:
        html = await fetch_result_html(page, query, captcha_solver=auto_solver)
    return extract_result(html)
