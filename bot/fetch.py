from typing import Awaitable, Callable

from patchright.async_api import Page

from bot.models import CpfQuery

QUERY_URL = (
    "https://servicos.receita.fazenda.gov.br/servicos/cpf/consultasituacao/ConsultaPublica.asp"
)

CaptchaSolver = Callable[[Page], Awaitable[None]]


async def manual_solver(page: Page) -> None:
    await page.wait_for_timeout(10_000)


async def fetch_result_html(
    page: Page, query: CpfQuery, captcha_solver: CaptchaSolver = manual_solver
) -> str:
    await page.goto(QUERY_URL)
    await page.fill("#txtCPF", query.cpf)
    await page.fill("#txtDataNascimento", query.birth_date)
    await captcha_solver(page)
    async with page.expect_navigation():
        await page.click("#id_submit")
    return await page.content()
