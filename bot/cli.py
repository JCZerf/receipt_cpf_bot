import argparse
import asyncio

from bot.browser.session import open_page
from bot.captcha.solver import auto_solver
from bot.core.logging_config import configure_logging
from bot.lookup.extract import extract_result
from bot.lookup.fetch import fetch_result_html
from bot.models import CpfQuery


async def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser(description="Query CPF registration status")
    parser.add_argument("cpf")
    parser.add_argument("birth_date", help="ddmmyyyy")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    query = CpfQuery(cpf=args.cpf, birth_date=args.birth_date)
    async with open_page(headless=args.headless) as page:
        html = await fetch_result_html(page, query, captcha_solver=auto_solver)
    result = extract_result(html)
    print(result.record if result.record else result.message)


if __name__ == "__main__":
    asyncio.run(main())
